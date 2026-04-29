"""Geração de palavras-passe compatíveis com os validadores Django."""

from __future__ import annotations

import hashlib
import secrets
import string

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()

_CARACTERES_ESPECIAIS = "!@#$%^&*-_=+"


def gerar_palavra_passe_segura(email: str, minimo: int = 12) -> str:
    """
    Gera uma palavra-passe aleatória com pelo menos um carácter de cada tipo:
    minúscula, maiúscula, dígito e especial. Cumpre os validadores configurados
    em AUTH_PASSWORD_VALIDATORS (tamanho mínimo, complexidade, etc.).
    """
    if minimo < 8:
        minimo = 8

    alphabet = string.ascii_letters + string.digits + _CARACTERES_ESPECIAIS
    rng = secrets.SystemRandom()

    for _ in range(50):
        obrigatorios = [
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.digits),
            secrets.choice(_CARACTERES_ESPECIAIS),
        ]
        resto = [secrets.choice(alphabet) for _ in range(max(0, minimo - len(obrigatorios)))]
        partes = obrigatorios + resto
        rng.shuffle(partes)
        candidata = "".join(partes)
        try:
            uname = username_a_partir_do_email(email)
            validate_password(
                candidata,
                User(username=uname, email=email),
            )
            return candidata
        except ValidationError:
            minimo += 2

    raise RuntimeError("Não foi possível gerar uma palavra-passe válida.")


def username_a_partir_do_email(email: str) -> str:
    """`User.username` tem max_length=150; e-mails podem ser mais longos."""
    e = (email or "").strip().lower()
    if len(e) <= User._meta.get_field("username").max_length:
        return e
    return ("u" + hashlib.sha256(e.encode("utf-8")).hexdigest())[
        : User._meta.get_field("username").max_length
    ]
