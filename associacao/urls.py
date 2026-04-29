from django.urls import path

from . import views

app_name = "associacao"

urlpatterns = [
    path("dashboard/", views.dashboard_associacoes, name="dashboard"),
    path("novo/", views.novo_associacao, name="novo"),
    path(
        "<int:pk>/fatura-exames/",
        views.associacao_fatura_exames,
        name="fatura_exames",
    ),
    path("detalhe/<int:pk>/", views.detalhe_associacao, name="detalhe"),
    path("editar/<int:pk>/", views.editar_associacao, name="editar"),
    path("excluir/<int:pk>/", views.excluir_associacao, name="excluir"),
]

