
from django.db import models
from django.conf import settings

from .validators import validar_cnpj, validar_imagem_instituicao


class Administrador(models.Model):
    idAdm = models.AutoField(primary_key=True)
    nomeAdm = models.CharField(max_length=150)
    emailAdm = models.EmailField(unique=True)

    def __str__(self):
        return self.nomeAdm


class TipoApoio(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


class Instituicao(models.Model):

    TIPO_CHOICES = [
        ('ong_associacao', 'ONG / associação'),
        ('hospital', 'Hospital'),
        ('clinica_centro_tratamento', 'Clínica / centro de tratamento'),
        ('casa_apoio', 'Casa de apoio'),
        ('instituto_fundacao', 'Instituto / fundação'),
        ('voluntariado_grupo_apoio', 'Voluntariado / grupo de apoio'),
        ('orgao_publico', 'Órgão público'),
        ('outros', 'Outros'),
    ]

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('ativa', 'Ativa'),
        ('rejeitada', 'Rejeitada'),
        ('inativa', 'Inativa'),
    ]

    idInst = models.AutoField(primary_key=True)
    cnpj = models.CharField(
        max_length=14,
        unique=True,
        null=True,
        blank=True,
        validators=[validar_cnpj],
    )
    nomeInst = models.CharField(max_length=200)
    tipo = models.CharField(max_length=60, blank=True)
    descricao = models.TextField()
    conteudoInformativo = models.TextField(blank=True)
    logo = models.ImageField(
        upload_to='instituicoes/%Y/%m/',
        blank=True,
        null=True,
        validators=[validar_imagem_instituicao],
    )

    servicosOferecidos = models.ManyToManyField(
        TipoApoio,
        related_name='instituicoes',
        blank=True
    )

    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(unique=True)
    email_contato = models.EmailField(blank=True)
    site = models.URLField(blank=True)
    logradouro = models.CharField(max_length=250)
    cep = models.CharField(max_length=9, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=100)
    horarioAtendimento = models.CharField(max_length=200)
    telefone_whatsapp = models.CharField(max_length=20, blank=True)
    redes_sociais = models.CharField(max_length=200, blank=True)
    instagram = models.CharField(max_length=200, blank=True)
    facebook = models.CharField(max_length=200, blank=True)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pendente',
    )
    motivo_rejeicao = models.TextField(blank=True)
    avaliado_em = models.DateTimeField(null=True, blank=True)
    avaliado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='instituicoes_avaliadas',
        null=True,
        blank=True,
    )
    criado_em = models.DateTimeField(auto_now_add=True, null=True)
    atualizado_em = models.DateTimeField(auto_now=True, null=True)

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='instituicao',
        null=True,
        blank=True,
    )

    administrador = models.ForeignKey(
        Administrador,
        on_delete=models.PROTECT,
        related_name='instituicoes',
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.nomeInst
