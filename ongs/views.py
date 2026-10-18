from functools import wraps

import requests
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .cnpj_api import consultar_dados_cnpj
from .forms import (
    CadastroInstituicaoForm,
    ContatoInstituicaoForm,
    PerfilInstituicaoForm,
)
from .models import Instituicao, TipoApoio
from .validators import normalizar_cnpj


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


def _email_disponivel(email, usuario):
    if len(email) > 150:
        return False
    try:
        validate_email(email)
    except ValidationError:
        return False
    User = get_user_model()
    return not User.objects.filter(
        Q(username__iexact=email) | Q(email__iexact=email)
    ).exclude(pk=usuario.pk).exists()


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
    if request.method == 'POST' and form.is_valid():
        cnpj = form.cleaned_data['cnpj']
        try:
            dados_cnpj = consultar_dados_cnpj(cnpj)
        except requests.HTTPError as erro:
            if erro.response is not None and erro.response.status_code == 404:
                form.add_error('cnpj', 'CNPJ n├úo encontrado na base consultada.')
            elif erro.response is not None and erro.response.status_code == 400:
                form.add_error('cnpj', 'CNPJ rejeitado pela consulta cadastral.')
            else:
                form.add_error(None, 'N├úo foi poss├¡vel validar o CNPJ. Tente novamente.')
        except (requests.RequestException, ValueError):
            form.add_error(None, 'N├úo foi poss├¡vel validar o CNPJ. Tente novamente.')
        else:
            situacao = dados_cnpj.get('descricao_situacao_cadastral', '')
            if situacao.strip().upper() != 'ATIVA':
                form.add_error('cnpj', 'A institui├º├úo precisa estar ativa na Receita Federal.')
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
                    form.add_error(None, 'CNPJ ou e-mail j├í cadastrado. Confira os dados informados.')
                else:
                    messages.success(
                        request,
                        'Cadastro enviado. A institui├º├úo ficar├í dispon├¡vel ap├│s a aprova├º├úo administrativa.',
                    )
                    return redirect('login')

    return render(request, 'cadastro.html', {
        'form': form,
        'servicos_selecionados': request.POST.getlist('servicos'),
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
            'instagram': instituicao.instagram,
            'facebook': instituicao.facebook,
        })
    return render(request, 'dashboard-instituicao-contato.html', {
        'instituicao': instituicao,
        'form': form,
    })


@instituicao_required
def dashboard_instituicao_configuracoes_view(request):
    instituicao = request.instituicao
    if request.method == 'POST' and request.POST.get('acao') != 'excluir_conta':
        email = request.POST.get('email', '').strip().lower()
        User = get_user_model()
        if not _email_disponivel(email, request.user):
            messages.error(request, 'Informe um e-mail v├ílido e ainda n├úo utilizado.')
        else:
            request.user.email = email
            request.user.username = email
            instituicao.email = email
            if request.POST.get('visivel') and instituicao.status == 'inativa':
                instituicao.status = 'ativa'
            elif not request.POST.get('visivel') and instituicao.status == 'ativa':
                instituicao.status = 'inativa'
            try:
                with transaction.atomic():
                    request.user.save(update_fields=['email', 'username'])
                    instituicao.full_clean()
                    instituicao.save()
            except (IntegrityError, ValidationError):
                messages.error(request, 'N├úo foi poss├¡vel salvar as configura├º├Áes. Verifique o e-mail.')
            else:
                messages.success(request, 'Configura├º├Áes salvas com sucesso.')
                return redirect('dashboard_instituicao_configuracoes')
    return render(request, 'dashboard-instituicao-configuracoes.html', {
        'instituicao': instituicao,
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
            messages.success(request, 'Status da institui├º├úo atualizado.')
        return redirect('dashboard_admin_gerenciar')

    instituicoes = Instituicao.objects.all().order_by('nomeInst')
    busca = request.GET.get('busca', '').strip()
    status = request.GET.get('status', '')
    cidade = request.GET.get('cidade', '')
    if busca:
        instituicoes = instituicoes.filter(
            Q(nomeInst__icontains=busca)
            | Q(cnpj__icontains=busca)
            | Q(cidade__icontains=busca)
        )
    if status:
        instituicoes = instituicoes.filter(status=status)
    if cidade:
        instituicoes = instituicoes.filter(cidade__iexact=cidade)
    return render(request, 'dashboard-admin-gerenciar.html', {
        'instituicoes': instituicoes,
        'cidades': Instituicao.objects.order_by('cidade').values_list(
            'cidade', flat=True
        ).distinct(),
        'status_selecionado': status,
        'cidade_selecionada': cidade,
        'busca': busca,
    })


@administrador_required
def dashboard_admin_categoria_view(request):
    if request.method == 'POST':
        acao = request.POST.get('acao')
        nome = request.POST.get('nome', '').strip()
        if acao in {'criar_categoria', 'editar_categoria'} and (
            not nome or len(nome) > 100
        ):
            messages.error(request, 'Informe um nome de categoria com at├® 100 caracteres.')
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
        return redirect('dashboard_admin_categoria')

    return render(request, 'dashboard-admin-categoria.html', {
        'categorias': TipoApoio.objects.annotate(
            total_instituicoes=Count('instituicoes', distinct=True)
        ).order_by('nome'),
    })


@administrador_required
def dashboard_admin_configuracoes_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        User = get_user_model()
        if not _email_disponivel(email, request.user):
            messages.error(request, 'Informe um e-mail v├ílido e ainda n├úo utilizado.')
        else:
            request.user.email = email
            request.user.username = email
            try:
                request.user.save(update_fields=['email', 'username'])
            except IntegrityError:
                messages.error(request, 'Este e-mail j├í est├í associado a uma conta.')
            else:
                messages.success(request, 'E-mail administrativo atualizado.')
                return redirect('dashboard_admin_configuracoes')
    return render(request, 'dashboard-admin-configuracoes.html', {
        'administradores': get_user_model().objects.filter(is_staff=True).order_by('email'),
    })


def ver_instituicao_view(request, pk=None):
    if pk is None:
        pk = request.GET.get('id')
    instituicao = get_object_or_404(
        Instituicao.objects.filter(status='ativa').prefetch_related('servicosOferecidos'),
        pk=pk,
    )
    return render(request, 'ver-instituicao.html', {'instituicao': instituicao})
