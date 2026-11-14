from django import template
from ..services import traduzir_texto

register = template.Library()

@register.filter
def traduzir(valor):
    return traduzir_texto(valor)