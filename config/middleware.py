from __future__ import annotations

from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from core.models import PerfilConta


class IdleTimeoutMiddleware:
    """
    Faz logout do utilizador após X segundos de inatividade (sem requests).

    A contagem é atualizada a cada request autenticada.
    """

    SESSION_ACTIVITY_KEY = "last_activity_at"

    def __init__(self, get_response):
        self.get_response = get_response
        self.idle_timeout_seconds = int(
            getattr(settings, "SESSION_IDLE_TIMEOUT", 600)
        )

        try:
            self.login_path = reverse(settings.LOGIN_URL)
        except Exception:
            self.login_path = None

        try:
            self.logout_path = reverse("logout")
        except Exception:
            self.logout_path = None

    def __call__(self, request):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return self.get_response(request)

        # Evita interferir com assets/rotas do sistema.
        path = request.path or ""
        if path.startswith("/static/") or path.startswith("/admin/"):
            return self.get_response(request)

        if self.logout_path and path.startswith(self.logout_path):
            return self.get_response(request)

        # LOGIN_URL está configurado como rota raiz ("/"). Nesse caso, "startswith('/')" seria
        # verdadeiro para todas as páginas. Por isso, fazemos apenas match exato.
        if self.login_path:
            if self.login_path == "/" and path != "/":
                pass
            elif self.login_path != "/" and path.startswith(self.login_path):
                return self.get_response(request)
            elif self.login_path == "/" and path == "/":
                return self.get_response(request)

        now_ts = timezone.now().timestamp()
        last_ts = request.session.get(self.SESSION_ACTIVITY_KEY)

        if last_ts is not None:
            try:
                last_ts_float = float(last_ts)
            except (TypeError, ValueError):
                last_ts_float = None

            if last_ts_float is not None:
                idle_seconds = now_ts - last_ts_float
                if idle_seconds > self.idle_timeout_seconds:
                    logout(request)
                    # Garantir flush/limpeza da sessão (o logout já tenta, mas reforça).
                    request.session.flush()
                    target_login = self.login_path or "/"
                    return redirect(f"{target_login}?timeout=1")

        request.session[self.SESSION_ACTIVITY_KEY] = now_ts
        return self.get_response(request)


class ForcarTrocaPasswordMiddleware:
    """
    Utilizadores com perfil.forcar_troca_password só podem aceder à troca
    de palavra-passe (e logout) até concluírem a alteração.
    """

    PREFIXOS_ISENTOS = (
        "/conta/primeiro-acesso",
        "/conta/logout",
        "/admin/",
        "/static/",
    )
    EXACT_ISENTOS = frozenset({"/favicon.ico"})

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            path = request.path_info or ""
            if path in self.EXACT_ISENTOS or any(
                path.startswith(p) for p in self.PREFIXOS_ISENTOS
            ):
                return self.get_response(request)
            try:
                if user.perfil_conta.forcar_troca_password:
                    return redirect("core:primeiro_acesso_password")
            except PerfilConta.DoesNotExist:
                pass

        return self.get_response(request)


class LoginRequiredMiddleware:
    """
    Garante que qualquer página (exceto `core:login`, assets e admin) exige login.

    Isto evita que rotas novas fiquem públicas por engano.
    """

    def __init__(self, get_response):
        self.get_response = get_response

        try:
            self.login_path = reverse(settings.LOGIN_URL)
        except Exception:
            self.login_path = "/"

        self.static_prefixes = ("/static/",)
        self.admin_prefixes = ("/admin/",)
        self.excluded_exact_paths = {"/favicon.ico", "/robots.txt"}

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            return self.get_response(request)

        path = request.path_info or ""

        if path in self.excluded_exact_paths:
            return self.get_response(request)

        if path.startswith(self.static_prefixes):
            return self.get_response(request)

        if path.startswith(self.admin_prefixes):
            return self.get_response(request)

        # Permite acesso ao login apenas.
        if self.login_path == "/":
            if path == "/":
                return self.get_response(request)
        else:
            if path.startswith(self.login_path):
                return self.get_response(request)

        return redirect(self.login_path)

