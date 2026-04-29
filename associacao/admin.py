from django.contrib import admin

from .models import Associacao


@admin.register(Associacao)
class AssociacaoAdmin(admin.ModelAdmin):
    list_display = ("nome_completo", "nif", "estado", "criado_em")
    search_fields = ("nome_completo", "nif", "email", "telefone")
    list_filter = ("estado",)

