
import json
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
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

    @patch('ongs.cnpj_api.consultar_dados_cnpj')
    def test_cnpj_api_checks_local_value_and_activity(self, consultar):
        request = RequestFactory().get('/')
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
            'descricao_situacao_cadastral': 'ATIVA'
        }
        dados = self.dados_cadastro()

        response = self.client.post(reverse('cadastro'), dados)

        self.assertEqual(response.status_code, 302)

        instituicao = Instituicao.objects.get(cnpj=dados['cnpj'])
        self.assertEqual(instituicao.status, 'pendente')
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
    def test_invalid_cnpj_is_rejected_without_external_lookup(
        self,
        consultar,
    ):
        dados = self.dados_cadastro()
        dados['cnpj'] = '00.000.000/0000-00'

        response = self.client.post(reverse('cadastro'), dados)

        self.assertEqual(response.status_code, 200)
        self.assertIn('cnpj', response.context['form'].errors)
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

        self.assertEqual(
            self.client.get(
                reverse('dashboard_admin')
            ).status_code,
            200,
        )
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
