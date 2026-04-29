from django import forms

from .models import Arbitro
from associacao.models import Associacao
from core.models import Modalidade


class ArbitroForm(forms.ModelForm):
    class Meta:
        model = Arbitro
        fields = [
            "nome_completo",
            "data_nascimento",
            "cpf_nif",
            "sexo",
            "email",
            "telefone",
            "codigo_postal",
            "localidade",
            "rua_avenida",
            "numero",
            "complemento",
            "observacoes_morada",
            "cidade",
            "categoria",
            "associacao_futebol",
            "modalidade",
            "data_ultimo_exame",
            "estado_aptidao",
        ]
        widgets = {
            "nome_completo": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 "
                    "dark:border-slate-700 dark:text-white",
                    "placeholder": "Ex: João Miguel Ferreira da Silva",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 "
                    "dark:border-slate-700 dark:text-white",
                    "placeholder": "email@exemplo.com",
                }
            ),
            "data_nascimento": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full h-[42px] px-3 rounded-lg border-[#d1d5db] dark:bg-slate-800 "
                    "dark:border-slate-700 dark:text-white",
                }
            ),
            "cpf_nif": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 "
                    "dark:border-slate-700 dark:text-white",
                    "placeholder": "000000000",
                    "inputmode": "numeric",
                    "pattern": "\\d{9}",
                }
            ),
            "telefone": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 "
                    "dark:border-slate-700 dark:text-white",
                    "placeholder": "+351 000 000 000",
                }
            ),
            "cidade": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 "
                    "dark:border-slate-700 dark:text-white",
                    "placeholder": "Cidade",
                }
            ),
            "codigo_postal": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 "
                    "dark:border-slate-700 dark:text-white",
                    "placeholder": "Código Postal",
                    "inputmode": "numeric",
                }
            ),
            "localidade": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 "
                    "dark:border-slate-700 dark:text-white",
                    "placeholder": "Localidade",
                }
            ),
            "rua_avenida": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 "
                    "dark:border-slate-700 dark:text-white",
                    "placeholder": "Rua / Avenida",
                }
            ),
            "numero": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 "
                    "dark:border-slate-700 dark:text-white",
                    "placeholder": "Número",
                }
            ),
            "complemento": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 "
                    "dark:border-slate-700 dark:text-white",
                    "placeholder": "Complemento",
                }
            ),
            "observacoes_morada": forms.Textarea(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 "
                    "dark:border-slate-700 dark:text-white",
                    "rows": 3,
                    "placeholder": "Observações",
                }
            ),
            "categoria": forms.Select(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 "
                    "dark:border-slate-700 dark:text-white",
                }
            ),
            "associacao_futebol": forms.Select(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 "
                    "dark:border-slate-700 dark:text-white",
                }
            ),
            "modalidade": forms.Select(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 "
                    "dark:border-slate-700 dark:text-white",
                }
            ),
            "data_ultimo_exame": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full pl-10 rounded-lg border-[#d1d5db] dark:bg-slate-800 "
                    "dark:border-slate-700 dark:text-white",
                }
            ),
            "estado_aptidao": forms.Select(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 "
                    "dark:border-slate-700 dark:text-white",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostra apenas associações ativas no registo de árbitros.
        self.fields["associacao_futebol"].queryset = (
            Associacao.objects.filter(estado="ativo").order_by("nome_completo")
        )

        # Mostra apenas modalidades (todas são elegíveis no momento).
        self.fields["modalidade"].queryset = Modalidade.objects.all().order_by("nome")

        # UX: todos os campos (exceto `nome_completo`) devem ser opcionais.
        # O modelo já tem `blank=True` para a maioria, mas garantimos aqui.
        for field_name, field in self.fields.items():
            if field_name != "nome_completo":
                field.required = False

    sexo = forms.ChoiceField(
        choices=Arbitro.SEXO_CHOICES,
        required=False,
        widget=forms.RadioSelect(
            attrs={
                "class": "text-primary focus:ring-primary border-[#d1d5db] dark:bg-slate-800",
            }
        ),
        label="Sexo",
    )

    def clean_cpf_nif(self):
        cpf_nif = self.cleaned_data.get("cpf_nif", "") or ""
        cpf_nif = str(cpf_nif).strip()
        if not cpf_nif:
            return ""

        qs = Arbitro.objects.filter(cpf_nif=cpf_nif)
        if self.instance and getattr(self.instance, "pk", None):
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("Este NIF já está registado.")
        return cpf_nif

