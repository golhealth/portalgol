from django.contrib import admin

from .models import Arbitro, RealizacaoExameArbitro


@admin.register(Arbitro)
class ArbitroAdmin(admin.ModelAdmin):
    list_display = (
        "nome_completo",
        "email",
        "categoria",
        "estado_aptidao",
        "ativo",
        "criado_em",
    )
    list_filter = ("ativo", "estado_aptidao", "categoria")
    search_fields = ("nome_completo", "email")


@admin.register(RealizacaoExameArbitro)
class RealizacaoExameArbitroAdmin(admin.ModelAdmin):
    list_display = ("arbitro", "data_realizacao", "prestador", "criado_em")
    list_filter = ("data_realizacao",)
    search_fields = ("arbitro__nome_completo", "prestador__nome_completo")
