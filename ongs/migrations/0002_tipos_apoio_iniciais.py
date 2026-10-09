from django.db import migrations

TIPOS = [
    ('Banco de perucas', 'Doação ou empréstimo de perucas.'),
    ('Banco de lenços', 'Lenços, turbantes e acessórios.'),
    ('Apoio psicológico', 'Acolhimento e atendimento psicológico.'),
    ('Assistência social', 'Orientação e apoio social.'),
]


def criar_tipos(apps, schema_editor):
    TipoApoio = apps.get_model('ongs', 'TipoApoio')
    for nome, descricao in TIPOS:
        TipoApoio.objects.get_or_create(nome=nome, defaults={'descricao': descricao})


def remover_tipos(apps, schema_editor):
    apps.get_model('ongs', 'TipoApoio').objects.filter(nome__in=[n for n, _ in TIPOS]).delete()


class Migration(migrations.Migration):
    dependencies = [('ongs', '0001_initial')]
    operations = [migrations.RunPython(criar_tipos, remover_tipos)]
