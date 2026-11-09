from functools import wraps
from types import SimpleNamespace

import requests

from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.contrib.messages import get_messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.formats import date_format
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_POST

from .cnpj_api import (
    consultar_dados_cnpj,
    diagnosticar_falha_consulta_cnpj,
    validar_token_cnpj,
)
from .forms import (
    AdministradorForm,
    AlterarSenhaForm,
    CadastroInstituicaoForm,
    ContatoInstituicaoForm,
    ConfiguracoesInstituicaoForm,
    EmailAcessoForm,
    ExcluirContaForm,
    PerfilInstituicaoForm,
)
from .models import Instituicao, TipoApoio
from .validators import normalizar_cnpj

_TIPO_INSTITUICAO_LABELS = {
    'ong_associacao': _('ONG / associação'),
    'hospital': _('Hospital'),
    'clinica_centro_tratamento': _('Clínica / centro de tratamento'),
    'casa_apoio': _('Casa de apoio'),
    'instituto_fundacao': _('Instituto / fundação'),
    'voluntariado_grupo_apoio': _('Voluntariado / grupo de apoio'),
    'orgao_publico': _('Órgão público'),
    'outros': _('Outros'),
}
_STATUS_INSTITUICAO_LABELS = {
    'pendente': _('Pendente'),
    'ativa': _('Ativo'),
    'rejeitada': _('Desativado'),
    'inativa': _('Desativado'),
}


def _formatar_cnpj(cnpj):
    cnpj = normalizar_cnpj(cnpj)
    if len(cnpj) != 14:
        return cnpj
    return f'{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}'


def instituicao_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        instituicao = getattr(request.user, 'instituicao', None)
        if instituicao is None:
            raise PermissionDenied
        request.instituicao = instituicao
        return view(request, *args, **kwargs)

    return wrapped


def administrador_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapped


def _instituicoes_publicas(params):
    instituicoes = Instituicao.objects.filter(status='ativa').prefetch_related(
        'servicosOferecidos'
    )
    termo = (params.get('busca') or params.get('q') or '').strip()
    localizacao = (params.get('localizacao') or params.get('cidade') or '').strip()
    estado = params.get('estado', '').strip().upper()
    tipo = params.get('tipo', '').strip()
    servicos = params.getlist('servicos') if hasattr(params, 'getlist') else []
    nomes_servicos = {
        'banco_peruca': 'Banco de perucas',
        'banco_lenco': 'Banco de len├ºos',
        'apoio_psicologico': 'Apoio psicol├│gico',
        'assistencia_social': 'Assist├¬ncia social',
    }

    if termo:
        instituicoes = instituicoes.filter(
            Q(nomeInst__icontains=termo)
            | Q(cidade__icontains=termo)
            | Q(estado__icontains=termo)
            | Q(servicosOferecidos__nome__icontains=termo)
        )
    if localizacao:
        instituicoes = instituicoes.filter(
            Q(cidade__icontains=localizacao)
            | Q(estado__icontains=localizacao)
            | Q(cep__icontains=localizacao)
        )
    if estado:
        instituicoes = instituicoes.filter(estado__iexact=estado)
    if tipo:
        instituicoes = instituicoes.filter(tipo=tipo)
    if servicos:
        servicos_filtrados = [nomes_servicos.get(item, item) for item in servicos]
        instituicoes = instituicoes.filter(
            servicosOferecidos__nome__in=servicos_filtrados
        )

    return instituicoes.distinct().order_by('nomeInst')


def _contexto_busca(request):
    params = request.GET
    instituicoes = _instituicoes_publicas(params)
    localizacao = params.get('localizacao') or params.get('cidade', '')
    return {
        'instituicoes': instituicoes,
        'destaques': instituicoes[:3],
        'busca': params.get('busca') or params.get('q', ''),
        'localizacao': localizacao,
        'cidade': localizacao,
        'estado_selecionado': params.get('estado', ''),
        'tipo_selecionado': params.get('tipo', ''),
        'servicos_selecionados': params.getlist('servicos'),
    }


def home_view(request):
    context = _contexto_busca(request)
    return render(request, 'index.html', context)


def busca_view(request):
    return render(request, 'filtro.html', _contexto_busca(request))


def filtro_view(request):
    return render(request, 'filtro.html', _contexto_busca(request))


