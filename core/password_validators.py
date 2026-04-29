"""Validadores adicionais de palavra-passe para o projeto."""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class ComplexidadePasswordValidator:
    """
    Exige maiúscula, minúscula, dígito e carácter especial (política do projeto).
    O comprimento mínimo global continua a ser aplicado pelo MinimumLengthValidator.
    """

    def validate(self, password, user=None):
        if not re.search(r"[a-z]", password):
            raise ValidationError(
                _("Tem de incluir pelo menos uma letra minúscula."),
                code="password_no_lower",
            )
        if not re.search(r"[A-Z]", password):
            raise ValidationError(
                _("Tem de incluir pelo menos uma letra maiúscula."),
                code="password_no_upper",
            )
        if not re.search(r"\d", password):
            raise ValidationError(
                _("Tem de incluir pelo menos um algarismo."),
                code="password_no_digit",
            )
        if not re.search(r"[!@#$%^&*\-_=+]", password):
            raise ValidationError(
                _(
                    "Tem de incluir pelo menos um carácter especial "
                    "(! @ # $ % ^ & * - _ = +)."
                ),
                code="password_no_special",
            )

    def get_help_text(self):
        return _(
            "A palavra-passe deve incluir maiúsculas, minúsculas, números e "
            "um carácter especial (!@#$%^&*-_=+), além do comprimento mínimo."
        )
