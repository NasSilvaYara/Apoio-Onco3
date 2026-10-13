
from django.db import models


class Administrador(models.Model):
    idAdm = models.AutoField(primary_key=True)
    nomeAdm = models.CharField(max_length=150)
    emailAdm = models.EmailField(unique=True)

    def __str__(self):
        return self.nomeAdm


class TipoApoio(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField()

    def __str__(self):
        return self.nome


class Instituicao(models.Model):

    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
    ]

    idInst = models.AutoField(primary_key=True)
    nomeInst = models.CharField(max_length=200)
    descricao = models.TextField()
    conteudoInformativo = models.TextField()

    servicosOferecidos = models.ManyToManyField(
        TipoApoio,
        related_name='instituicoes',
        blank=True
    )

    telefone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    site = models.URLField(blank=True)
    logradouro = models.CharField(max_length=250)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=100)
    horarioAtendimento = models.CharField(max_length=200)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ativo'
    )

    administrador = models.ForeignKey(
        Administrador,
        on_delete=models.PROTECT,
        related_name='instituicoes'
    )

    def __str__(self):
        return self.nomeInst
