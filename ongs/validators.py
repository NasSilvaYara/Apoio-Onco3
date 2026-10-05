"""Validadores e normalizadores usados pelos models."""
import re

from django.core.exceptions import ValidationError

_PESOS_DV1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
_PESOS_DV2 = [6] + _PESOS_DV1


def normalizar_cnpj(valor):
    """Remove máscara (. / -) e deixa em maiúsculas: '12.abc.345/01de-35' -> '12ABC34501DE35'."""
    return re.sub(r'[^0-9A-Za-z]', '', valor or '').upper()


def _digito(base, pesos):
    soma = sum((ord(c) - 48) * p for c, p in zip(base, pesos))
    resto = soma % 11
    return '0' if resto < 2 else str(11 - resto)


def cnpj_valido(valor):
    cnpj = normalizar_cnpj(valor)
    if not re.fullmatch(r'[0-9A-Z]{12}[0-9]{2}', cnpj):
        return False
    if len(set(cnpj)) == 1:  
        return False
    dv1 = _digito(cnpj[:12], _PESOS_DV1)
    dv2 = _digito(cnpj[:12] + dv1, _PESOS_DV2)
    return cnpj[12:] == dv1 + dv2


def gerar_cnpj(base12):
    """Completa uma base de 12 caracteres com os dois dígitos verificadores (útil em testes/seed)."""
    base12 = normalizar_cnpj(base12)
    dv1 = _digito(base12, _PESOS_DV1)
    dv2 = _digito(base12 + dv1, _PESOS_DV2)
    return base12 + dv1 + dv2


def validar_cnpj(valor):
    if not cnpj_valido(valor):
        raise ValidationError('CNPJ inválido.', code='cnpj_invalido')


