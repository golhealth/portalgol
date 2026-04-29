from django.urls import path

from . import views

app_name = "exames"

urlpatterns = [
    path("", views.dashboard_exames, name="dashboard"),
    path("novo/", views.novo_ato, name="novo"),
    path("novo/ajax/", views.novo_ato_ajax, name="novo_ato_ajax"),
    path("marcar/", views.marcar_exames_dashboard, name="marcar_exames"),
    path("marcar/ajax/", views.marcar_exame_ajax, name="marcar_exame_ajax"),
    path("prestador-exames/ajax/", views.prestador_exames_ajax, name="prestador_exames_ajax"),
    path("marcados/", views.exames_marcados, name="exames_marcados"),
    path("marcados/<int:pk>/editar/", views.marcar_exame_editar, name="marcacao_editar"),
    path("marcados/<int:pk>/excluir/", views.marcar_exame_excluir, name="marcacao_excluir"),
    path("marcados/<int:pk>/", views.marcar_exame_detalhe, name="marcacao_detalhe"),
    path("editar/<int:pk>/", views.editar_exame, name="editar"),
]

