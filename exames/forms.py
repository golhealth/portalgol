from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django import forms
from django.core.exceptions import ValidationError

from .models import Exame, MarcacaoExame

DT_LOCAL = ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M")
INPUT_CLASS = "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white px-4 py-2.5 text-sm"


def parse_valor_monetario_pt(value, *, max_digits: int = 12, decimal_places: int = 2) -> Decimal | None:
    """
    Aceita valores introduzidos no formato português (ex.: 50,00 ou 1.234,56)
    num campo de texto, compatível com o placeholder 0,00.
    """
    if value in (None, ""):
        return None
    if isinstance(value, Decimal):
        dec = value
    else:
        s = str(value).strip()
        if not s:
            return None
        s = s.replace(" ", "")
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")
        try:
            dec = Decimal(s)
        except InvalidOperation:
            raise ValidationError("Introduza um valor numérico válido.") from None

    dec = dec.quantize(Decimal("1") / (10**decimal_places), rounding=ROUND_HALF_UP)
    limit = Decimal(10 ** (max_digits - decimal_places)) - Decimal("1") / (
        10**decimal_places
    )
    if dec.copy_abs() > limit:
        raise ValidationError(
            f"O valor excede o máximo permitido ({max_digits} dígitos no total)."
        )
    return dec


class MarcacaoExameEditForm(forms.ModelForm):
    class Meta:
        model = MarcacaoExame
        fields = ["prestador", "data_hora_consulta", "observacao"]
        widgets = {
            "prestador": forms.Select(attrs={"class": INPUT_CLASS}),
            "data_hora_consulta": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={"type": "datetime-local", "class": INPUT_CLASS},
            ),
            "observacao": forms.Textarea(
                attrs={
                    "class": INPUT_CLASS,
                    "rows": 3,
                    "placeholder": "Opcional",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["data_hora_consulta"].input_formats = DT_LOCAL
        self.fields["observacao"].required = False
        self.fields["prestador"].queryset = self.fields["prestador"].queryset.order_by(
            "nome_completo"
        )


class ImportAtosExcelForm(forms.Form):
    """Upload da listagem de atos médicos (.xlsx)."""

    arquivo = forms.FileField(
        label="Ficheiro Excel (.xlsx)",
        widget=forms.ClearableFileInput(attrs={"accept": ".xlsx"}),
    )

    def clean_arquivo(self):
        uploaded = self.cleaned_data["arquivo"]
        name = (uploaded.name or "").lower()
        if not name.endswith(".xlsx"):
            raise ValidationError("O ficheiro deve estar no formato .xlsx.")
        return uploaded


class ExameForm(forms.ModelForm):
    class Meta:
        model = Exame
        fields = ["codigo", "nome", "abreviatura", "ativo"]
        widgets = {
            "codigo": forms.NumberInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                    "placeholder": "Ex: 100",
                }
            ),
            "nome": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                    "placeholder": "Ex: Consulta Médica",
                }
            ),
            "abreviatura": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                    "placeholder": "Ex: CM",
                }
            ),
            "ativo": forms.CheckboxInput(
                attrs={
                    "class": "h-4 w-4 rounded border-slate-300 text-primary focus:ring-primary/50",
                }
            ),
        }

