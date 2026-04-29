from django.contrib import admin

from .models import Categoria, Departamento, Epoca, Modalidade, PerfilConta


@admin.register(PerfilConta)
class PerfilContaAdmin(admin.ModelAdmin):
    list_display = ("user", "forcar_troca_password", "criado_em")
    list_filter = ("forcar_troca_password",)
    search_fields = ("user__username", "user__email")


@admin.register(Epoca)
class EpocaAdmin(admin.ModelAdmin):
    list_display = ("nome", "inicio_data", "fim_data", "ativo", "criado_em")
    list_filter = ("ativo",)
    search_fields = ("nome",)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)


@admin.register(Modalidade)
class ModalidadeAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo", "criado_em")
    list_filter = ("ativo",)
    search_fields = ("nome",)
