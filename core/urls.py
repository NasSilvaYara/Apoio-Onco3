from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from ongs.views import (
    home_view,
    busca_view,
    informacoes_view,
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
    filtro_view,
    ver_instituicao_view,
    logout_view,
)

from ongs.cnpj_api import consultar_cnpj


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', home_view, name='home'),
    path('busca/', busca_view, name='busca'),
    path('informacoes/<slug:tema>/', informacoes_view, name='informacoes_detalhe'),

    path('login/', login_view, name='login'),
    path('cadastro/', cadastro_view, name='cadastro'),
    path('logout/', logout_view, name='logout'),

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

    path('filtro/', filtro_view, name='filtro'),
    path('instituicao/', ver_instituicao_view, name='ver_instituicao'),
    path('instituicao/<int:pk>/', ver_instituicao_view, name='ver_instituicao_detalhe'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)