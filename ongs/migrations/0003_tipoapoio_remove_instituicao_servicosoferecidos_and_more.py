
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ongs', '0002_tipos_apoio_iniciais'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='instituicao',
            name='servicosOferecidos',
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
    ]