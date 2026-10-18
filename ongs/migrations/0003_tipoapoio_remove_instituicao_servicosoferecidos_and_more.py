
from django.db import migrations, models


def migrar_servicos_legados(apps, schema_editor):
    Instituicao = apps.get_model('ongs', 'Instituicao')
    TipoApoio = apps.get_model('ongs', 'TipoApoio')
    banco = schema_editor.connection.alias

    for instituicao in Instituicao.objects.using(banco).all().iterator():
        valores = (instituicao.servicosLegados or '').replace(';', ',').split(',')
        for valor in valores:
            nome = valor.strip().strip('[]\'"')
            if not nome:
                continue
            tipo = TipoApoio.objects.using(banco).filter(nome__iexact=nome).first()
            if tipo is None:
                tipo = TipoApoio.objects.using(banco).create(nome=nome, descricao='')
            instituicao.servicosOferecidos.add(tipo)


def reverter_servicos_legados(apps, schema_editor):
    Instituicao = apps.get_model('ongs', 'Instituicao')
    banco = schema_editor.connection.alias

    for instituicao in Instituicao.objects.using(banco).all().iterator():
        instituicao.servicosLegados = ', '.join(
            instituicao.servicosOferecidos.values_list('nome', flat=True)
        )
        instituicao.save(update_fields=['servicosLegados'])


class Migration(migrations.Migration):

    dependencies = [
        ('ongs', '0002_tipos_apoio_iniciais'),
    ]

    operations = [
        migrations.RenameField(
            model_name='instituicao',
            old_name='servicosOferecidos',
            new_name='servicosLegados',
        ),

        migrations.AddField(
            model_name='instituicao',
            name='servicosOferecidos',
            field=models.ManyToManyField(
                blank=True,
                related_name='instituicoes',
                to='ongs.tipoapoio'
            ),
        ),
        migrations.RunPython(migrar_servicos_legados, reverter_servicos_legados),
        migrations.RemoveField(
            model_name='instituicao',
            name='servicosLegados',
        ),
    ]