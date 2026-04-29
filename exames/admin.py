from django.contrib import admin

from .models import Exame, MarcacaoExame


@admin.register(Exame)
class ExameAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo", "criado_em")
    search_fields = ("nome",)
    list_filter = ("ativo",)


@admin.register(MarcacaoExame)
class MarcacaoExameAdmin(admin.ModelAdmin):
    list_display = (
        "epoca",
        "associacao",
        "arbitro",
        "prestador",
        "data_hora_consulta",
        "criado_em",
    )
    search_fields = ("arbitro__nome_completo", "associacao__nome_completo", "epoca__nome")
    list_filter = ("epoca", "associacao", "prestador")

