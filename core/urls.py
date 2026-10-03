"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from ongs.views import home_view, dashboard_view, login_view, cadastro_view

urlpatterns = [
    path('', home_view, name='home'),                     # <--- Página inicial (http://127.0.0.1:8000/)
    path('admin/', admin.site.urls),
    path('dashboard/', dashboard_view, name='dashboard'), # <--- Painel Admin
    path('login/', login_view, name='login'),
    path('cadastro/', cadastro_view, name='cadastro'),
]