from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist


def header_user(request):
    """Nome completo e departamento do utilizador autenticado (cabeçalho da app)."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}

    nome = (user.get_full_name() or "").strip()
    if not nome:
        nome = user.get_username()

    departamento = ""
    try:
        departamento = (user.perfil_conta.departamento or "").strip()
    except ObjectDoesNotExist:
        departamento = ""

    partes = [p for p in nome.split() if p]
    if len(partes) >= 2:
        inicial = (partes[0][0] + partes[-1][0]).upper()
    elif partes:
        inicial = partes[0][0].upper()
    else:
        inicial = "?"

    return {
        "header_user_nome": nome,
        "header_user_departamento": departamento or "—",
        "header_user_inicial": inicial,
    }
