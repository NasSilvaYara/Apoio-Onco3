from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from .models import Instituicao, TipoApoio
from .validators import normalizar_cnpj, validar_cnpj, validar_imagem_instituicao

_UFS_BR = {
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT',
    'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO',
    'RR', 'SC', 'SP', 'SE', 'TO',
}


class LoginForm(forms.Form):
    email = forms.EmailField(
        error_messages={
            'required': 'Informe seu e-mail.',
            'invalid': 'Informe um endereço de e-mail válido.',
        },
    )
    senha = forms.CharField(
        strip=False,
        error_messages={'required': 'Informe sua senha.'},
    )

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()


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
    numero = forms.CharField(max_length=20, required=False)
    complemento = forms.CharField(max_length=100, required=False)
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
        if not cnpj.isdigit() or len(cnpj) != 14:
            raise ValidationError(
                'Informe um CNPJ com exatamente 14 dígitos numéricos.',
            )
        if Instituicao.cnpj_ja_cadastrado(cnpj):
            raise ValidationError(
                'Este CNPJ já está cadastrado na plataforma.',
            )
        return cnpj

    @staticmethod
    def email_ja_cadastrado(email):
        email = email.strip().lower()
        user_model = get_user_model()
        return (
            user_model.objects.filter(
                Q(username__iexact=email) | Q(email__iexact=email)
            ).exists()
            or Instituicao.objects.filter(email__iexact=email).exists()
        )

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
        if self.email_ja_cadastrado(email):
            raise ValidationError(
                'Este e-mail já está associado a uma conta ou instituição.'
            )
        return email

    def clean(self):
        cleaned_data = super().clean()
        contacts = ('telefone', 'whatsapp', 'email_contato', 'site')
        if not any(cleaned_data.get(field) for field in contacts):
            self.add_error(
                'telefone',
                ValidationError('Informe ao menos uma forma de contato.'),
            )

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
    numero = forms.CharField(max_length=20, required=False)
    complemento = forms.CharField(max_length=100, required=False)
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
    redes = forms.CharField(max_length=200, required=False)
    instagram = forms.CharField(max_length=200, required=False)
    facebook = forms.CharField(max_length=200, required=False)

    def clean(self):
        cleaned_data = super().clean()
        contact_fields = ('telefone', 'whatsapp', 'email_atendimento', 'site')
        if not any(cleaned_data.get(field) for field in contact_fields):
            raise ValidationError('Informe ao menos uma forma de contato.')
        return cleaned_data


class ConfiguracoesInstituicaoForm(forms.Form):
    nome = forms.CharField(max_length=200, label=_('Nome da instituição'))
    email = forms.EmailField(max_length=150, label=_('E-mail de acesso'))
    visivel = forms.BooleanField(required=False, label=_('Perfil visível nas buscas'))
    logo = forms.ImageField(
        required=False,
        label=_('Foto da instituição'),
        validators=[validar_imagem_instituicao],
        widget=forms.ClearableFileInput(attrs={
            'accept': '.jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp',
        }),
    )

    def __init__(self, *args, user, instituicao, **kwargs):
        self.user = user
        self.instituicao = instituicao
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        User = get_user_model()
        if User.objects.filter(
            Q(username__iexact=email) | Q(email__iexact=email)
        ).exclude(pk=self.user.pk).exists():
            raise ValidationError(_('Este e-mail já está associado a uma conta.'))
        if Instituicao.objects.filter(email__iexact=email).exclude(
            pk=self.instituicao.pk
        ).exists():
            raise ValidationError(_('Este e-mail já está associado a uma instituição.'))
        return email


class EmailAcessoForm(forms.Form):
    email = forms.EmailField(max_length=150, label=_('E-mail de acesso'))

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        User = get_user_model()
        if User.objects.filter(
            Q(username__iexact=email) | Q(email__iexact=email)
        ).exclude(pk=self.user.pk).exists():
            raise ValidationError(_('Este e-mail já está associado a uma conta.'))
        return email


class AlterarSenhaForm(forms.Form):
    senha_atual = forms.CharField(
        label=_('Senha atual'),
        strip=False,
        widget=forms.PasswordInput,
    )
    nova_senha = forms.CharField(
        label=_('Nova senha'),
        min_length=8,
        strip=False,
        widget=forms.PasswordInput,
    )
    confirmar_senha = forms.CharField(
        label=_('Confirmar nova senha'),
        strip=False,
        widget=forms.PasswordInput,
    )

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_senha_atual(self):
        senha = self.cleaned_data['senha_atual']
        if not self.user.check_password(senha):
            raise ValidationError(_('A senha atual está incorreta.'))
        return senha

    def clean_nova_senha(self):
        senha = self.cleaned_data['nova_senha']
        try:
            validate_password(senha, self.user)
        except ValidationError as error:
            raise ValidationError(error.messages) from error
        return senha

    def clean(self):
        cleaned_data = super().clean()
        nova_senha = cleaned_data.get('nova_senha')
        confirmar_senha = cleaned_data.get('confirmar_senha')
        if nova_senha and confirmar_senha and nova_senha != confirmar_senha:
            self.add_error(
                'confirmar_senha',
                _('As senhas não coincidem.'),
            )
        return cleaned_data


class ExcluirContaForm(forms.Form):
    senha_atual = forms.CharField(
        label=_('Senha atual'),
        strip=False,
        widget=forms.PasswordInput,
    )
    confirmar_exclusao = forms.BooleanField(
        label=_('Confirmo que desejo excluir a conta e seus dados.'),
        required=True,
    )

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_senha_atual(self):
        senha = self.cleaned_data['senha_atual']
        if not self.user.check_password(senha):
            raise ValidationError(_('A senha atual está incorreta.'))
        return senha


class AdministradorForm(forms.Form):
    nome = forms.CharField(max_length=150, label=_('Nome'))
    email = forms.EmailField(max_length=150, label=_('E-mail'))
    senha = forms.CharField(
        min_length=8,
        strip=False,
        widget=forms.PasswordInput,
        label=_('Senha'),
    )
    confirmar_senha = forms.CharField(
        strip=False,
        widget=forms.PasswordInput,
        label=_('Confirmar senha'),
    )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        User = get_user_model()
        usuarios = User.objects.filter(
            Q(username__iexact=email) | Q(email__iexact=email)
        )
        if usuarios.exists():
            raise ValidationError(_('Este e-mail já está associado a uma conta.'))
        return email

    def clean_senha(self):
        senha = self.cleaned_data.get('senha')
        if senha:
            try:
                validate_password(senha)
            except ValidationError as error:
                raise ValidationError(error.messages) from error
        return senha

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get('senha')
        confirmar_senha = cleaned_data.get('confirmar_senha')
        if senha and confirmar_senha and senha != confirmar_senha:
            self.add_error(
                'confirmar_senha',
                _('As senhas não coincidem.'),
            )
        return cleaned_data
