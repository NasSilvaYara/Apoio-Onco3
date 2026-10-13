
from django.db import migrations, models


def criar_tipos(apps, schema_editor):
    TipoApoio = apps.get_model('ongs', 'TipoApoio')
    db = schema_editor.connection.alias

    tipos = [
        ('Banco de perucas', 'Doação ou empréstimo de perucas.'),
        ('Banco de lenços', 'Lenços, turbantes e acessórios.'),
        ('Apoio psicológico', 'Acolhimento e atendimento psicológico.'),
        ('Assistência social', 'Orientação e apoio social.'),
    ]

    for nome, descricao in tipos:
        TipoApoio.objects.using(db).get_or_create(
            nome=nome,
            defaults={'descricao': descricao}
        )


class Migration(migrations.Migration):

    dependencies = [
        ('ongs', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TipoApoio',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID'
                    )
                ),
                ('nome', models.CharField(max_length=100, unique=True)),
                ('descricao', models.TextField()),
            ],
        ),

        migrations.RunPython(
            criar_tipos,
            migrations.RunPython.noop
        ),
    ]
