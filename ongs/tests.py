
import json
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import requests
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import (
    RequestFactory,
    SimpleTestCase,
    TestCase,
    override_settings,
)
from django.urls import reverse
from PIL import Image

from .cnpj_api import consultar_cnpj
from .models import Instituicao, TipoApoio
from .validators import (
    gerar_cnpj,
    cnpj_valido,
    validar_imagem_instituicao,
)


class InformacoesViewTests(TestCase):
    def test_each_topic_displays_its_own_content(self):
        temas = {
            'entenda-o-cancer': 'Entenda o câncer',
            'saude-emocional': 'Saúde emocional',
            'autoestima-no-tratamento': 'Autoestima durante o tratamento',
        }

        for slug, titulo in temas.items():
            with self.subTest(tema=slug):
                response = self.client.get(f'/informacoes/{slug}/')

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, titulo)
                self.assertTemplateUsed(
                    response, 'informacoes-para-voce.html'
                )

    def test_unknown_topic_returns_not_found(self):
        response = self.client.get('/informacoes/tema-inexistente/')

        self.assertEqual(response.status_code, 404)


class ValidacaoSemBancoTests(SimpleTestCase):
    def test_cnpj_checksum_and_supported_image_formats(self):
        self.assertTrue(cnpj_valido(gerar_cnpj('112223330001')))
        self.assertTrue(cnpj_valido('12.ABC.DEF/0001-36'))
        self.assertFalse(cnpj_valido('11.222.333/0001-80'))
        self.assertFalse(cnpj_valido('00.000.000/0000-00'))

        for formato, extensao in (
            ('JPEG', 'jpg'),
            ('JPEG', 'jpeg'),
            ('PNG', 'png'),
            ('WEBP', 'webp'),
        ):
            conteudo = BytesIO()
            Image.new('RGB', (4, 4)).save(conteudo, format=formato)
            arquivo = SimpleUploadedFile(
                f'logo.{extensao}',
                conteudo.getvalue(),
                content_type=f'image/{extensao}',
            )
            validar_imagem_instituicao(arquivo)

    def test_image_size_limit(self):
        arquivo = SimpleUploadedFile(
            'grande.png',
            b'x' * (5 * 1024 * 1024 + 1),
        )
        with self.assertRaisesMessage(
            ValidationError,
            'A imagem deve ter no máximo 5 MB.',
        ):
            validar_imagem_instituicao(arquivo)

    @patch('ongs.cnpj_api.Instituicao.cnpj_ja_cadastrado', return_value=False)
    @patch('ongs.cnpj_api.consultar_dados_cnpj')
    def test_cnpj_api_checks_local_value_and_activity(
        self,
        consultar,
        cnpj_ja_cadastrado,
    ):
        request = RequestFactory().get('/')
        request.session = {}
        cnpj = gerar_cnpj('112223330001')
        consultar.return_value = {
            'descricao_situacao_cadastral': 'ATIVA'
        }

        resposta = consultar_cnpj(request, cnpj)
        self.assertTrue(json.loads(resposta.content)['ativo'])

        resposta = consultar_cnpj(
            request,
            '00.000.000/0000-00',
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            json.loads(resposta.content)['mensagem'],
            'CNPJ inválido. Verifique os números informados.',
        )
        self.assertEqual(consultar.call_count, 1)


