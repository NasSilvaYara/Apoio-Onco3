from django.contrib import admin
from .models import Administrador, Instituicao


@admin.register(Administrador)
class AdministradorAdmin(admin.ModelAdmin):
    list_display = ('idAdm', 'nomeAdm', 'emailAdm')


@admin.register(Instituicao)
class InstituicaoAdmin(admin.ModelAdmin):
    list_display = (
        'idInst',
        'nomeInst',
        'cidade',
        'estado',
        'status',
    )

    list_filter = ('status', 'estado', 'cidade')

    search_fields = (
        'nomeInst',
        'cidade',
        'estado',
        'email',
    )