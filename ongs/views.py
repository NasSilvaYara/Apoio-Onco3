from django.shortcuts import render
from django.http import Http404
from django.db.models import Q
from .models import Instituicao

def home_view(request):
    """View para a página inicial"""
    return render(request, 'index.html')

def busca_view(request):
    """View para a página/tela de busca e filtros"""
    busca = request.GET.get('busca', '').strip()
    cidade = request.GET.get('cidade', '').strip()
    
    instituicoes = Instituicao.objects.all()
    
    if busca:
        instituicoes = instituicoes.filter(
            Q(nomeInst__icontains=busca) | 
            Q(cidade__icontains=busca) | 
            Q(estado__icontains=busca)
        )
        
    if cidade:
        instituicoes = instituicoes.filter(cidade__icontains=cidade)
        
    context = {
        'instituicoes': instituicoes,
        'busca': busca,
        'cidade': cidade,
    }
    return render(request, 'busca.html', context)

# Mantenha suas outras views aqui embaixo (login_view, cadastro_view, etc.)


def dashboard_view(request):
    total_instituicoes = Instituicao.objects.count()
    instituicoes_ativas = Instituicao.objects.filter(status='Ativa').count()
    aguardando_aprovacao = Instituicao.objects.filter(status='Pendente').count()
    
    context = {
        'total_instituicoes': total_instituicoes,
        'instituicoes_ativas': instituicoes_ativas,
        'aguardando_aprovacao': aguardando_aprovacao,
    }
    return render(request, 'dashboard.html', context)

def login_view(request):
    return render(request, 'login.html')

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
    return render(request, 'cadastro.html')

def dashboard_instituicao_view(request):
    return render(request, 'dashboard-instituicao.html')

def dashboard_instituicao_perfil_view(request):
    return render(request, 'dashboard-instituicao-perfil.html')

def dashboard_instituicao_contato_view(request):
    return render(request, 'dashboard-instituicao-contato.html')

def dashboard_instituicao_configuracoes_view(request):
    return render(request, 'dashboard-instituicao-configuracoes.html')

def dashboard_admin_view(request):
    return render(request, 'dashboard-admin.html')

def dashboard_admin_gerenciar_view(request):
    return render(request, 'dashboard-admin-gerenciar.html')

def dashboard_admin_categoria_view(request):
    return render(request, 'dashboard-admin-categoria.html')

def dashboard_admin_configuracoes_view(request):
    return render(request, 'dashboard-admin-configuracoes.html')

def filtro_view(request):
    return render(request, 'filtro.html')

def ver_instituicao_view(request):
    return render(request, 'ver-instituicao.html')