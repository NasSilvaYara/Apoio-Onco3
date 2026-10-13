
import re
import requests

from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def consultar_cnpj(request, cnpj):
    # Remove a pontuação, mantendo letras e números.
    cnpj = re.sub(r"[^0-9A-Za-z]", "", cnpj).upper()

    if not re.fullmatch(r"[0-9A-Z]{12}[0-9]{2}", cnpj):
        return JsonResponse({
            "valido": False,
            "mensagem": "Formato de CNPJ inválido."
        }, status=400)

    try:
        resposta = requests.get(
            f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}",
            timeout=10
        )

        if resposta.status_code == 404:
            return JsonResponse({
                "valido": False,
                "mensagem": "CNPJ não encontrado na base consultada."
            }, status=404)

        if resposta.status_code == 400:
            return JsonResponse({
                "valido": False,
                "mensagem": "CNPJ rejeitado pela consulta."
            }, status=400)

        resposta.raise_for_status()
        dados = resposta.json()

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
            "mensagem": (
                "CNPJ ativo."
                if ativo else
                "CNPJ encontrado, mas não está ativo."
            )
        })

    except (requests.RequestException, ValueError):
        return JsonResponse({
            "valido": None,
            "mensagem": "Não foi possível consultar o CNPJ agora."
        }, status=503)
