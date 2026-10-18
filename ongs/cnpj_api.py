
import requests

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .validators import cnpj_valido, normalizar_cnpj


def consultar_dados_cnpj(cnpj):
    resposta = requests.get(
        f'https://brasilapi.com.br/api/cnpj/v1/{cnpj}',
        timeout=10,
    )
    resposta.raise_for_status()
    dados = resposta.json()
    if not isinstance(dados, dict):
        raise ValueError('Resposta cadastral inválida.')
    return dados

@require_GET
def consultar_cnpj(request, cnpj):
    cnpj = normalizar_cnpj(cnpj)

    if not cnpj_valido(cnpj):
        return JsonResponse({
            "valido": False,
            "mensagem": "CNPJ inválido."
        }, status=400)

    try:
        dados = consultar_dados_cnpj(cnpj)
    except requests.HTTPError as erro:
        status = erro.response.status_code if erro.response is not None else 503
        if status == 404:
            return JsonResponse({
                "valido": False,
                "mensagem": "CNPJ não encontrado na base consultada."
            }, status=404)
        if status == 400:
            return JsonResponse({
                "valido": False,
                "mensagem": "CNPJ rejeitado pela consulta."
            }, status=400)
        return JsonResponse({
            "valido": None,
            "mensagem": "Não foi possível consultar o CNPJ agora."
        }, status=503)
    except (requests.RequestException, ValueError):
        return JsonResponse({
            "valido": None,
            "mensagem": "Não foi possível consultar o CNPJ agora."
        }, status=503)

    situacao = dados.get("descricao_situacao_cadastral", "")
    ativo = situacao.upper() == "ATIVA"

    return JsonResponse({
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
            "CNPJ encontrado, mas não está ativo."
        )
    })
