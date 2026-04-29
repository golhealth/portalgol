from django.urls import path

from . import views

app_name = "prestador"

urlpatterns = [
    path("dashboard/", views.dashboard_prestadores, name="dashboard"),
    path("lista/", views.lista_prestadores, name="lista"),
    path("novo/", views.novo_prestador, name="novo"),
    path("detalhe/<int:pk>/", views.detalhe_prestador, name="detalhe"),
    path("editar/<int:pk>/", views.editar_prestador, name="editar"),
    path("excluir/<int:pk>/", views.excluir_prestador, name="excluir"),
    path("<int:pk>/atos/", views.prestador_atos_realizados, name="atos"),
]

