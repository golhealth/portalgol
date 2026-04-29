from django import forms
from django.core.exceptions import ValidationError

from exames.forms import parse_valor_monetario_pt
from exames.models import Exame

from .models import Prestador


class PrestadorForm(forms.ModelForm):
    nome_completo = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                "placeholder": "Ex: AF Lisboa",
            }
        ),
        label="Nome Completo",
    )
    nif = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                "placeholder": "000000000",
                "inputmode": "numeric",
                "pattern": "\\d{9}",
            }
        ),
        label="NIF",
    )

    class Meta:
        model = Prestador
        fields = [
            "nome_completo",
            "nif",
            "inicio_protocolo_data",
            "inicio_protocolo_hora",
            "fim_protocolo_data",
            "fim_protocolo_hora",
            "estado",
            "codigo_postal",
            "localidade",
            "concelho",
            "distrito",
            "rua_avenida",
            "numero",
            "complemento",
            "observacoes_morada",
            "responsavel",
            "telefone",
            "email",
            "fax",
        ]

        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                    "placeholder": "email@exemplo.com",
                }
            ),
            "telefone": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                    "placeholder": "+351 000 000 000",
                }
            ),
            "inicio_protocolo_data": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                }
            ),
            "inicio_protocolo_hora": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                }
            ),
            "fim_protocolo_data": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                }
            ),
            "fim_protocolo_hora": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                }
            ),
            "estado": forms.RadioSelect(
                attrs={
                    "class": "flex flex-wrap gap-6",
                }
            ),
            "rua_avenida": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                    "placeholder": "Rua / Avenida",
                }
            ),
            "numero": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                    "placeholder": "Nº",
                    "inputmode": "numeric",
                }
            ),
            "complemento": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                    "placeholder": "Complemento (opcional)",
                }
            ),
            "codigo_postal": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                    "placeholder": "0000-000",
                }
            ),
            "localidade": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                    "placeholder": "Localidade",
                }
            ),
            "concelho": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                    "placeholder": "Concelho",
                }
            ),
            "distrito": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                    "placeholder": "Distrito",
                }
            ),
            "responsavel": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                    "placeholder": "Responsável",
                }
            ),
            "fax": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                    "placeholder": "--",
                }
            ),
            "observacoes_morada": forms.Textarea(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                    "placeholder": "Observações (opcional)",
                    "rows": 3,
                }
            ),
        }


class ExameValorForm(forms.Form):
    """
    Linha do formulário dinâmico "Exames e Valores" para Prestadores.
    """

    exame_nome = forms.ModelChoiceField(
        required=False,
        label="Ato médico",
        queryset=Exame.objects.none(),
        empty_label="Selecione um ato médico",
        widget=forms.Select(
            attrs={
                "class": "w-full bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-700 rounded-lg focus:ring-primary focus:border-primary px-4 py-2 text-sm",
            }
        ),
    )

    valor = forms.CharField(
        required=False,
        label="Valor",
        widget=forms.TextInput(
            attrs={
                "class": "w-full bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-700 rounded-lg focus:ring-primary focus:border-primary px-4 py-2.5 text-sm",
                "placeholder": "0,00",
                "inputmode": "decimal",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Usa apenas exames ativos.
        self.fields["exame_nome"].queryset = Exame.objects.filter(ativo=True).order_by(
            "nome"
        )

    def clean_valor(self):
        v = parse_valor_monetario_pt(self.cleaned_data.get("valor"))
        if v is not None and v < 0:
            raise ValidationError("O valor não pode ser negativo.")
        return v

