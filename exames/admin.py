from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path, reverse

from .forms import ImportAtosExcelForm
from .import_atos import importar_atos_excel
from .models import Exame, MarcacaoExame


@admin.register(Exame)
class ExameAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "abreviatura", "ativo", "criado_em")
    search_fields = ("codigo", "nome", "abreviatura")
    list_filter = ("ativo",)
    ordering = ("codigo", "nome")
    change_list_template = "admin/exames/exame/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "importar-excel/",
                self.admin_site.admin_view(self.importar_excel_view),
                name="exames_exame_importar_excel",
            ),
        ]
        return custom + urls

    def importar_excel_view(self, request):
        if not self.has_add_permission(request):
            messages.error(request, "Não tem permissão para importar atos médicos.")
            return redirect("admin:exames_exame_changelist")

        if request.method == "POST":
            form = ImportAtosExcelForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    result = importar_atos_excel(form.cleaned_data["arquivo"].read())
                except ValueError as exc:
                    messages.error(request, str(exc))
                except Exception:
                    messages.error(
                        request,
                        "Não foi possível ler o ficheiro Excel. Verifique o formato.",
                    )
                else:
                    msg = (
                        f"Importação concluída: {result['inserted']} criados, "
                        f"{result['updated']} atualizados, {result['skipped']} ignorados."
                    )
                    if result["errors"]:
                        preview = "; ".join(result["errors"][:5])
                        if len(result["errors"]) > 5:
                            preview += f" … (+{len(result['errors']) - 5} avisos)"
                        msg += f" Avisos: {preview}"
                    messages.success(request, msg)
                    return redirect("admin:exames_exame_changelist")
            else:
                messages.error(request, "Selecione um ficheiro .xlsx válido.")
        else:
            form = ImportAtosExcelForm()

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Importar atos médicos (Excel)",
            "form": form,
            "changelist_url": reverse("admin:exames_exame_changelist"),
        }
        return render(request, "admin/exames/exame/importar_atos.html", context)


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
