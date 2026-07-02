from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.login_view, name="login"),
    path("conta/primeiro-acesso/", views.primeiro_acesso_password, name="primeiro_acesso_password"),
    path("index/", views.index_view, name="index"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    # Mantém a URL `/exames/novo/`, mas o handler fica no `core`
    path("exames/novo/", views.novo_exame, name="novo_exame"),
    path("perfil/", views.profile_view, name="profile"),
    path("utilizadores/", views.utilizadores_dashboard, name="utilizadores_dashboard"),
    path("utilizadores/novo/", views.criar_utilizador, name="criar_utilizador"),
    path("utilizadores/<int:pk>/editar/", views.editar_utilizador, name="utilizador_editar"),
    path(
        "utilizadores/<int:pk>/toggle-ativo/",
        views.utilizador_toggle_ativo,
        name="utilizador_toggle_ativo",
    ),
    path(
        "utilizadores/apagar-em-massa/",
        views.utilizadores_apagar_em_massa,
        name="utilizadores_apagar_em_massa",
    ),
    path("departamentos/novo/", views.novo_departamento, name="departamento_novo"),
    path(
        "departamentos/novo/ajax/",
        views.novo_departamento_ajax,
        name="departamento_novo_ajax",
    ),
    path("categorias/novo/", views.novo_categoria, name="categoria_novo"),
    path("categorias/novo/ajax/", views.novo_categoria_ajax, name="categoria_novo_ajax"),
    path("modalidades/novo/", views.novo_modalidade, name="modalidade_novo"),
    path("modalidades/novo/ajax/", views.novo_modalidade_ajax, name="modalidade_novo_ajax"),
    path("epocas/novo/", views.novo_epoca, name="epoca_novo"),
    path("epocas/novo/ajax/", views.novo_epoca_ajax, name="epoca_novo_ajax"),
    path("exames/novo/ajax/", views.novo_exame_ajax, name="exame_novo_ajax"),
    path("epocas/<int:pk>/", views.epoca_detalhe, name="epoca_detalhe"),
    path(
        "epocas/<int:pk>/associacoes/add/ajax/",
        views.epoca_associacao_add_ajax,
        name="epoca_associacao_add_ajax",
    ),
    path(
        "epocas/<int:epoca_pk>/associacoes/<int:associacao_pk>/arbitros/importar/",
        views.epoca_associacao_import_arbitros,
        name="epoca_associacao_import_arbitros",
    ),
    path(
        "epocas/<int:epoca_pk>/associacoes/<int:associacao_pk>/arbitros/",
        views.epoca_associacao_arbitros,
        name="epoca_associacao_arbitros",
    ),
]
