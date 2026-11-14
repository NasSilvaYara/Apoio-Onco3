from ongs.models import TraducaoCache
from ongs.services import hash_texto

TRADUCOES = {
    "en": {
        "ONG / associação": "NGO / association",
        "Hospital": "Hospital",
        "Clínica / centro de tratamento": "Clinic / treatment center",
        "Casa de apoio": "Support house",
        "Instituto / fundação": "Institute / foundation",
        "Voluntariado / grupo de apoio": "Volunteering / support group",
        "Órgão público": "Public agency",
        "Outros": "Others",
        "Banco de perucas": "Wig bank",
        "Banco de lenços": "Headscarf bank",
        "Apoio psicológico": "Psychological support",
        "Assistência social": "Social assistance",
    },
}

for idioma, itens in TRADUCOES.items():
    for pt, trad in itens.items():
        TraducaoCache.objects.update_or_create(
            hash_texto=hash_texto(pt),
            idioma=idioma,
            defaults={"traducao": trad},
        )
print("Traduções cadastradas.")