class PlataformaTests(TestCase):
    def setUp(self):
        self.media_dir = TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)

        media_settings = override_settings(
            MEDIA_ROOT=self.media_dir.name
        )
        media_settings.enable()
        self.addCleanup(media_settings.disable)

        self.tipo_apoio, _ = TipoApoio.objects.get_or_create(
            nome='Banco de perucas',
            defaults={'descricao': 'Apoio com perucas.'},
        )

    def imagem_png(self, nome='logo.png'):
        conteudo = BytesIO()
        Image.new(
            'RGB',
            (4, 4),
            color='white',
        ).save(conteudo, format='PNG')

        return SimpleUploadedFile(
            nome,
            conteudo.getvalue(),
            content_type='image/png',
        )

    def dados_cadastro(
        self,
        base='112223330001',
        email='instituicao@example.org',
    ):
        return {
            'cnpj': gerar_cnpj(base),
            'nome': 'Instituição Exemplo',
            'tipo': 'ong_associacao',
            'descricao': 'Atendimento e acolhimento.',
            'horario': 'Segunda a sexta, das 8h às 17h',
            'servicos': [str(self.tipo_apoio.pk)],
            'cep': '01001-000',
            'estado': 'sp',
            'endereco': 'Praça da Sé',
            'numero': '123',
            'complemento': 'Sala 4',
            'bairro': 'Sé',
            'cidade': 'São Paulo',
            'telefone': '(11) 3000-0000',
            'whatsapp': '',
            'email_contato': 'contato@example.org',
            'site': '',
            'redes': '',
            'email': email,
            'senha': 'ApoioOnco!2026',
            'senha2': 'ApoioOnco!2026',
            'imagem_instituicao': self.imagem_png(),
        }

    def criar_instituicao(
        self,
        nome,
        status='ativa',
        base='223334440001',
    ):
        User = get_user_model()
        email = f'{nome.lower().replace(" ", ".")}@example.org'

        usuario = User.objects.create_user(
            username=email,
            email=email,
            password='ApoioOnco!2026',
        )

        instituicao = Instituicao.objects.create(
            cnpj=gerar_cnpj(base),
            nomeInst=nome,
            tipo='ong_associacao',
            descricao='Descrição da instituição.',
            conteudoInformativo='',
            telefone='(11) 3000-0000',
            email=email,
            email_contato=email,
            logradouro='Rua Exemplo',
            cep='01001-000',
            bairro='Centro',
            cidade='São Paulo',
            estado='SP',
            horarioAtendimento='Dias úteis',
            status=status,
            usuario=usuario,
        )
        instituicao.servicosOferecidos.add(self.tipo_apoio)

        return usuario, instituicao

    def test_mysql_connection_uses_expected_backend(self):
        self.assertEqual(connection.vendor, 'mysql')

        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            self.assertEqual(cursor.fetchone()[0], 1)

    @patch('ongs.views.consultar_dados_cnpj')
    def test_valid_active_cnpj_creates_pending_institution_and_hashed_user(
        self,
        consultar,
    ):
        consultar.return_value = {
            'descricao_situacao_cadastral': 'ATIVA',
            'razao_social': 'Razão social de teste',
            'nome_fantasia': 'Nome fantasia de teste',
        }
        dados = self.dados_cadastro()

        response = self.client.post(reverse('cadastro'), dados)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('cadastro_sucesso'))
        sucesso = self.client.get(response.url)
        self.assertEqual(sucesso.status_code, 200)
        self.assertTrue(sucesso.context['cadastro_enviado'])
        self.assertContains(sucesso, 'Cadastro enviado!')

        instituicao = Instituicao.objects.get(cnpj=dados['cnpj'])
        self.assertEqual(instituicao.status, 'pendente')
        self.assertEqual(instituicao.razao_social, 'Razão social de teste')
        self.assertEqual(instituicao.nome_fantasia, 'Nome fantasia de teste')
        self.assertEqual(instituicao.numero, '123')
        self.assertEqual(instituicao.complemento, 'Sala 4')
        self.assertTrue(
            instituicao.logo.name.startswith('instituicoes/')
        )
        self.assertTrue(
            default_storage.exists(instituicao.logo.name)
        )
        self.assertEqual(
            instituicao.servicosOferecidos.count(),
            1,
        )
        self.assertEqual(
            instituicao.usuario.email,
            dados['email'],
        )
        self.assertTrue(
            instituicao.usuario.check_password(dados['senha'])
        )
        self.assertNotEqual(
            instituicao.usuario.password,
            dados['senha'],
        )
        consultar.assert_called_once_with(dados['cnpj'])

    @patch('ongs.views.consultar_dados_cnpj')
    @patch('ongs.cnpj_api.consultar_dados_cnpj')
    def test_browser_validation_token_avoids_second_brasilapi_lookup(
        self,
        consultar_api,
        consultar_cadastro,
    ):
        cnpj = gerar_cnpj('112223330001')
        consultar_api.return_value = {
            'cnpj': cnpj,
            'descricao_situacao_cadastral': 'ATIVA',
            'razao_social': 'Razão social de teste',
            'nome_fantasia': 'Nome fantasia de teste',
        }

        validacao = self.client.get(reverse('consultar_cnpj', args=[cnpj]))
        self.assertEqual(validacao.status_code, 200)
        token = validacao.json()['token_validacao']
        self.assertTrue(token)

        dados = self.dados_cadastro()
        dados['token_validacao_cnpj'] = token
        response = self.client.post(reverse('cadastro'), dados)

        self.assertEqual(response.status_code, 302)
        consultar_api.assert_called_once_with(cnpj)
        consultar_cadastro.assert_not_called()

    @patch('ongs.views.consultar_dados_cnpj')
    @patch('ongs.cnpj_api.consultar_dados_cnpj')
    def test_expired_browser_token_requires_server_side_revalidation(
        self,
        consultar_api,
        consultar_cadastro,
    ):
        cnpj = gerar_cnpj('112223330001')
        consultar_api.return_value = {
            'cnpj': cnpj,
            'descricao_situacao_cadastral': 'ATIVA',
        }
        consultar_cadastro.return_value = {
            'cnpj': cnpj,
            'descricao_situacao_cadastral': 'ATIVA',
        }

        validacao = self.client.get(reverse('consultar_cnpj', args=[cnpj]))
        dados = self.dados_cadastro()
        dados['token_validacao_cnpj'] = validacao.json()['token_validacao']

        with patch('ongs.cnpj_api._TOKEN_CNPJ_MAX_AGE', -1):
            response = self.client.post(reverse('cadastro'), dados)

        self.assertEqual(response.status_code, 302)
        consultar_api.assert_called_once_with(cnpj)
        consultar_cadastro.assert_called_once_with(cnpj)

    @patch('ongs.views.consultar_dados_cnpj')
    def test_registration_rate_limit_message_respects_retry_after(
        self,
        consultar,
    ):
        resposta_api = Mock(
            status_code=429,
            headers={'Retry-After': '37'},
        )
        consultar.side_effect = requests.HTTPError(response=resposta_api)
        dados = self.dados_cadastro()

        with self.assertLogs('ongs.cnpj_api', level='ERROR'):
            response = self.client.post(reverse('cadastro'), dados)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['cnpj_retry_after'], 37)
        self.assertEqual(
            response.context['form'].errors['cnpj'],
            [
                'A consulta do CNPJ atingiu o limite de requisições. '
                'Tente novamente em 37 segundos.'
            ],
        )
        self.assertContains(response, 'data-cnpj-retry-after="37"')
        consultar.assert_called_once_with(dados['cnpj'])

    @patch('ongs.views.consultar_dados_cnpj')
    def test_invalid_cnpj_is_rejected_without_external_lookup(
        self,
        consultar,
    ):
        dados = self.dados_cadastro()
        dados['cnpj'] = '00.000.000/0000-00'

        response = self.client.post(reverse('cadastro'), dados)

        self.assertEqual(response.status_code, 200)
        self.assertIn('cnpj', response.context['form'].errors)
        self.assertEqual(
            response.context['form'].errors['cnpj'],
            ['CNPJ inválido. Verifique os números informados.'],
        )
        self.assertContains(response, 'data-field="cnpj"', html=False)
        consultar.assert_not_called()

    @patch('ongs.views.consultar_dados_cnpj')
    def test_inactive_cnpj_is_rejected(self, consultar):
        consultar.return_value = {
            'descricao_situacao_cadastral': 'INAPTA'
        }
        dados = self.dados_cadastro()

        response = self.client.post(reverse('cadastro'), dados)

        self.assertEqual(response.status_code, 200)
        self.assertIn('cnpj', response.context['form'].errors)
        self.assertEqual(
            response.context['form'].errors['cnpj'],
            ['Este CNPJ não possui situação cadastral ativa.'],
        )
        self.assertFalse(
            Instituicao.objects.filter(
                cnpj=dados['cnpj']
            ).exists()
        )

    @patch('ongs.views.consultar_dados_cnpj')
    def test_duplicate_cnpj_is_rejected_before_lookup(
        self,
        consultar,
    ):
        _, existente = self.criar_instituicao('Existente')
        dados = self.dados_cadastro(base='334445550001')
        dados['cnpj'] = existente.cnpj

        response = self.client.post(reverse('cadastro'), dados)

        self.assertEqual(response.status_code, 200)
        self.assertIn('cnpj', response.context['form'].errors)
        self.assertEqual(
            response.context['form'].errors['cnpj'],
            ['Este CNPJ já está cadastrado na plataforma.'],
        )
        consultar.assert_not_called()

    @patch('ongs.views.consultar_dados_cnpj')
    def test_duplicate_cnpj_with_and_without_punctuation_is_rejected(
        self,
        consultar,
    ):
        _, formatted = self.criar_instituicao(
            'Pendente formatada',
            status='pendente',
            base='223334440001',
        )
        formatted.cnpj = (
            f'{formatted.cnpj[:2]}.{formatted.cnpj[2:5]}.'
            f'{formatted.cnpj[5:8]}/{formatted.cnpj[8:12]}-'
            f'{formatted.cnpj[12:]}'
        )
        formatted.save(update_fields=['cnpj'])

        dados_sem_pontuacao = self.dados_cadastro(base='334445550001')
        dados_sem_pontuacao['cnpj'] = gerar_cnpj('223334440001')
        response = self.client.post(
            reverse('cadastro'),
            dados_sem_pontuacao,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['form'].errors['cnpj'],
            ['Este CNPJ já está cadastrado na plataforma.'],
        )
        consultar.assert_not_called()

        _, sem_pontuacao = self.criar_instituicao(
            'Inativa sem pontuação',
            status='inativa',
            base='445556660001',
        )
        dados_formatados = self.dados_cadastro(base='556667770001')
        dados_formatados['cnpj'] = (
            f'{sem_pontuacao.cnpj[:2]}.{sem_pontuacao.cnpj[2:5]}.'
            f'{sem_pontuacao.cnpj[5:8]}/{sem_pontuacao.cnpj[8:12]}-'
            f'{sem_pontuacao.cnpj[12:]}'
        )
        response = self.client.post(reverse('cadastro'), dados_formatados)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['form'].errors['cnpj'],
            ['Este CNPJ já está cadastrado na plataforma.'],
        )
        consultar.assert_not_called()

    @patch('ongs.views.consultar_dados_cnpj', side_effect=requests.Timeout)
    def test_registration_timeout_shows_safe_cnpj_error(self, consultar):
        dados = self.dados_cadastro()

        with self.assertLogs('ongs.cnpj_api', level='ERROR') as logs:
            response = self.client.post(reverse('cadastro'), dados)

        mensagem = (
            'Não foi possível consultar o CNPJ no momento. '
            'Tente novamente mais tarde.'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].errors['cnpj'], [mensagem])
        self.assertContains(response, mensagem)
        self.assertIn('categoria=timeout', logs.output[0])
        consultar.assert_called_once()

    @patch('ongs.cnpj_api.consultar_dados_cnpj')
    def test_cnpj_api_reports_specific_external_failure_categories(
        self,
        consultar,
    ):
        cnpj = gerar_cnpj('112223330001')
        response_404 = Mock(status_code=404)
        response_429 = Mock(status_code=429)
        response_503 = Mock(status_code=503)
        falhas = (
            (requests.Timeout(), 504, 'timeout'),
            (requests.ConnectionError(), 503, 'conexao'),
            (requests.HTTPError(response=response_404), 404, 'nao_encontrado'),
            (
                requests.HTTPError(response=response_429),
                429,
                'limite_requisicoes',
            ),
            (
                requests.HTTPError(response=response_503),
                502,
                'indisponivel',
            ),
        )

        for erro, status, codigo in falhas:
            with self.subTest(codigo=codigo):
                consultar.side_effect = erro
                with self.assertLogs('ongs.cnpj_api', level='ERROR'):
                    response = self.client.get(
                        reverse('consultar_cnpj', args=[cnpj]),
                    )

                dados = response.json()
                self.assertEqual(response.status_code, status)
                self.assertEqual(dados['codigo_erro'], codigo)
                self.assertEqual(
                    dados['mensagem'],
                    'CNPJ não encontrado na base consultada.'
                    if codigo == 'nao_encontrado'
                    else (
                        'A consulta do CNPJ atingiu o limite de requisições. '
                        'Tente novamente mais tarde.'
                        if codigo == 'limite_requisicoes'
                        else 'Não foi possível consultar o CNPJ no momento. '
                        'Tente novamente mais tarde.'
                    ),
                )

    @patch('ongs.cnpj_api.consultar_dados_cnpj')
    def test_cnpj_api_returns_retry_after_for_rate_limit(self, consultar):
        resposta_api = Mock(
            status_code=429,
            headers={'Retry-After': '42'},
        )
        consultar.side_effect = requests.HTTPError(response=resposta_api)
        cnpj = gerar_cnpj('112223330001')

        with self.assertLogs('ongs.cnpj_api', level='ERROR'):
            response = self.client.get(
                reverse('consultar_cnpj', args=[cnpj]),
            )

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response['Retry-After'], '42')
        self.assertEqual(
            response.json()['mensagem'],
            'A consulta do CNPJ atingiu o limite de requisições. '
            'Tente novamente em 42 segundos.',
        )

    @patch('ongs.cnpj_api.requests.get')
    def test_cnpj_api_rejects_invalid_brasilapi_payload(self, get):
        resposta = Mock()
        resposta.json.return_value = []
        get.return_value = resposta
        cnpj = gerar_cnpj('112223330001')

        with self.assertLogs('ongs.cnpj_api', level='ERROR'):
            response = self.client.get(
                reverse('consultar_cnpj', args=[cnpj]),
            )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()['codigo_erro'], 'resposta_invalida')
        self.assertEqual(
            response.json()['mensagem'],
            'Não foi possível consultar o CNPJ no momento. '
            'Tente novamente mais tarde.',
        )

    @patch('ongs.cnpj_api.consultar_dados_cnpj')
    def test_cnpj_api_rejects_existing_cnpj_before_external_lookup(
        self,
        consultar,
    ):
        _, existente = self.criar_instituicao(
            'Instituição já cadastrada',
            status='pendente',
        )

        response = self.client.get(
            reverse('consultar_cnpj', args=[existente.cnpj]),
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()['mensagem'],
            'Este CNPJ já está cadastrado na plataforma.',
        )
        consultar.assert_not_called()

    @patch('ongs.views.consultar_dados_cnpj')
    def test_registration_requires_an_image(self, consultar):
        dados = self.dados_cadastro()
        dados.pop('imagem_instituicao')

        response = self.client.post(reverse('cadastro'), dados)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'imagem_instituicao',
            response.context['form'].errors,
        )
        consultar.assert_not_called()

    @patch('ongs.views.consultar_dados_cnpj')
    def test_invalid_image_file_is_rejected(self, consultar):
        dados = self.dados_cadastro()
        dados['imagem_instituicao'] = SimpleUploadedFile(
            'nao-e-imagem.png',
            b'arquivo invalido',
            content_type='image/png',
        )

        response = self.client.post(reverse('cadastro'), dados)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'imagem_instituicao',
            response.context['form'].errors,
        )
        consultar.assert_not_called()

    def test_institution_login_and_admin_permissions(self):
        usuario, instituicao = self.criar_instituicao(
            'Conta Instituição',
            status='pendente',
        )

        response = self.client.post(
            reverse('login'),
            {
                'identificacao': instituicao.cnpj,
                'senha': 'ApoioOnco!2026',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('dashboard_instituicao'),
        )
        self.assertEqual(
            self.client.get(
                reverse('dashboard_instituicao_perfil')
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                reverse('dashboard_admin')
            ).status_code,
            403,
        )

        self.client.logout()

        admin = get_user_model().objects.create_user(
            username='admin@example.org',
            email='admin@example.org',
            password='ApoioOnco!2026',
            is_staff=True,
        )
        self.client.force_login(admin)

        response = self.client.get(reverse('dashboard_admin'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.client.get(
                reverse('dashboard_instituicao')
            ).status_code,
            403,
        )

    def test_administrator_approval_and_rejection_are_persisted(self):
        admin = get_user_model().objects.create_user(
            username='moderador@example.org',
            email='moderador@example.org',
            password='ApoioOnco!2026',
            is_staff=True,
        )

        _, aprovada = self.criar_instituicao(
            'Para Aprovar',
            status='pendente',
        )
        _, rejeitada = self.criar_instituicao(
            'Para Rejeitar',
            status='pendente',
            base='334445550001',
        )

        self.client.force_login(admin)

        self.client.post(
            reverse('dashboard_admin_gerenciar'),
            {
                'instituicao_id': aprovada.pk,
                'acao': 'aprovar',
            },
        )
        self.client.post(
            reverse('dashboard_admin_gerenciar'),
            {
                'instituicao_id': rejeitada.pk,
                'acao': 'rejeitar',
                'motivo_rejeicao': 'Dados insuficientes.',
            },
        )

        aprovada.refresh_from_db()
        rejeitada.refresh_from_db()

        self.assertEqual(aprovada.status, 'ativa')
        self.assertEqual(aprovada.avaliado_por, admin)
        self.assertEqual(rejeitada.status, 'rejeitada')
        self.assertEqual(
            rejeitada.motivo_rejeicao,
            'Dados insuficientes.',
        )

    def test_administrator_can_inactivate_and_reactivate_institution(self):
        admin = get_user_model().objects.create_user(
            username='reativador@example.org',
            email='reativador@example.org',
            password='ApoioOnco!2026',
            is_staff=True,
        )
        _, instituicao = self.criar_instituicao(
            'Para Desativar',
            status='ativa',
        )
        self.client.force_login(admin)

        for action, expected_status in (
            ('inativar', 'inativa'),
            ('reativar', 'ativa'),
        ):
            response = self.client.post(
                reverse('dashboard_admin_gerenciar'),
                {
                    'instituicao_id': instituicao.pk,
                    'acao': action,
                },
                HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['status'], expected_status)
            instituicao.refresh_from_db()
            self.assertEqual(instituicao.status, expected_status)
            self.assertEqual(instituicao.avaliado_por, admin)
            self.assertIsNotNone(instituicao.avaliado_em)

    def test_manage_page_displays_safe_institution_details(self):
        admin = get_user_model().objects.create_user(
            username='revisora@example.org',
            email='revisora@example.org',
            password='ApoioOnco!2026',
            is_staff=True,
        )
        user, instituicao = self.criar_instituicao(
            'Instituição em análise',
            status='pendente',
        )
        instituicao.razao_social = 'Razão social cadastrada'
        instituicao.nome_fantasia = 'Nome fantasia cadastrado'
        instituicao.tipo = 'hospital'
        instituicao.descricao = 'Atendimento e acolhimento.'
        instituicao.conteudoInformativo = 'Informações de atendimento.'
        instituicao.horarioAtendimento = 'Segunda a sexta, das 8h às 17h'
        instituicao.cep = '01001-000'
        instituicao.logradouro = 'Praça da Sé'
        instituicao.numero = '123'
        instituicao.complemento = 'Sala 4'
        instituicao.bairro = 'Sé'
        instituicao.telefone = '(11) 3000-0000'
        instituicao.telefone_whatsapp = '(11) 99999-0000'
        instituicao.email_contato = 'contato@example.org'
        instituicao.site = 'https://example.org'
        instituicao.redes_sociais = '@instituicao'
        instituicao.instagram = '@instituicao'
        instituicao.facebook = 'facebook.com/instituicao'
        instituicao.logo = self.imagem_png('logo-cadastro.png')
        instituicao.save()
        self.client.force_login(admin)

        response = self.client.get(reverse('dashboard_admin_gerenciar'))

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('user', response.context)
        details = response.context['instituicoes'][0]
        self.assertEqual(details['email_acesso'], user.email)
        self.assertEqual(details['razao_social'], 'Razão social cadastrada')
        self.assertEqual(details['nome_fantasia'], 'Nome fantasia cadastrado')
        self.assertEqual(details['descricao'], 'Atendimento e acolhimento.')
        self.assertEqual(details['conteudo_informativo'], 'Informações de atendimento.')
        self.assertEqual(details['horario'], 'Segunda a sexta, das 8h às 17h')
        self.assertEqual(details['cep'], '01001-000')
        self.assertEqual(details['logradouro'], 'Praça da Sé')
        self.assertEqual(details['numero'], '123')
        self.assertEqual(details['complemento'], 'Sala 4')
        self.assertEqual(details['bairro'], 'Sé')
        self.assertEqual(details['telefone'], '(11) 3000-0000')
        self.assertEqual(details['whatsapp'], '(11) 99999-0000')
        self.assertEqual(details['email_contato'], 'contato@example.org')
        self.assertEqual(details['site'], 'https://example.org')
        self.assertEqual(details['redes_sociais'], '@instituicao')
        self.assertEqual(details['instagram'], '@instituicao')
        self.assertEqual(details['facebook'], 'facebook.com/instituicao')
        self.assertIn(self.tipo_apoio.nome, details['servicos'])
        self.assertTrue(details['logo_url'].endswith('logo-cadastro.png'))
        self.assertNotIn('password', details)
        self.assertNotIn('senha', details)
        self.assertNotIn(user.password, response.content.decode())
        self.assertContains(response, 'instituicoes-data')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, 'Senhas não são exibidas por segurança.')
        for field in (
            'cnpj_formatado',
            'razao_social',
            'nome_fantasia',
            'nome',
            'tipo_display',
            'descricao',
            'conteudo_informativo',
            'horario',
            'servicos',
            'cep',
            'logradouro',
            'numero',
            'complemento',
            'bairro',
            'cidade',
            'estado',
            'telefone',
            'whatsapp',
            'email_contato',
            'instagram',
            'facebook',
            'redes_sociais',
            'email_acesso',
        ):
            self.assertContains(response, f'data-detail="{field}"')
        self.assertContains(response, 'data-detail-link="site"')

    def test_manage_page_uses_three_status_labels_and_icon_actions(self):
        admin = get_user_model().objects.create_user(
            username='status-admin@example.org',
            email='status-admin@example.org',
            password='ApoioOnco!2026',
            is_staff=True,
        )
        self.criar_instituicao(
            'Pendente',
            status='pendente',
            base='223334440001',
        )
        _, ativa = self.criar_instituicao(
            'Ativa',
            status='ativa',
            base='334445550001',
        )
        self.criar_instituicao(
            'Rejeitada',
            status='rejeitada',
            base='445556660001',
        )
        self.criar_instituicao(
            'Inativa',
            status='inativa',
            base='556667770001',
        )
        self.client.force_login(admin)

        response = self.client.get(reverse('dashboard_admin_gerenciar'))

        self.assertEqual(response.status_code, 200)
        por_nome = {
            instituicao['nome']: instituicao['status_display']
            for instituicao in response.context['instituicoes']
        }
        self.assertEqual(
            por_nome,
            {
                'Pendente': 'Pendente',
                'Ativa': 'Ativo',
                'Rejeitada': 'Desativado',
                'Inativa': 'Desativado',
            },
        )
        dados_ativa = next(
            instituicao
            for instituicao in response.context['instituicoes']
            if instituicao['nome'] == 'Ativa'
        )
        self.assertEqual(
            dados_ativa['cnpj_formatado'],
            (
                f'{ativa.cnpj[:2]}.{ativa.cnpj[2:5]}.'
                f'{ativa.cnpj[5:8]}/{ativa.cnpj[8:12]}-{ativa.cnpj[12:]}'
            ),
        )
        self.assertContains(response, '<th scope="col">Instituição</th>')
        self.assertContains(response, '<th scope="col">CNPJ</th>')
        self.assertContains(response, '<th scope="col">Cidade</th>')
        self.assertContains(response, '<th scope="col">Status</th>')
        self.assertContains(response, '<th scope="col">Ações</th>'        )
        self.assertContains(response, 'São Paulo, SP')
        self.assertContains(response, 'data-status-filter="ativo"')
        self.assertContains(response, 'data-status-filter="desativado"')
        self.assertContains(response, 'data-quick-action="aprovar"')
        self.assertContains(response, 'data-quick-action="rejeitar"')
        self.assertContains(response, 'data-quick-action="inativar"')
        self.assertContains(response, 'data-quick-action="reativar"')

    def test_admin_moderation_returns_safe_json_for_async_actions(self):
        response = self.client.post(
            reverse('dashboard_admin_gerenciar'),
            {'instituicao_id': '1', 'acao': 'aprovar'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 302)

        usuario_comum = get_user_model().objects.create_user(
            username='usuario@example.org',
            email='usuario@example.org',
            password='ApoioOnco!2026',
        )
        self.client.force_login(usuario_comum)
        response = self.client.post(
            reverse('dashboard_admin_gerenciar'),
            {'instituicao_id': '1', 'acao': 'aprovar'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 403)

        admin = get_user_model().objects.create_user(
            username='moderadora@example.org',
            email='moderadora@example.org',
            password='ApoioOnco!2026',
            is_staff=True,
        )
        _, instituicao = self.criar_instituicao(
            'Aprovação assíncrona',
            status='pendente',
        )
        self.client.force_login(admin)

        response = self.client.post(
            reverse('dashboard_admin_gerenciar'),
            {'instituicao_id': instituicao.pk, 'acao': 'aprovar'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ativa')
        self.assertNotIn('password', response.json())
        instituicao.refresh_from_db()
        self.assertEqual(instituicao.status, 'ativa')

    def test_profile_and_contact_updates_change_only_logged_in_institution(
        self,
    ):
        _, instituicao = self.criar_instituicao(
            'Minha Instituicao'
        )
        _, outra = self.criar_instituicao(
            'Outra Instituicao',
            base='334445550001',
        )
        assistencia_social, _ = TipoApoio.objects.get_or_create(
            nome='Assistência social'
        )

        self.client.force_login(instituicao.usuario)

        perfil = {
            'nome': 'Nome Atualizado',
            'tipo': 'hospital',
            'descricao': 'Descrição atualizada.',
            'cep': '20000-000',
            'logradouro': 'Rua Nova',
            'bairro': 'Centro',
            'cidade': 'Rio de Janeiro',
            'estado': 'rj',
            'horario': 'Todos os dias',
            'servicos': [
                self.tipo_apoio.nome,
                assistencia_social.nome,
            ],
        }

        response = self.client.post(
            reverse('dashboard_instituicao_perfil'),
            perfil,
        )
        self.assertEqual(response.status_code, 302)

        instituicao.refresh_from_db()
        outra.refresh_from_db()

        self.assertEqual(
            instituicao.nomeInst,
            'Nome Atualizado',
        )
        self.assertEqual(
            instituicao.cidade,
            'Rio de Janeiro',
        )
        self.assertSetEqual(
            set(
                instituicao.servicosOferecidos.values_list(
                    'nome',
                    flat=True,
                )
            ),
            {
                self.tipo_apoio.nome,
                assistencia_social.nome,
            },
        )
        self.assertEqual(
            outra.nomeInst,
            'Outra Instituicao',
        )
        self.assertEqual(outra.cidade, 'São Paulo')

        contato = {
            'telefone': '',
            'whatsapp': '(21) 99999-0000',
            'email_atendimento': 'novo-contato@example.org',
            'site': '',
            'instagram': '@apoio',
            'facebook': '',
        }

        response = self.client.post(
            reverse('dashboard_instituicao_contato'),
            contato,
        )
        self.assertEqual(response.status_code, 302)

        instituicao.refresh_from_db()
        self.assertEqual(
            instituicao.telefone_whatsapp,
            contato['whatsapp'],
        )
        self.assertEqual(
            instituicao.email_contato,
            contato['email_atendimento'],
        )

    def test_profile_rejects_unknown_service_without_saving_other_fields(
        self,
    ):
        _, instituicao = self.criar_instituicao(
            'Minha Instituicao'
        )
        self.client.force_login(instituicao.usuario)

        perfil = {
            'nome': 'Nome não deve ser salvo',
            'tipo': 'hospital',
            'descricao': 'Descrição atualizada.',
            'cep': '20000-000',
            'logradouro': 'Rua Nova',
            'bairro': 'Centro',
            'cidade': 'Rio de Janeiro',
            'estado': 'rj',
            'horario': 'Todos os dias',
            'servicos': ['Serviço inexistente'],
        }

        response = self.client.post(
            reverse('dashboard_instituicao_perfil'),
            perfil,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'servicos',
            response.context['form'].errors,
        )

        instituicao.refresh_from_db()
        self.assertEqual(
            instituicao.nomeInst,
            'Minha Instituicao',
        )
        self.assertSetEqual(
            set(
                instituicao.servicosOferecidos.values_list(
                    'nome',
                    flat=True,
                )
            ),
            {self.tipo_apoio.nome},
        )

    def test_institution_settings_update_only_own_account_and_visibility(self):
        usuario, instituicao = self.criar_instituicao('Minha Instituicao')
        outro_usuario, outra = self.criar_instituicao(
            'Outra Instituicao',
            base='334445550001',
        )
        self.client.force_login(usuario)

        response = self.client.post(
            reverse('dashboard_instituicao_configuracoes'),
            {
                'acao': 'salvar_configuracoes',
                'nome': 'Minha Instituicao atualizada',
                'email': 'novo-email@example.org',
                'logo': self.imagem_png('nova-logo.png'),
            },
        )

        self.assertRedirects(
            response,
            reverse('dashboard_instituicao_configuracoes'),
        )
        usuario.refresh_from_db()
        instituicao.refresh_from_db()
        outra.refresh_from_db()
        outro_usuario.refresh_from_db()
        self.assertEqual(usuario.email, 'novo-email@example.org')
        self.assertEqual(usuario.username, 'novo-email@example.org')
        self.assertEqual(instituicao.nomeInst, 'Minha Instituicao atualizada')
        self.assertEqual(instituicao.email, 'novo-email@example.org')
        self.assertTrue(instituicao.logo.name.endswith('nova-logo.png'))
        self.assertEqual(instituicao.status, 'inativa')
        self.assertEqual(outra.email, outro_usuario.email)
        self.assertEqual(outra.status, 'ativa')

    def test_institution_password_change_keeps_session_and_deletion_checks_password(self):
        usuario, instituicao = self.criar_instituicao('Minha Instituicao')
        self.client.force_login(usuario)
        url = reverse('dashboard_instituicao_configuracoes')

        response = self.client.post(
            url,
            {
                'acao': 'alterar_senha',
                'senha_atual': 'ApoioOnco!2026',
                'nova_senha': 'NovaSenha!2026',
                'confirmar_senha': 'NovaSenha!2026',
            },
        )
        self.assertRedirects(response, url)
        usuario.refresh_from_db()
        self.assertTrue(usuario.check_password('NovaSenha!2026'))
        self.assertEqual(self.client.get(url).status_code, 200)

        response = self.client.post(
            url,
            {
                'acao': 'excluir_conta',
                'senha_atual': 'senha-incorreta',
                'confirmar_exclusao': 'on',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            get_user_model().objects.filter(pk=usuario.pk).exists()
        )

        response = self.client.post(
            url,
            {
                'acao': 'excluir_conta',
                'senha_atual': 'NovaSenha!2026',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            get_user_model().objects.filter(pk=usuario.pk).exists()
        )

        response = self.client.post(
            url,
            {
                'acao': 'excluir_conta',
                'senha_atual': 'NovaSenha!2026',
                'confirmar_exclusao': 'on',
            },
        )
        self.assertRedirects(response, reverse('home'))
        self.assertFalse(
            get_user_model().objects.filter(pk=usuario.pk).exists()
        )
        self.assertFalse(Instituicao.objects.filter(pk=instituicao.pk).exists())

    def test_admin_settings_create_and_delete_admin_users(self):
        admin = get_user_model().objects.create_user(
            username='admin@example.org',
            email='admin@example.org',
            password='ApoioOnco!2026',
            is_staff=True,
        )
        self.client.force_login(admin)
        url = reverse('dashboard_admin_configuracoes')

        response = self.client.post(
            url,
            {
                'acao': 'criar_administrador',
                'nome': 'Nova Admin',
                'email': 'nova-admin@example.org',
                'senha': 'curta',
                'confirmar_senha': 'curta',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nova Admin')
        self.assertIn('senha', response.context['form_administrador'].errors)

        response = self.client.post(
            url,
            {
                'acao': 'criar_administrador',
                'nome': 'Nova Admin',
                'email': 'nova-admin@example.org',
                'senha': 'senha-longa-para-teste-2026',
                'confirmar_senha': 'outra-senha-longa-2026',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'confirmar_senha',
            response.context['form_administrador'].errors,
        )
        self.assertFalse(
            get_user_model().objects.filter(
                email='nova-admin@example.org'
            ).exists()
        )

        response = self.client.post(
            url,
            {
                'acao': 'criar_administrador',
                'nome': 'Nova Admin',
                'email': 'nova-admin@example.org',
                'senha': 'NovaConta!2026',
                'confirmar_senha': 'NovaConta!2026',
            },
        )
        self.assertRedirects(response, url)
        nova_admin = get_user_model().objects.get(
            email='nova-admin@example.org'
        )
        self.assertTrue(nova_admin.is_staff)
        self.assertTrue(nova_admin.check_password('NovaConta!2026'))
        self.assertIsNotNone(
            authenticate(
                username='nova-admin@example.org',
                password='NovaConta!2026',
            )
        )

        response = self.client.get(url)
        self.assertNotContains(response, 'Editar administradora')
        self.assertNotContains(response, 'dialogo-editar-admin')

        response = self.client.post(
            url,
            {
                'acao': 'excluir_administrador',
                'administrador_id': nova_admin.pk,
            },
        )
        self.assertRedirects(response, url)
        self.assertFalse(
            get_user_model().objects.filter(pk=nova_admin.pk).exists()
        )
        self.assertTrue(get_user_model().objects.filter(pk=admin.pk).exists())

    def test_admin_deletion_cannot_remove_self_or_last_admin(self):
        admin = get_user_model().objects.create_user(
            username='principal@example.org',
            email='principal@example.org',
            password='ApoioOnco!2026',
            is_staff=True,
        )
        outro_admin = get_user_model().objects.create_user(
            username='outro@example.org',
            email='outro@example.org',
            password='ApoioOnco!2026',
            is_staff=True,
        )
        self.client.force_login(admin)
        url = reverse('dashboard_admin_configuracoes')

        response = self.client.post(
            url,
            {
                'acao': 'excluir_administrador',
                'administrador_id': admin.pk,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            get_user_model().objects.filter(pk=admin.pk).exists()
        )
        self.assertContains(response, 'Não é possível excluir sua própria conta')

        response = self.client.post(
            url,
            {
                'acao': 'excluir_administrador',
                'administrador_id': outro_admin.pk,
            },
        )
        self.assertRedirects(response, url)
        self.assertEqual(
            get_user_model().objects.filter(is_staff=True).count(),
            1,
        )

    def test_admin_settings_list_includes_superusers_without_exposing_credentials(self):
        admin = get_user_model().objects.create_superuser(
            username='super-admin@example.org',
            email='super-admin@example.org',
            password='ApoioOnco!2026',
            first_name='Admin Principal',
        )
        self.client.force_login(admin)

        response = self.client.get(
            reverse('dashboard_admin_configuracoes')
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admin Principal')
        self.assertContains(response, 'super-admin@example.org')
        self.assertContains(response, 'Cadastrada em')
        self.assertContains(response, 'Ativa')
        self.assertNotContains(response, admin.password)
        self.assertEqual(
            list(response.context['administradores']),
            [admin],
        )

    def test_admin_account_email_requires_valid_unique_address(self):
        admin = get_user_model().objects.create_user(
            username='conta-admin@example.org',
            email='conta-admin@example.org',
            password='ApoioOnco!2026',
            is_staff=True,
        )
        get_user_model().objects.create_user(
            username='outra-conta@example.org',
            email='outra-conta@example.org',
            password='ApoioOnco!2026',
        )
        self.client.force_login(admin)
        url = reverse('dashboard_admin_configuracoes')

        for invalid_email in ('invalido', 'outra-conta@example.org'):
            response = self.client.post(
                url,
                {'acao': 'salvar_conta', 'email': invalid_email},
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn('email', response.context['form_conta'].errors)
            self.assertContains(response, invalid_email)

        response = self.client.post(
            url,
            {'acao': 'salvar_conta', 'email': 'novo-admin@example.org'},
        )
        self.assertRedirects(response, url)
        admin.refresh_from_db()
        self.assertEqual(admin.email, 'novo-admin@example.org')
        self.assertEqual(admin.username, 'novo-admin@example.org')

    def test_admin_password_change_validates_and_keeps_authenticated_session(self):
        admin = get_user_model().objects.create_user(
            username='senha-admin@example.org',
            email='senha-admin@example.org',
            password='ApoioOnco!2026',
            is_staff=True,
        )
        self.client.force_login(admin)
        url = reverse('dashboard_admin_configuracoes')

        response = self.client.post(
            url,
            {
                'acao': 'alterar_senha',
                'senha_atual': 'senha-incorreta',
                'nova_senha': 'OutraSenha!2026',
                'confirmar_senha': 'OutraSenha!2026',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-reopen="true"')
        self.assertContains(response, 'A senha atual está incorreta.')
        self.assertNotContains(response, 'senha-incorreta')

        response = self.client.post(
            url,
            {
                'acao': 'alterar_senha',
                'senha_atual': 'ApoioOnco!2026',
                'nova_senha': 'SenhaNova!2026',
                'confirmar_senha': 'SenhaNova!2026',
            },
        )
        self.assertRedirects(response, url)
        admin.refresh_from_db()
        self.assertTrue(admin.check_password('SenhaNova!2026'))
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_admin_categories_support_create_read_update_delete_and_safe_errors(self):
        admin = get_user_model().objects.create_user(
            username='categorias@example.org',
            email='categorias@example.org',
            password='ApoioOnco!2026',
            is_staff=True,
        )
        self.client.force_login(admin)
        url = reverse('dashboard_admin_categoria')

        response = self.client.post(
            url,
            {'acao': 'criar_categoria', 'nome': ''},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

        response = self.client.post(
            url,
            {'acao': 'criar_categoria', 'nome': 'Novo apoio'},
        )
        self.assertRedirects(response, url)
        categoria = TipoApoio.objects.get(nome='Novo apoio')

        response = self.client.get(url)
        self.assertContains(response, 'Novo apoio')
        self.assertContains(response, 'dialogo-excluir-categoria')

        response = self.client.post(
            url,
            {
                'acao': 'editar_categoria',
                'categoria_id': categoria.pk,
                'nome': 'Apoio atualizado',
            },
        )
        self.assertRedirects(response, url)
        categoria.refresh_from_db()
        self.assertEqual(categoria.nome, 'Apoio atualizado')

        response = self.client.post(
            url,
            {'acao': 'excluir_categoria', 'categoria_id': categoria.pk},
        )
        self.assertRedirects(response, url)
        self.assertFalse(TipoApoio.objects.filter(pk=categoria.pk).exists())

    def test_configuration_pages_enforce_account_roles(self):
        usuario, instituicao = self.criar_instituicao('Minha Instituicao')
        admin = get_user_model().objects.create_user(
            username='admin@example.org',
            email='admin@example.org',
            password='ApoioOnco!2026',
            is_staff=True,
        )
        self.client.force_login(usuario)
        self.assertEqual(
            self.client.get(
                reverse('dashboard_admin_configuracoes')
            ).status_code,
            403,
        )
        self.client.force_login(admin)
        self.assertEqual(
            self.client.get(
                reverse('dashboard_instituicao_configuracoes')
            ).status_code,
            403,
        )
        self.assertNotEqual(instituicao.usuario_id, admin.pk)

    def test_public_search_shows_only_approved_institutions_and_filters(
        self,
    ):
        _, ativa = self.criar_instituicao(
            'Aprovada',
            status='ativa',
        )
        _, pendente = self.criar_instituicao(
            'Pendente',
            status='pendente',
            base='334445550001',
        )

        response = self.client.get(
            reverse('busca'),
            {
                'localizacao': 'São Paulo',
                'estado': 'SP',
                'tipo': 'ong_associacao',
                'servicos': 'banco_peruca',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, ativa.nomeInst)
        self.assertNotContains(response, pendente.nomeInst)

    def test_home_search_combines_filters_and_keeps_selections(self):
        _, matching = self.criar_instituicao(
            'Aprovada para apoio',
            status='ativa',
        )
        _, other_city = self.criar_instituicao(
            'Aprovada no Rio',
            status='ativa',
            base='334445550001',
        )
        other_city.cidade = 'Rio de Janeiro'
        other_city.save(update_fields=['cidade'])

        response = self.client.get(
            reverse('home'),
            {
                'busca': 'aprovada',
                'localizacao': 'sao paulo',
                'estado': 'SP',
                'tipo': 'ong_associacao',
                'servicos': str(self.tipo_apoio.pk),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context['instituicoes']),
            [matching],
        )
        self.assertTrue(response.context['tem_filtros'])
        self.assertEqual(response.context['busca'], 'aprovada')
        self.assertEqual(response.context['localizacao'], 'sao paulo')
        self.assertEqual(response.context['estado_selecionado'], 'SP')
        self.assertEqual(len(response.context['estados_brasil']), 27)
        self.assertEqual(
            response.context['servicos_selecionados'],
            [str(self.tipo_apoio.pk)],
        )
        self.assertContains(response, matching.nomeInst)
        self.assertNotContains(response, other_city.nomeInst)

    def test_home_search_opens_results_with_selected_filters(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'action="/filtro/"')
        self.assertContains(response, 'name="q"')
        self.assertContains(response, 'fa-location-dot filter-icon')
        self.assertContains(response, 'fa-hospital filter-icon')
        self.assertContains(response, 'fa-hand-holding-heart filter-icon')
        self.assertNotContains(response, 'Limpar filtros')

        response = self.client.get(
            reverse('filtro'),
            {
                'q': 'apoio',
                'estado': 'SP',
                'tipo': 'ong_associacao',
                'servicos': str(self.tipo_apoio.pk),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['busca'], 'apoio')
        self.assertEqual(response.context['estado_selecionado'], 'SP')
        self.assertEqual(
            response.context['tipo_selecionado'],
            'ong_associacao',
        )
        self.assertEqual(
            response.context['servicos_selecionados'],
            [str(self.tipo_apoio.pk)],
        )
        self.assertContains(response, 'name="q"')
        self.assertContains(response, 'value="apoio"')
        self.assertContains(response, 'value="SP" selected')
        self.assertContains(
            response,
            'value="ong_associacao" selected',
        )
        self.assertContains(
            response,
            f'value="{self.tipo_apoio.pk}" checked',
        )

    def test_admin_dashboard_filters_cities_with_partial_accentless_search(self):
        admin = get_user_model().objects.create_user(
            username='busca-admin@example.org',
            email='busca-admin@example.org',
            password='ApoioOnco!2026',
            is_staff=True,
        )
        self.client.force_login(admin)

        self.criar_instituicao('Instituição São Paulo')
        _, rio = self.criar_instituicao(
            'Instituição Rio',
            base='334445550001',
        )
        rio.cidade = 'Rio de Janeiro'
        rio.estado = 'RJ'
        rio.save(update_fields=['cidade', 'estado'])
        self.criar_instituicao(
            'Instituição Inativa São Paulo',
            status='inativa',
            base='445556660001',
        )
        self.criar_instituicao(
            'Instituição Pendente São Paulo',
            status='pendente',
            base='556667770001',
        )

        response = self.client.get(
            reverse('dashboard_admin'),
            {'cidade': 'sao'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context['dashboard_grafico']['cidades']),
            ['São Paulo'],
        )
        self.assertEqual(response.context['busca_cidade'], 'sao')
        self.assertContains(response, 'value="sao"')
        self.assertEqual(response.context['total_instituicoes'], 3)
        self.assertEqual(response.context['instituicoes_inativas'], 1)
        self.assertEqual(response.context['instituicoes_ativas'], 1)
        self.assertEqual(response.context['aguardando_aprovacao'], 1)
        total_por_tipo = dict(response.context['total_por_tipo'])
        self.assertEqual(total_por_tipo[self.tipo_apoio.nome], 1)
        self.assertEqual(sum(total_por_tipo.values()), 1)

        response = self.client.get(
            reverse('dashboard_admin'),
            {'cidade': 'cidade inexistente'},
        )
        self.assertEqual(response.context['dashboard_grafico']['cidades'], {})
        self.assertEqual(response.context['total_instituicoes'], 0)
        self.assertEqual(response.context['instituicoes_inativas'], 0)
        self.assertContains(response, 'Nenhum resultado encontrado.')