@administrador_required
def dashboard_view(request):
    context = {
        'total_instituicoes': Instituicao.objects.count(),
        'instituicoes_ativas': Instituicao.objects.filter(status='ativa').count(),
        'aguardando_aprovacao': Instituicao.objects.filter(status='pendente').count(),
    }
    return render(request, 'dashboard.html', context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_admin' if request.user.is_staff else 'dashboard_instituicao')

    erro = ''
    if request.method == 'POST':
        identificacao = request.POST.get('identificacao', '').strip()
        senha = request.POST.get('senha', '')
        user_model = get_user_model()
        usuario = None

        if '@' not in identificacao:
            instituicao = Instituicao.objects.filter(
                cnpj=normalizar_cnpj(identificacao)
            ).select_related('usuario').first()
            if instituicao:
                usuario = instituicao.usuario

        if usuario is None:
            usuario = user_model.objects.filter(
                Q(username__iexact=identificacao) | Q(email__iexact=identificacao)
            ).first()

        autenticado = None
        if usuario is not None:
            autenticado = authenticate(
                request,
                username=usuario.get_username(),
                password=senha,
            )

        if autenticado is not None:
            if not autenticado.is_staff and not hasattr(autenticado, 'instituicao'):
                erro = 'Esta conta n├úo est├í vinculada a uma institui├º├úo.'
            else:
                login(request, autenticado)
                destino = 'dashboard_admin' if autenticado.is_staff else 'dashboard_instituicao'
                return redirect(destino)
        else:
            erro = 'E-mail/CNPJ ou senha inv├ílidos.'

    return render(request, 'login.html', {'erro': erro})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('home')


def informacoes_view(request, tema):
    """Exibe conteúdo informativo específico para cada tema."""
    temas = {
        'entenda-o-cancer': {
            'titulo': 'Entenda o câncer',
            'resumo': 'Informação clara pode ajudar você a compreender melhor o diagnóstico e a conversar com a equipe de saúde.',
            'aviso': 'Cada diagnóstico e tratamento é único. Converse com profissionais de saúde para entender o que se aplica ao seu caso.',
            'secao_cartoes': 'Informações importantes',
            'cartoes': [
                {'titulo': 'Diferentes tipos', 'texto': 'Câncer é um conjunto de doenças, com características e cuidados que podem variar.', 'icone': 'fa-ribbon'},
                {'titulo': 'Diagnóstico', 'texto': 'Exames e avaliações ajudam a equipe a compreender cada situação.', 'icone': 'fa-magnifying-glass'},
                {'titulo': 'Tratamento individual', 'texto': 'O plano é definido com profissionais de saúde conforme cada caso.', 'icone': 'fa-user-doctor'},
            ],
            'ajuda_titulo': 'Como se preparar para conversar com a equipe',
            'ajuda_itens': [
                {'texto': 'Anote suas dúvidas antes das consultas.', 'icone': 'fa-clipboard-list'},
                {'texto': 'Peça que expliquem os exames e as opções de tratamento em linguagem simples.', 'icone': 'fa-comments'},
                {'texto': 'Leve alguém de confiança, se isso ajudar você.', 'icone': 'fa-user-group'},
            ],
            'cta_titulo': 'Precisa de apoio durante o tratamento?',
            'cta_texto': 'Encontre instituições e serviços de apoio perto de você.',
            'perguntas': [
                {'pergunta': 'O câncer é uma única doença?', 'resposta': 'Não. Câncer é o nome dado a um conjunto de doenças. O tipo e o comportamento podem variar, por isso as orientações devem ser individualizadas pela equipe de saúde.'},
                {'pergunta': 'Como posso entender melhor meu diagnóstico?', 'resposta': 'Peça à equipe que explique o diagnóstico, os exames e os próximos passos. Você pode anotar as dúvidas e solicitar que repitam ou esclareçam qualquer informação.'},
                {'pergunta': 'Posso mudar meu tratamento por conta própria?', 'resposta': 'Não interrompa nem altere o tratamento sem conversar com os profissionais responsáveis. Se tiver dúvidas ou efeitos que preocupem você, procure a equipe de saúde.'},
            ],
            'fontes': 'INCA e Ministério da Saúde.',
            'secoes': [
                {
                    'titulo': 'O que é câncer?',
                    'texto': 'Câncer é o nome dado a um conjunto de doenças em que algumas células passam a crescer de forma desordenada. Existem diferentes tipos, e cada um pode se comportar de uma maneira.',
                },
                {
                    'titulo': 'Diagnóstico e próximos passos',
                    'texto': 'Exames e avaliações ajudam a equipe de saúde a identificar o tipo da doença e a planejar o cuidado. É válido pedir explicações em linguagem simples, anotar dúvidas e levar alguém de confiança às consultas.',
                    'itens': [
                        'Pergunte quais exames foram feitos e o que os resultados significam.',
                        'Converse sobre os benefícios, possíveis efeitos e alternativas do tratamento.',
                        'Peça uma cópia dos documentos e anote os contatos da equipe responsável.',
                    ],
                },
                {
                    'titulo': 'Tratamento é individualizado',
                    'texto': 'As opções de tratamento dependem de diversos fatores clínicos e das necessidades de cada pessoa. A equipe assistencial pode explicar o plano proposto e orientar sobre como lidar com efeitos durante o cuidado.',
                },
                {
                    'titulo': 'Onde buscar informação confiável',
                    'texto': 'Prefira fontes oficiais de saúde e confirme informações encontradas na internet com profissionais que acompanham o tratamento. Evite iniciar, interromper ou alterar tratamentos por conta própria.',
                },
            ],
        },
        'saude-emocional': {
            'titulo': 'Saúde emocional',
            'resumo': 'Cuidar das emoções também faz parte da jornada. Você não precisa passar por tudo sem apoio.',
            'aviso': 'O apoio emocional não substitui o acompanhamento da equipe de saúde. Peça ajuda profissional quando sentir que precisa.',
            'secao_cartoes': 'Emoções comuns durante o tratamento',
            'cartoes': [
                {'titulo': 'Medo e ansiedade', 'texto': 'Muito comuns, principalmente antes de exames e resultados.', 'icone': 'fa-heart-pulse'},
                {'titulo': 'Tristeza', 'texto': 'Sentir-se para baixo em alguns dias pode fazer parte do processo.', 'icone': 'fa-cloud'},
                {'titulo': 'Cansaço emocional', 'texto': 'Respeitar seus limites também é cuidado.', 'icone': 'fa-battery-quarter'},
            ],
            'ajuda_titulo': 'Quando vale buscar ajuda profissional',
            'ajuda_itens': [
                {'texto': 'Tristeza ou angústia que não passam por muitos dias.', 'icone': 'fa-calendar-days'},
                {'texto': 'Dificuldade para dormir ou para realizar o dia a dia.', 'icone': 'fa-moon'},
                {'texto': 'Vontade de se isolar de quem você ama.', 'icone': 'fa-user-group'},
            ],
            'cta_titulo': 'Procurando apoio psicológico?',
            'cta_texto': 'Encontre instituições perto de você que oferecem esse atendimento.',
            'perguntas': [
                {'pergunta': 'É normal sentir medo durante o tratamento?', 'resposta': 'Sim. Muitas pessoas sentem medo e ansiedade nessa fase. Conversar com a equipe de saúde e com alguém de confiança pode ajudar. Se o sofrimento persistir, peça apoio profissional.'},
                {'pergunta': 'Como conversar com a família sobre o que estou sentindo?', 'resposta': 'Escolha um momento tranquilo e tente dizer com clareza do que precisa, como ser ouvida, receber ajuda em uma tarefa ou ter companhia. Você pode pedir apoio à equipe para iniciar essa conversa.'},
                {'pergunta': 'Preciso pagar para ter apoio psicológico?', 'resposta': 'As opções variam conforme a cidade e o serviço. Pergunte à equipe de saúde sobre atendimento disponível pelo SUS, serviços públicos, organizações sociais ou grupos de apoio.'},
            ],
            'fontes': 'INCA e Ministério da Saúde.',
            'secoes': [
                {
                    'titulo': 'Cada pessoa reage de um jeito',
                    'texto': 'Receber um diagnóstico ou atravessar um tratamento pode trazer sentimentos variados, como medo, tristeza, raiva, esperança ou cansaço. Não existe uma forma certa de sentir, e essas emoções não precisam ser enfrentadas em silêncio.',
                },
                {
                    'titulo': 'Peça apoio do seu jeito',
                    'texto': 'Compartilhar o que está sentindo com alguém de confiança pode ajudar. Você também pode conversar com a equipe de saúde sobre atendimento psicológico, serviço social ou grupos de apoio disponíveis na sua região.',
                    'itens': [
                        'Diga às pessoas próximas que tipo de ajuda seria útil para você.',
                        'Converse com a equipe sobre mudanças de humor, sono ou apetite que preocupem você.',
                        'Busque grupos de apoio acolhedores e respeitosos com a sua experiência.',
                    ],
                },
                {
                    'titulo': 'Pequenos cuidados no cotidiano',
                    'texto': 'Quando for possível e fizer sentido para você, reserve momentos para atividades que tragam conforto, mantenha contato com pessoas queridas e respeite seus limites. A equipe de saúde pode ajudar a adaptar essas atividades ao tratamento.',
                },
                {
                    'titulo': 'Quando procurar ajuda',
                    'texto': 'Se o sofrimento estiver intenso, persistente ou dificultando sua rotina, conte à equipe que acompanha você e peça orientação profissional. Buscar ajuda é parte do cuidado.',
                },
            ],
        },
        'autoestima-no-tratamento': {
            'titulo': 'Autoestima durante o tratamento',
            'resumo': 'Seu corpo pode passar por mudanças, mas a sua identidade e o seu valor vão muito além da aparência.',
            'aviso': 'Antes de usar produtos ou iniciar cuidados com pele, cabelo e unhas durante o tratamento, converse com a equipe de saúde.',
            'secao_cartoes': 'Cuidado e autoestima no seu ritmo',
            'cartoes': [
                {'titulo': 'Mudanças no corpo', 'texto': 'Cada pessoa vive as mudanças da aparência de uma forma diferente.', 'icone': 'fa-person'},
                {'titulo': 'Respeito aos limites', 'texto': 'Seu conforto e seu tempo são importantes durante o tratamento.', 'icone': 'fa-hand'},
                {'titulo': 'Autocuidado possível', 'texto': 'Pequenos gestos podem ajudar quando fizerem sentido para você.', 'icone': 'fa-spa'},
            ],
            'ajuda_titulo': 'Ideias de cuidado para conversar com a equipe',
            'ajuda_itens': [
                {'texto': 'Pergunte quais cuidados com pele e unhas são seguros para você.', 'icone': 'fa-comments'},
                {'texto': 'Experimente lenços, acessórios ou perucas apenas se tiver vontade.', 'icone': 'fa-heart'},
                {'texto': 'Compartilhe suas preocupações com alguém de confiança.', 'icone': 'fa-user-group'},
            ],
            'cta_titulo': 'Buscando apoio e acolhimento?',
            'cta_texto': 'Encontre serviços e instituições que podem apoiar você nessa fase.',
            'perguntas': [
                {'pergunta': 'É normal me sentir diferente com as mudanças no corpo?', 'resposta': 'Sim. Mudanças durante o tratamento podem mexer com a forma como você se vê. Não há uma maneira certa de se sentir; converse com alguém de confiança ou com a equipe de saúde.'},
                {'pergunta': 'Posso usar maquiagem, tintura ou produtos para a pele?', 'resposta': 'A segurança depende do tratamento e da sua situação. Antes de usar produtos ou fazer procedimentos, confirme com a equipe que acompanha você.'},
                {'pergunta': 'Onde posso encontrar perucas ou lenços?', 'resposta': 'Algumas instituições e bancos de perucas oferecem esses itens. Consulte os serviços disponíveis na sua região e escolha somente o que for confortável para você.'},
            ],
            'fontes': 'INCA e Ministério da Saúde.',
            'secoes': [
                {
                    'titulo': 'Mudanças no corpo e na imagem',
                    'texto': 'O tratamento pode trazer mudanças na aparência, na disposição e na relação com o próprio corpo. Cada pessoa vive isso de maneira diferente. Você pode acolher seus sentimentos sem se cobrar por estar bem o tempo todo.',
                },
                {
                    'titulo': 'Cuide de você com gentileza',
                    'texto': 'Autocuidado não precisa seguir um padrão. Escolha, no seu ritmo, o que faz você se sentir confortável e respeite os limites do seu corpo durante o tratamento.',
                    'itens': [
                        'Converse com a equipe sobre cuidados seguros para sua pele, cabelo e unhas.',
                        'Experimente lenços, acessórios ou perucas se tiver vontade — sem obrigação.',
                        'Peça ajuda para adaptar roupas e atividades ao seu conforto.',
                    ],
                },
                {
                    'titulo': 'Respeite o que você sente',
                    'texto': 'É possível sentir saudade de como era antes e, ao mesmo tempo, descobrir novas formas de se reconhecer. Falar sobre essas mudanças com alguém de confiança ou com um profissional pode ajudar.',
                },
                {
                    'titulo': 'Apoio prático e acolhedor',
                    'texto': 'Bancos de perucas, grupos de apoio e serviços de acolhimento podem oferecer alternativas e troca de experiências. Procure opções confiáveis e escolha apenas o que fizer sentido para você.',
                },
            ],
        },
    }
    conteudo = temas.get(tema)
    if conteudo is None:
        raise Http404('Tema informativo não encontrado.')

    outros_temas = [
        {'slug': slug, 'titulo': dados['titulo']}
        for slug, dados in temas.items()
        if slug != tema
    ]
    return render(
        request,
        'informacoes-para-voce.html',
        {'tema': conteudo, 'outros_temas': outros_temas},
    )

def cadastro_view(request):
    form = CadastroInstituicaoForm(request.POST or None, request.FILES or None)
    cnpj_retry_after = None
    if request.method == 'POST' and form.is_valid():
        cnpj = form.cleaned_data['cnpj']
        dados_cnpj = validar_token_cnpj(
            request,
            request.POST.get('token_validacao_cnpj'),
            cnpj,
        )
        if dados_cnpj is None:
            try:
                dados_cnpj = consultar_dados_cnpj(cnpj)
            except (requests.RequestException, ValueError, TypeError) as erro:
                _, _, mensagem, cnpj_retry_after = (
                    diagnosticar_falha_consulta_cnpj(erro)
                )
                form.add_error('cnpj', mensagem)

        if dados_cnpj is not None and not form.errors:
            situacao = dados_cnpj.get('descricao_situacao_cadastral', '')
            if situacao.strip().upper() != 'ATIVA':
                form.add_error(
                    'cnpj',
                    'Este CNPJ não possui situação cadastral ativa.',
                )
            else:
                User = get_user_model()
                dados = form.cleaned_data
                try:
                    with transaction.atomic():
                        usuario = User.objects.create_user(
                            username=dados['email'],
                            email=dados['email'],
                            password=dados['senha'],
                        )
                        instituicao = Instituicao.objects.create(
                            cnpj=cnpj,
                            razao_social=dados_cnpj.get('razao_social') or '',
                            nome_fantasia=dados_cnpj.get('nome_fantasia') or '',
                            nomeInst=dados['nome'],
                            tipo=dados['tipo'],
                            descricao=dados['descricao'],
                            conteudoInformativo='',
                            logo=dados['imagem_instituicao'],
                            telefone=dados['telefone'],
                            telefone_whatsapp=dados['whatsapp'],
                            email=usuario.email,
                            email_contato=dados['email_contato'],
                            site=dados['site'],
                            logradouro=dados['endereco'],
                            numero=dados['numero'],
                            complemento=dados['complemento'],
                            cep=dados['cep'],
                            bairro=dados['bairro'],
                            cidade=dados['cidade'],
                            estado=dados['estado'],
                            horarioAtendimento=dados['horario'],
                            redes_sociais=dados['redes'],
                            status='pendente',
                            usuario=usuario,
                        )
                        instituicao.servicosOferecidos.set(dados['servicos'])
                except IntegrityError:
                    if Instituicao.cnpj_ja_cadastrado(cnpj):
                        form.add_error(
                            'cnpj',
                            'Este CNPJ já está cadastrado na plataforma.',
                        )
                    else:
                        form.add_error(
                            None,
                            'CNPJ ou e-mail já cadastrado. Confira os dados informados.',
                        )
                else:
                    messages.success(
                        request,
                        'Cadastro enviado. A institui├º├úo ficar├í dispon├¡vel ap├│s a aprova├º├úo administrativa.',
                    )
                    return redirect('cadastro_sucesso')

    return render(request, 'cadastro.html', {
        'form': form,
        'servicos_selecionados': request.POST.getlist('servicos'),
        'cnpj_retry_after': cnpj_retry_after,
    })


@require_GET
def cadastro_sucesso_view(request):
    form = CadastroInstituicaoForm()
    form.fields['servicos'].queryset = TipoApoio.objects.none()
    return render(request, 'cadastro.html', {
        'form': form,
        'servicos_selecionados': [],
        'cadastro_enviado': True,
    })


@instituicao_required
def dashboard_instituicao_view(request):
    instituicao = request.instituicao
    return render(request, 'dashboard-instituicao.html', {
        'instituicao': instituicao,
        'total_servicos': instituicao.servicosOferecidos.count(),
    })


@instituicao_required
def dashboard_instituicao_perfil_view(request):
    instituicao = request.instituicao
    if request.method == 'POST':
        form = PerfilInstituicaoForm(request.POST, request.FILES)
        if form.is_valid():
            dados = form.cleaned_data
            instituicao.nomeInst = dados['nome']
            instituicao.tipo = dados['tipo']
            instituicao.descricao = dados['descricao']
            instituicao.cep = dados['cep']
            instituicao.logradouro = dados['logradouro']
            instituicao.numero = dados['numero']
            instituicao.complemento = dados['complemento']
            instituicao.bairro = dados['bairro']
            instituicao.cidade = dados['cidade']
            instituicao.estado = dados['estado']
            instituicao.horarioAtendimento = dados['horario']
            if dados.get('logo'):
                instituicao.logo = dados['logo']
            try:
                with transaction.atomic():
                    instituicao.full_clean()
                    instituicao.save()
                    instituicao.servicosOferecidos.set(dados['servicos'])
            except ValidationError as erro:
                form.add_error(None, erro.messages)
            else:
                messages.success(request, 'Perfil atualizado com sucesso.')
                return redirect('dashboard_instituicao_perfil')
        else:
            messages.error(request, 'Revise os campos destacados e tente novamente.')
    else:
        form = PerfilInstituicaoForm(initial={
            'nome': instituicao.nomeInst,
            'tipo': instituicao.tipo,
            'descricao': instituicao.descricao,
            'cep': instituicao.cep,
            'logradouro': instituicao.logradouro,
            'numero': instituicao.numero,
            'complemento': instituicao.complemento,
            'bairro': instituicao.bairro,
            'cidade': instituicao.cidade,
            'estado': instituicao.estado,
            'horario': instituicao.horarioAtendimento,
            'servicos': instituicao.servicosOferecidos.values_list('nome', flat=True),
        })
    return render(request, 'dashboard-instituicao-perfil.html', {
        'instituicao': instituicao,
        'form': form,
        'tipos_apoio': TipoApoio.objects.filter(ativo=True),
        'servicos_selecionados': (
            form['servicos'].value()
            if request.method == 'POST'
            else list(instituicao.servicosOferecidos.values_list('nome', flat=True))
        ),
    })


@instituicao_required
def dashboard_instituicao_contato_view(request):
    instituicao = request.instituicao
    if request.method == 'POST':
        form = ContatoInstituicaoForm(request.POST)
        if form.is_valid():
            dados = form.cleaned_data
            instituicao.telefone = dados['telefone']
            instituicao.telefone_whatsapp = dados['whatsapp']
            instituicao.email_contato = dados['email_atendimento']
            instituicao.site = dados['site']
            instituicao.redes_sociais = dados['redes']
            instituicao.instagram = dados['instagram']
            instituicao.facebook = dados['facebook']
            try:
                instituicao.full_clean()
                instituicao.save()
            except ValidationError as erro:
                form.add_error(None, erro)
            else:
                messages.success(request, 'Dados de contato atualizados com sucesso.')
                return redirect('dashboard_instituicao_contato')
        else:
            messages.error(request, 'Revise os dados de contato e tente novamente.')
    else:
        form = ContatoInstituicaoForm(initial={
            'telefone': instituicao.telefone,
            'whatsapp': instituicao.telefone_whatsapp,
            'email_atendimento': instituicao.email_contato,
            'site': instituicao.site,
            'redes': instituicao.redes_sociais,
            'instagram': instituicao.instagram,
            'facebook': instituicao.facebook,
        })
    return render(request, 'dashboard-instituicao-contato.html', {
        'instituicao': instituicao,
        'form': form,
    })


@login_required
@instituicao_required
def dashboard_instituicao_configuracoes_view(request):
    instituicao = request.instituicao
    configuracoes_form = ConfiguracoesInstituicaoForm(
        user=request.user,
        instituicao=instituicao,
        initial={
            'nome': instituicao.nomeInst,
            'email': request.user.email,
            'visivel': instituicao.status == 'ativa',
        },
    )
    senha_form = AlterarSenhaForm(user=request.user)
    exclusao_form = ExcluirContaForm(user=request.user)

    if request.method == 'POST':
        acao = request.POST.get('acao')
        if acao == 'salvar_configuracoes':
            configuracoes_form = ConfiguracoesInstituicaoForm(
                request.POST,
                request.FILES,
                user=request.user,
                instituicao=instituicao,
            )
            if configuracoes_form.is_valid():
                email = configuracoes_form.cleaned_data['email']
                try:
                    with transaction.atomic():
                        request.user.email = email
                        request.user.username = email
                        request.user.save(update_fields=['email', 'username'])
                        instituicao.nomeInst = configuracoes_form.cleaned_data['nome']
                        instituicao.email = email
                        if configuracoes_form.cleaned_data.get('logo'):
                            instituicao.logo = configuracoes_form.cleaned_data['logo']
                        if instituicao.status in {'ativa', 'inativa'}:
                            instituicao.status = (
                                'ativa'
                                if configuracoes_form.cleaned_data['visivel']
                                else 'inativa'
                            )
                        instituicao.full_clean()
                        instituicao.save()
                except IntegrityError:
                    configuracoes_form.add_error(
                        'email',
                        _('Não foi possível salvar. Verifique se o e-mail está disponível.'),
                    )
                    messages.error(request, _('Revise os campos destacados.'))
                except ValidationError as error:
                    configuracoes_form.add_error(None, error.messages)
                    messages.error(request, _('Revise os campos destacados.'))
                else:
                    messages.success(request, _('Configurações salvas com sucesso.'))
                    return redirect('dashboard_instituicao_configuracoes')
            else:
                messages.error(request, _('Revise os campos destacados e tente novamente.'))
        elif acao == 'alterar_senha':
            senha_form = AlterarSenhaForm(request.POST, user=request.user)
            if senha_form.is_valid():
                request.user.set_password(senha_form.cleaned_data['nova_senha'])
                request.user.save(update_fields=['password'])
                update_session_auth_hash(request, request.user)
                messages.success(request, _('Senha alterada com sucesso.'))
                return redirect('dashboard_instituicao_configuracoes')
            messages.error(request, _('Não foi possível alterar a senha. Confira os dados informados.'))
        elif acao == 'excluir_conta':
            exclusao_form = ExcluirContaForm(request.POST, user=request.user)
            if exclusao_form.is_valid():
                request.user.delete()
                logout(request)
                messages.success(request, _('A conta da instituição foi excluída.'))
                return redirect('home')
            messages.error(request, _('Confirme a senha e a exclusão para continuar.'))
        else:
            messages.error(request, _('Ação inválida.'))

    return render(request, 'dashboard-instituicao-configuracoes.html', {
        'instituicao': instituicao,
        'configuracoes_form': configuracoes_form,
        'senha_form': senha_form,
        'exclusao_form': exclusao_form,
    })


@administrador_required
def dashboard_admin_view(request):
    cidades = Instituicao.objects.filter(status='ativa').values_list(
        'cidade', flat=True
    ).distinct()
    dados_dashboard = {}
    tipos = list(TipoApoio.objects.filter(ativo=True).order_by('nome'))
    for cidade in cidades:
        dados_dashboard[cidade] = [
            Instituicao.objects.filter(
                status='ativa', cidade=cidade, servicosOferecidos=tipo
            ).distinct().count()
            for tipo in tipos
        ]
    return render(request, 'dashboard-admin.html', {
        'total_instituicoes': Instituicao.objects.count(),
        'instituicoes_inativas': Instituicao.objects.filter(status='inativa').count(),
        'instituicoes_ativas': Instituicao.objects.filter(status='ativa').count(),
        'aguardando_aprovacao': Instituicao.objects.filter(status='pendente').count(),
        'tipos_apoio': tipos,
        'dashboard_grafico': {
            'tipos': [tipo.nome for tipo in tipos],
            'cidades': dados_dashboard,
        },
        'total_por_tipo': [
            (tipo.nome, tipo.instituicoes.filter(status='ativa').distinct().count())
            for tipo in tipos
        ],
    })


@login_required
@administrador_required
def dashboard_admin_gerenciar_view(request):
    if request.method == 'POST':
        instituicao = get_object_or_404(Instituicao, pk=request.POST.get('instituicao_id'))
        acao = request.POST.get('acao')
        status_por_acao = {
            'aprovar': 'ativa',
            'rejeitar': 'rejeitada',
            'inativar': 'inativa',
            'reativar': 'ativa',
        }
        if acao in status_por_acao:
            instituicao.status = status_por_acao[acao]
            instituicao.motivo_rejeicao = (
                request.POST.get('motivo_rejeicao', '').strip()
                if acao == 'rejeitar' else ''
            )
            instituicao.avaliado_por = request.user
            instituicao.avaliado_em = timezone.now()
            instituicao.save(update_fields=[
                'status', 'motivo_rejeicao', 'avaliado_por', 'avaliado_em', 'atualizado_em'
            ])
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'ok': True,
                    'id': instituicao.pk,
                    'status': instituicao.status,
                    'status_display': _STATUS_INSTITUICAO_LABELS[instituicao.status],
                    'motivo_rejeicao': instituicao.motivo_rejeicao,
                    'avaliado_em': date_format(
                        timezone.localtime(instituicao.avaliado_em),
                        'DATETIME_FORMAT',
                    ),
                    'atualizado_em': date_format(
                        timezone.localtime(instituicao.atualizado_em),
                        'DATETIME_FORMAT',
                    ),
                })
            messages.success(request, 'Status da institui├º├úo atualizado.')
        elif request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(
                {'ok': False, 'error': _('Ação inválida.')},
                status=400,
            )
        return redirect('dashboard_admin_gerenciar')

    registros = list(
        Instituicao.objects.prefetch_related('servicosOferecidos')
        .order_by('nomeInst')
    )
    emails_acesso = dict(
        Instituicao.objects.values_list('pk', 'usuario__email')
    )
    instituicoes = []
    for instituicao in registros:
        instituicoes.append({
            'id': instituicao.pk,
            'cnpj': instituicao.cnpj or '',
            'cnpj_formatado': _formatar_cnpj(instituicao.cnpj or ''),
            'razao_social': instituicao.razao_social,
            'nome_fantasia': instituicao.nome_fantasia,
            'nome': instituicao.nomeInst,
            'tipo': instituicao.tipo,
            'tipo_display': _TIPO_INSTITUICAO_LABELS.get(
                instituicao.tipo,
                instituicao.tipo,
            ),
            'descricao': instituicao.descricao,
            'conteudo_informativo': instituicao.conteudoInformativo,
            'logo_url': instituicao.logo.url if instituicao.logo else '',
            'horario': instituicao.horarioAtendimento,
            'servicos': [
                servico.nome
                for servico in instituicao.servicosOferecidos.all()
            ],
            'cep': instituicao.cep,
            'logradouro': instituicao.logradouro,
            'numero': instituicao.numero,
            'complemento': instituicao.complemento,
            'bairro': instituicao.bairro,
            'cidade': instituicao.cidade,
            'estado': instituicao.estado,
            'telefone': instituicao.telefone,
            'whatsapp': instituicao.telefone_whatsapp,
            'email_contato': instituicao.email_contato,
            'site': instituicao.site,
            'redes_sociais': instituicao.redes_sociais,
            'instagram': instituicao.instagram,
            'facebook': instituicao.facebook,
            'email_acesso': emails_acesso.get(instituicao.pk) or '',
            'status': instituicao.status,
            'status_display': _STATUS_INSTITUICAO_LABELS[instituicao.status],
            'motivo_rejeicao': instituicao.motivo_rejeicao,
            'criado_em': (
                date_format(
                    timezone.localtime(instituicao.criado_em),
                    'DATETIME_FORMAT',
                )
                if instituicao.criado_em else ''
            ),
            'avaliado_em': (
                date_format(
                    timezone.localtime(instituicao.avaliado_em),
                    'DATETIME_FORMAT',
                )
                if instituicao.avaliado_em else ''
            ),
            'atualizado_em': (
                date_format(
                    timezone.localtime(instituicao.atualizado_em),
                    'DATETIME_FORMAT',
                )
                if instituicao.atualizado_em else ''
            ),
        })

    request_path = request.get_full_path()
    template_context = {
        'instituicoes': instituicoes,
        'tipos_instituicao': [
            {
                'valor': valor,
                'rotulo': _TIPO_INSTITUICAO_LABELS.get(valor, _(rotulo)),
            }
            for valor, rotulo in Instituicao.TIPO_CHOICES
        ],
        'estados': sorted({
            instituicao['estado']
            for instituicao in instituicoes
            if instituicao['estado']
        }),
        'csrf_token': get_token(request),
        'messages': list(get_messages(request)),
        'request': SimpleNamespace(
            get_full_path=lambda: request_path,
        ),
    }
    return HttpResponse(render_to_string(
        'dashboard-admin-gerenciar.html',
        template_context,
    ))


