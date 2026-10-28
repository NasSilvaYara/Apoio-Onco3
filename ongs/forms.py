from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q

from .models import Instituicao, TipoApoio
from .validators import normalizar_cnpj, validar_cnpj, validar_imagem_instituicao

_UFS_BR = {
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT',
    'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO',
    'RR', 'SC', 'SP', 'SE', 'TO',
}


class CadastroInstituicaoForm(forms.Form):
    cnpj = forms.CharField(max_length=18, validators=[validar_cnpj])
    nome = forms.CharField(max_length=200)
    tipo = forms.ChoiceField(choices=Instituicao.TIPO_CHOICES)
    descricao = forms.CharField(max_length=300)
    imagem_instituicao = forms.ImageField(
        validators=[validar_imagem_instituicao],
        error_messages={'required': 'Envie uma imagem da instituição.'},
    )
    horario = forms.CharField(max_length=200)
    servicos = forms.ModelMultipleChoiceField(
        queryset=TipoApoio.objects.none(),
        required=True,
        error_messages={'required': 'Selecione pelo menos um tipo de serviço.'},
    )
    cep = forms.CharField(max_length=9)
    estado = forms.RegexField(regex=r'^[A-Za-z]{2}$', max_length=2)
    endereco = forms.CharField(max_length=250)
    bairro = forms.CharField(max_length=100)
    cidade = forms.CharField(max_length=100)
    telefone = forms.CharField(max_length=20, required=False)
    whatsapp = forms.CharField(max_length=20, required=False)
    email_contato = forms.EmailField(required=False)
    site = forms.URLField(required=False)
    redes = forms.CharField(max_length=200, required=False)
    email = forms.EmailField(max_length=150)
    senha = forms.CharField(min_length=8, strip=False)
    senha2 = forms.CharField(strip=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['servicos'].queryset = TipoApoio.objects.filter(ativo=True)

    def clean_cnpj(self):
        cnpj = normalizar_cnpj(self.cleaned_data['cnpj'])
        if Instituicao.objects.filter(cnpj=cnpj).exists():
            raise ValidationError('Já existe uma instituição cadastrada com este CNPJ.')
        return cnpj

    def clean_cep(self):
        cep = ''.join(char for char in self.cleaned_data['cep'] if char.isdigit())
        if len(cep) != 8:
            raise ValidationError('Informe um CEP válido com 8 dígitos.')
        return f'{cep[:5]}-{cep[5:]}'

    def clean_estado(self):
        estado = self.cleaned_data['estado'].upper()
        if estado not in _UFS_BR:
            raise ValidationError('Informe uma sigla válida de estado brasileiro.')
        return estado

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        user_model = get_user_model()
        if user_model.objects.filter(
            Q(username__iexact=email) | Q(email__iexact=email)
        ).exists():
            raise ValidationError('Este e-mail já está associado a uma conta.')
        if Instituicao.objects.filter(email__iexact=email).exists():
            raise ValidationError('Este e-mail já está associado a uma instituição.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        contacts = ('telefone', 'whatsapp', 'email_contato', 'site')
        if not any(cleaned_data.get(field) for field in contacts):
            raise ValidationError('Informe ao menos uma forma de contato.')

        senha = cleaned_data.get('senha')
        senha2 = cleaned_data.get('senha2')
        if senha and senha2 and senha != senha2:
            self.add_error('senha2', 'As senhas não coincidem.')
        if senha:
            try:
                validate_password(senha)
            except ValidationError as error:
                self.add_error('senha', error)
        return cleaned_data


class PerfilInstituicaoForm(forms.Form):
    nome = forms.CharField(max_length=200)
    tipo = forms.ChoiceField(choices=Instituicao.TIPO_CHOICES)
    descricao = forms.CharField(max_length=300)
    logo = forms.ImageField(required=False, validators=[validar_imagem_instituicao])
    cep = forms.CharField(max_length=9)
    logradouro = forms.CharField(max_length=250)
    bairro = forms.CharField(max_length=100)
    cidade = forms.CharField(max_length=100)
    estado = forms.RegexField(regex=r'^[A-Za-z]{2}$', max_length=2)
    horario = forms.CharField(max_length=200)
    servicos = forms.ModelMultipleChoiceField(
        queryset=TipoApoio.objects.none(),
        to_field_name='nome',
        required=True,
        error_messages={
            'required': 'Selecione pelo menos um tipo de apoio.',
            'invalid_choice': 'Um ou mais tipos de apoio selecionados são inválidos.',
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['servicos'].queryset = TipoApoio.objects.all()

    def clean_cep(self):
        cep = ''.join(char for char in self.cleaned_data['cep'] if char.isdigit())
        if len(cep) != 8:
            raise ValidationError('Informe um CEP válido com 8 dígitos.')
        return f'{cep[:5]}-{cep[5:]}'

    def clean_estado(self):
        estado = self.cleaned_data['estado'].upper()
        if estado not in _UFS_BR:
            raise ValidationError('Informe uma sigla válida de estado brasileiro.')
        return estado


class ContatoInstituicaoForm(forms.Form):
    telefone = forms.CharField(max_length=20, required=False)
    whatsapp = forms.CharField(max_length=20, required=False)
    email_atendimento = forms.EmailField(required=False)
    site = forms.URLField(required=False)
    instagram = forms.CharField(max_length=200, required=False)
    facebook = forms.CharField(max_length=200, required=False)

    def clean(self):
        cleaned_data = super().clean()
        contact_fields = ('telefone', 'whatsapp', 'email_atendimento', 'site')
        if not any(cleaned_data.get(field) for field in contact_fields):
            raise ValidationError('Informe ao menos uma forma de contato.')
        return cleaned_data
