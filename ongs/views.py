from django.shortcuts import render
from django.db.models import Q
from .models import Instituicao

def home_view(request):
    busca = request.GET.get('busca', '').strip()
    cidade = request.GET.get('cidade', '').strip()
    
    # Inicia buscando apenas as instituições ativas
    instituicoes = Instituicao.objects.filter(status='Ativa')
    
    # Filtra por nome, cidade ou estado se o campo busca for preenchido
    if busca:
        instituicoes = instituicoes.filter(
            Q(nomeInst__icontains=busca) | 
            Q(cidade__icontains=busca) | 
            Q(estado__icontains=busca)
        )
        
    # Filtra especificamente por cidade se o campo cidade for preenchido
    if cidade:
        instituicoes = instituicoes.filter(cidade__icontains=cidade)
        
    context = {
        'instituicoes': instituicoes,
        'busca': busca,
        'cidade': cidade,
    }
    return render(request, 'index.html', context)


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

def cadastro_view(request):
    return render(request, 'cadastro.html')