@login_required
@administrador_required
def dashboard_admin_categoria_view(request):
    if request.method == 'POST':
        acao = request.POST.get('acao')
        nome = request.POST.get('nome', '').strip()
        erro_formulario = False
        if acao in {'criar_categoria', 'editar_categoria'} and (
            not nome or len(nome) > 100
        ):
            messages.error(request, 'Informe um nome de categoria com at├® 100 caracteres.')
            erro_formulario = True
        elif acao == 'criar_categoria':
            categoria, criada = TipoApoio.objects.get_or_create(nome=nome)
            messages.success(
                request,
                'Categoria criada.' if criada else 'Esta categoria j├í estava cadastrada.',
            )
        elif acao == 'editar_categoria':
            categoria = get_object_or_404(TipoApoio, pk=request.POST.get('categoria_id'))
            categoria.nome = nome
            try:
                categoria.save(update_fields=['nome'])
            except IntegrityError:
                messages.error(request, 'J├í existe uma categoria com esse nome.')
                erro_formulario = True
            else:
                messages.success(request, 'Categoria atualizada.')
        elif acao == 'alternar_categoria':
            categoria = get_object_or_404(TipoApoio, pk=request.POST.get('categoria_id'))
            categoria.ativo = not categoria.ativo
            categoria.save(update_fields=['ativo'])
            messages.success(request, 'Visibilidade da categoria atualizada.')
        elif acao == 'excluir_categoria':
            categoria = get_object_or_404(TipoApoio, pk=request.POST.get('categoria_id'))
            if categoria.instituicoes.exists():
                messages.error(request, 'Esta categoria est├í vinculada a institui├º├Áes e n├úo pode ser exclu├¡da.')
            else:
                categoria.delete()
                messages.success(request, 'Categoria exclu├¡da.')
        if erro_formulario:
            return render(request, 'dashboard-admin-categoria.html', {
                'categorias': TipoApoio.objects.annotate(
                    total_instituicoes=Count('instituicoes', distinct=True)
                ).order_by('nome'),
                'categoria_nome': nome if acao == 'criar_categoria' else '',
                'categoria_edicao_id': (
                    request.POST.get('categoria_id')
                    if acao == 'editar_categoria'
                    else ''
                ),
                'categoria_edicao_nome': (
                    nome if acao == 'editar_categoria' else ''
                ),
            })
        return redirect('dashboard_admin_categoria')

    return render(request, 'dashboard-admin-categoria.html', {
        'categorias': TipoApoio.objects.annotate(
            total_instituicoes=Count('instituicoes', distinct=True)
        ).order_by('nome'),
    })


