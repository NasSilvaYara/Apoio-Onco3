import ongs.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ongs', '0006_instituicao_dados_cadastrais_complementares'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instituicao',
            name='cnpj',
            field=models.CharField(
                blank=True,
                max_length=18,
                null=True,
                unique=True,
                validators=[ongs.validators.validar_cnpj],
            ),
        ),
    ]
