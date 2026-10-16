from django.contrib import admin
from django.urls import path

from ongs.views import (
    home_view,
    busca_view,
    login_view,
    cadastro_view,
    dashboard_view,
    dashboard_instituicao_view,
    dashboard_instituicao_perfil_view,
    dashboard_instituicao_contato_view,
    dashboard_instituicao_configuracoes_view,
    dashboard_admin_view,
    dashboard_admin_gerenciar_view,
    dashboard_admin_categoria_view,
    dashboard_admin_configuracoes_view,
)

from ongs.cnpj_api import consultar_cnpj


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', home_view, name='home'),
    path('busca/', busca_view, name='busca'),

    path('login/', login_view, name='login'),
    path('cadastro/', cadastro_view, name='cadastro'),

    path('dashboard/', dashboard_view, name='dashboard'),

    path(
        'dashboard/instituicao/',
        dashboard_instituicao_view,
        name='dashboard_instituicao'
    ),
    path(
        'dashboard/instituicao/perfil/',
        dashboard_instituicao_perfil_view,
        name='dashboard_instituicao_perfil'
    ),
    path(
        'dashboard/instituicao/contato/',
        dashboard_instituicao_contato_view,
        name='dashboard_instituicao_contato'
    ),
    path(
        'dashboard/instituicao/configuracoes/',
        dashboard_instituicao_configuracoes_view,
        name='dashboard_instituicao_configuracoes'
    ),

    path(
        'api/cnpj/<str:cnpj>/',
        consultar_cnpj,
        name='consultar_cnpj'
    ),

    path(
        'dashboard/admin/',
        dashboard_admin_view,
        name='dashboard_admin'
    ),

    path(
        'dashboard/admin/gerenciar/',
        dashboard_admin_gerenciar_view,
        name='dashboard_admin_gerenciar'
    ),

    path(
        'dashboard/admin/categoria/',
        dashboard_admin_categoria_view,
        name='dashboard_admin_categoria'
    ),

    path(
        'dashboard/admin/configuracoes/',
        dashboard_admin_configuracoes_view,
        name='dashboard_admin_configuracoes'
    ),
]