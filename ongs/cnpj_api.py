
import logging
import math
import secrets
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests

from django.core import signing
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import Instituicao
from .validators import cnpj_valido, normalizar_cnpj

logger = logging.getLogger(__name__)

_TOKEN_CNPJ_SALT = 'ongs.validacao-cnpj'
_TOKEN_CNPJ_MAX_AGE = 120


def retry_after_segundos(erro):
    resposta = getattr(erro, 'response', None)
    retry_after = getattr(resposta, 'headers', {}).get('Retry-After')
    if not retry_after:
        return None

    try:
        return max(0, int(retry_after))
    except (TypeError, ValueError):
        try:
            data_limite = parsedate_to_datetime(retry_after)
            if data_limite.tzinfo is None:
                data_limite = data_limite.replace(tzinfo=timezone.utc)
            return max(
                0,
                math.ceil(
                    (data_limite - datetime.now(timezone.utc)).total_seconds()
                ),
            )
        except (TypeError, ValueError, OverflowError):
            return None


def diagnosticar_falha_consulta_cnpj(erro):
    retry_after = None
    if isinstance(erro, requests.Timeout):
        codigo, status = 'timeout', 504
    elif isinstance(erro, requests.ConnectionError):
        codigo, status = 'conexao', 503
    elif isinstance(erro, requests.HTTPError):
        status_api = erro.response.status_code if erro.response is not None else None
        if status_api == 404:
            codigo, status = 'nao_encontrado', 404
        elif status_api == 429:
            codigo, status = 'limite_requisicoes', 429
            retry_after = retry_after_segundos(erro)
        elif status_api is not None and 500 <= status_api <= 599:
            codigo, status = 'indisponivel', 502
        else:
            codigo, status = 'erro_http', 502
    elif isinstance(erro, (ValueError, TypeError)):
        codigo, status = 'resposta_invalida', 502
    else:
        codigo, status = 'falha_consulta', 503

    logger.exception(
        'Falha na consulta de CNPJ à BrasilAPI (categoria=%s).',
        codigo,
    )
    if codigo == 'nao_encontrado':
        mensagem = 'CNPJ não encontrado na base consultada.'
    elif codigo == 'limite_requisicoes':
        mensagem = 'A consulta do CNPJ atingiu o limite de requisições.'
        if retry_after is not None:
            mensagem += f' Tente novamente em {retry_after} segundos.'
        else:
            mensagem += ' Tente novamente mais tarde.'
    else:
        mensagem = (
            'Não foi possível consultar o CNPJ no momento. '
            'Tente novamente mais tarde.'
        )
    return codigo, status, mensagem, retry_after


def criar_token_validacao_cnpj(request, cnpj, dados):
    nonce = request.session.get('cnpj_validacao_nonce')
    if nonce is None:
        nonce = secrets.token_urlsafe(32)
        request.session['cnpj_validacao_nonce'] = nonce
    return signing.dumps(
        {
            'cnpj': normalizar_cnpj(cnpj),
            'dados': dados,
            'nonce': nonce,
        },
        salt=_TOKEN_CNPJ_SALT,
        compress=True,
    )


def validar_token_cnpj(request, token, cnpj):
    if not token:
        return None

    try:
        payload = signing.loads(
            token,
            salt=_TOKEN_CNPJ_SALT,
            max_age=_TOKEN_CNPJ_MAX_AGE,
        )
    except signing.BadSignature:
        return None

    if (
        not isinstance(payload, dict)
        or payload.get('cnpj') != normalizar_cnpj(cnpj)
        or payload.get('nonce') != request.session.get('cnpj_validacao_nonce')
    ):
        return None

    dados = payload.get('dados')
    if (
        not isinstance(dados, dict)
        or not isinstance(dados.get('descricao_situacao_cadastral'), str)
        or dados['descricao_situacao_cadastral'].strip().upper() != 'ATIVA'
    ):
        return None
    return dados


def consultar_dados_cnpj(cnpj):
    resposta = requests.get(
        f'https://brasilapi.com.br/api/cnpj/v1/{cnpj}',
        timeout=10,
    )
    resposta.raise_for_status()
    dados = resposta.json()
    if (
        not isinstance(dados, dict)
        or not isinstance(dados.get('descricao_situacao_cadastral'), str)
        or not dados['descricao_situacao_cadastral'].strip()
    ):
        raise ValueError('Resposta cadastral inválida.')
    return dados


@require_GET
def consultar_cnpj(request, cnpj):
    cnpj = normalizar_cnpj(cnpj)

    if not cnpj_valido(cnpj):
        return JsonResponse({
            "valido": False,
            "mensagem": "CNPJ inválido. Verifique os números informados."
        }, status=400)

    if Instituicao.cnpj_ja_cadastrado(cnpj):
        return JsonResponse({
            "valido": False,
            "mensagem": "Este CNPJ já está cadastrado na plataforma."
        }, status=409)

    try:
        dados = consultar_dados_cnpj(cnpj)
    except (requests.RequestException, ValueError, TypeError) as erro:
        codigo, status, mensagem, retry_after = diagnosticar_falha_consulta_cnpj(
            erro,
        )
        valido = False if codigo == 'nao_encontrado' else None
        resposta = JsonResponse({
            "valido": valido,
            "codigo_erro": codigo,
            "mensagem": mensagem,
        }, status=status)
        if retry_after is not None:
            resposta['Retry-After'] = str(retry_after)
        return resposta

    situacao = dados.get("descricao_situacao_cadastral", "")
    ativo = situacao.upper() == "ATIVA"

    resposta_data = {
        "valido": True,
        "ativo": ativo,
        "cnpj": dados.get("cnpj"),
        "razao_social": dados.get("razao_social"),
        "nome_fantasia": dados.get("nome_fantasia"),
        "situacao_cadastral": situacao,
        "municipio": dados.get("municipio"),
        "uf": dados.get("uf"),
        "cep": dados.get("cep"),
        "logradouro": dados.get("logradouro"),
        "bairro": dados.get("bairro"),
        "telefone": dados.get("ddd_telefone_1"),
        "email": dados.get("email"),
        "mensagem": (
            "CNPJ ativo."
            if ativo else
            "Este CNPJ não possui situação cadastral ativa."
        )
    }
    if ativo:
        resposta_data['token_validacao'] = criar_token_validacao_cnpj(
            request,
            cnpj,
            dados,
        )
    return JsonResponse(resposta_data)
