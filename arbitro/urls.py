from django.urls import path

from . import views

app_name = "arbitro"

urlpatterns = [
    path("dashboard/", views.dashboard_arbitros, name="dashboard"),
    path("lista/", views.lista_arbitros, name="lista"),
    path("novo/", views.novo_arbitro, name="novo"),
    path("detalhe/<int:pk>/", views.detalhe_arbitro, name="detalhe"),
    path("editar/<int:pk>/", views.editar_arbitro, name="editar"),
    path("excluir/<int:pk>/", views.excluir_arbitro, name="excluir"),
    path(
        "lookup-codigo-postal/",
        views.lookup_codigo_postal,
        name="lookup_codigo_postal",
    ),
    path(
        "ajax/atualizar-estado-aptidao/",
        views.atualizar_estado_aptidao_ajax,
        name="atualizar_estado_aptidao_ajax",
    ),
    path(
        "ajax/carregar-exame/",
        views.carregar_exame_ajax,
        name="carregar_exame_ajax",
    ),
]

