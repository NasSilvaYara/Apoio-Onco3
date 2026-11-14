import hashlib
import time
from django.utils.translation import get_language
from deep_translator import GoogleTranslator
from .models import TraducaoCache

_memoria = {}          # evita consultar o banco para o mesmo texto na mesma execução
_pausado_ate = 0       # se o Google bloquear, para de tentar por alguns minutos


def hash_texto(texto):
    return hashlib.sha256(texto.strip().encode("utf-8")).hexdigest()


def traduzir_texto(texto, idioma=None):
    global _pausado_ate
    if not texto:
        return texto
    idioma = (idioma or get_language() or "pt").split("-")[0].lower()
    if idioma == "pt":
        return texto

    h = hash_texto(texto)
    chave = (h, idioma)
    if chave in _memoria:
        return _memoria[chave]

    cache = TraducaoCache.objects.filter(hash_texto=h, idioma=idioma).first()
    if cache:
        _memoria[chave] = cache.traducao
        return cache.traducao

    if time.time() < _pausado_ate:
        return texto  # Google bloqueado há pouco: mostra o original sem esperar

    try:
        traduzido = GoogleTranslator(source="pt", target=idioma).translate(texto[:4900])
    except Exception as e:
        print("ERRO TRADUÇÃO:", repr(e))
        _pausado_ate = time.time() + 300  # pausa de 5 minutos
        return texto

    if traduzido:
        TraducaoCache.objects.get_or_create(
            hash_texto=h, idioma=idioma, defaults={"traducao": traduzido}
        )
        _memoria[chave] = traduzido
        return traduzido
    return texto