@login_required
@administrador_required
def dashboard_admin_configuracoes_view(request):
    User = get_user_model()
    form_conta = EmailAcessoForm(
        user=request.user,
        initial={'email': request.user.email},
    )
    form_administrador = AdministradorForm()
    senha_form = AlterarSenhaForm(user=request.user)

    if request.method == 'POST':
        acao = request.POST.get('acao')
        if acao == 'salvar_conta':
            form_conta = EmailAcessoForm(request.POST, user=request.user)
            if form_conta.is_valid():
                email = form_conta.cleaned_data['email']
                request.user.email = email
                request.user.username = email
                try:
                    request.user.save(update_fields=['email', 'username'])
                except IntegrityError:
                    form_conta.add_error(
                        'email',
                        _('Este e-mail já está associado a uma conta.'),
                    )
                    messages.error(request, _('Revise os campos destacados.'))
                else:
                    messages.success(request, _('E-mail administrativo atualizado.'))
                    return redirect('dashboard_admin_configuracoes')
            else:
                messages.error(request, _('Informe um e-mail válido e ainda não utilizado.'))
        elif acao == 'alterar_senha':
            senha_form = AlterarSenhaForm(request.POST, user=request.user)
            if senha_form.is_valid():
                request.user.set_password(senha_form.cleaned_data['nova_senha'])
                request.user.save(update_fields=['password'])
                update_session_auth_hash(request, request.user)
                messages.success(request, _('Senha alterada com sucesso.'))
                return redirect('dashboard_admin_configuracoes')
            messages.error(request, _('Não foi possível alterar a senha. Confira os dados informados.'))
        elif acao == 'criar_administrador':
            form_administrador = AdministradorForm(request.POST)
            if form_administrador.is_valid():
                dados = form_administrador.cleaned_data
                try:
                    nova_administradora = User(
                        username=dados['email'],
                        email=dados['email'],
                        first_name=dados['nome'],
                        is_staff=True,
                    )
                    nova_administradora.set_password(dados['senha'])
                    nova_administradora.save()
                except IntegrityError:
                    form_administrador.add_error(
                        'email',
                        _('Este e-mail já está associado a uma conta.'),
                    )
                    messages.error(request, _('Revise os campos destacados.'))
                else:
                    messages.success(request, _('Administradora criada com sucesso.'))
                    return redirect('dashboard_admin_configuracoes')
            else:
                messages.error(request, _('Revise os campos destacados e tente novamente.'))
        elif acao == 'excluir_administrador':
            alvo = get_object_or_404(
                User.objects.filter(is_staff=True),
                pk=request.POST.get('administrador_id'),
            )
            if alvo.pk == request.user.pk:
                messages.error(request, _('Não é possível excluir sua própria conta nesta tela.'))
            else:
                with transaction.atomic():
                    administradores_bloqueados = list(
                        User.objects.select_for_update()
                        .filter(is_staff=True)
                        .order_by('pk')
                    )
                    alvo_bloqueado = next(
                        (
                            administrador
                            for administrador in administradores_bloqueados
                            if administrador.pk == alvo.pk
                        ),
                        None,
                    )
                    if alvo_bloqueado is None:
                        messages.error(request, _('Esta administradora não está mais disponível.'))
                    elif len(administradores_bloqueados) <= 1:
                        messages.error(request, _('Não é possível excluir a última administradora.'))
                    else:
                        alvo_bloqueado.delete()
                        messages.success(request, _('Administradora excluída com sucesso.'))
                        return redirect('dashboard_admin_configuracoes')
        else:
            messages.error(request, _('Ação inválida.'))

    return render(request, 'dashboard-admin-configuracoes.html', {
        'administradores': User.objects.filter(
            is_staff=True,
        ).only(
            'pk',
            'email',
            'username',
            'first_name',
            'last_name',
            'date_joined',
            'is_active',
        ).order_by('email'),
        'form_conta': form_conta,
        'form_administrador': form_administrador,
        'senha_form': senha_form,
    })


def ver_instituicao_view(request, pk=None):
    if pk is None:
        pk = request.GET.get('id')
    instituicao = get_object_or_404(
        Instituicao.objects.filter(status='ativa').prefetch_related('servicosOferecidos'),
        pk=pk,
    )
    return render(request, 'ver-instituicao.html', {'instituicao': instituicao})

def esqueci_senha_view(request):
    return render(request, 'esqueci-senha.html')

def redefinir_senha_view(request):
    return render(request, 'redefinir-senha.html')