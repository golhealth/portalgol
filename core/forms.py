from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group

from .models import Categoria, Departamento, Epoca, Modalidade
from .password_utils import username_a_partir_do_email

User = get_user_model()


class LoginForm(forms.Form):
    """Formulário de login com e-mail e password."""
    username = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={
            "class": "w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4",
            "placeholder": "seu@email.com",
            "autofocus": True,
        }),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "class": "w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4",
            "placeholder": "••••••••",
        }),
    )
    next = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("username")
        password = cleaned_data.get("password")
        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise forms.ValidationError("E-mail ou password incorretos.")
            auth_user = authenticate(username=user.username, password=password)
            if auth_user is None:
                raise forms.ValidationError("E-mail ou password incorretos.")
            self.user = auth_user
        return cleaned_data


class CategoriaForm(forms.ModelForm):
    """Formulário simples para registar uma nova categoria."""

    class Meta:
        model = Categoria
        fields = ["nome"]
        widgets = {
            "nome": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                    "placeholder": "Ex: Cardiológico",
                }
            )
        }


class ModalidadeForm(forms.ModelForm):
    """Formulário simples para registar uma nova modalidade."""

    class Meta:
        model = Modalidade
        fields = ["nome"]
        widgets = {
            "nome": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                    "placeholder": "Ex: Cardiológico",
                }
            )
        }


class DepartamentoForm(forms.ModelForm):
    """Formulário simples para registar um departamento."""

    class Meta:
        model = Departamento
        fields = ["nome", "ativo"]
        widgets = {
            "nome": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                    "placeholder": "Ex: Operações Clínicas",
                }
            ),
            "ativo": forms.CheckboxInput(
                attrs={
                    "class": "h-4 w-4 rounded border-slate-300 text-primary focus:ring-primary/50",
                }
            ),
        }


class EpocaForm(forms.ModelForm):
    """Formulário para registar uma nova época."""

    class Meta:
        model = Epoca
        fields = ["nome", "inicio_data", "fim_data", "ativo"]
        widgets = {
            "nome": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                    "placeholder": "Ex: 2026 / Temporada de Primavera",
                }
            ),
            "inicio_data": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                }
            ),
            "fim_data": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                }
            ),
            "ativo": forms.CheckboxInput(
                attrs={
                    "class": "h-4 w-4 rounded border-slate-300 text-primary focus:ring-primary/50",
                }
            ),
        }


class EpocaAtivoForm(forms.ModelForm):
    """
    Form para o dashboard: permite apenas marcar a época como ativa/inativa.
    """

    class Meta:
        model = Epoca
        fields = ["ativo"]
        widgets = {
            "ativo": forms.CheckboxInput(
                attrs={
                    "class": "h-4 w-4 rounded border-slate-300 text-primary focus:ring-primary/50",
                }
            )
        }


class ImportArbitrosExcelForm(forms.Form):
    """
    Upload do Excel com a lista de árbitros para importar.
    """

    arquivo = forms.FileField(
        required=True,
        label="Ficheiro Excel (.xlsx)",
        widget=forms.ClearableFileInput(
            attrs={
                "class": "w-full rounded-lg border-[#d1d5db] dark:bg-slate-800 dark:border-slate-700 dark:text-white",
                "accept": ".xlsx",
            }
        ),
    )


class CriarUtilizadorForm(forms.Form):
    """
    Criação de utilizador no backoffice (apenas superutilizadores).
    O nome de utilizador interno fica igual ao e-mail; a palavra-passe é gerada e enviada por e-mail.
    """

    first_name = forms.CharField(
        label="Primeiro Nome",
        required=False,
        max_length=150,
        widget=forms.TextInput(),
    )
    last_name = forms.CharField(
        label="Último Nome",
        required=False,
        max_length=150,
        widget=forms.TextInput(),
    )
    departamento = forms.ModelChoiceField(
        label="Departamento",
        required=False,
        queryset=Departamento.objects.filter(ativo=True).order_by("nome"),
        empty_label="Selecione um departamento",
        widget=forms.Select(),
    )
    email = forms.EmailField(
        label="E-mail",
        required=True,
        help_text="Será usado para iniciar sessão e como identificador da conta.",
        widget=forms.EmailInput(),
    )
    groups = forms.ModelMultipleChoiceField(
        label="Grupos",
        queryset=Group.objects.all().order_by("name"),
        required=False,
        help_text="Permissões herdadas dos grupos (opcional).",
        widget=forms.SelectMultiple(attrs={"size": 8, "class": ""}),
    )
    is_active = forms.BooleanField(
        label="Utilizador ativo",
        required=False,
        initial=True,
        help_text="Se desativado, não consegue iniciar sessão.",
    )
    is_staff = forms.BooleanField(
        label="Membro da equipa (staff)",
        required=False,
        initial=False,
        help_text="Permite acesso a funcionalidades administrativas.",
    )
    is_superuser = forms.BooleanField(
        label="Superutilizador",
        required=False,
        initial=False,
        help_text="Acesso total sem restrições de permissões.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base = (
            "w-full rounded-lg border border-slate-200 dark:border-slate-700 "
            "bg-white dark:bg-slate-900 px-4 py-2.5 text-sm text-slate-900 dark:text-slate-100 "
            "focus:ring-2 focus:ring-primary/50 focus:border-primary"
        )
        self.fields["first_name"].widget.attrs.setdefault("class", base)
        self.fields["last_name"].widget.attrs.setdefault("class", base)
        self.fields["departamento"].widget.attrs.setdefault("class", base)
        self.fields["email"].widget.attrs.setdefault("class", base)
        self.fields["groups"].widget.attrs["class"] = base + " min-h-[10rem] py-2"
        check = "h-5 w-5 rounded border-slate-300 text-primary focus:ring-primary/40"
        self.fields["is_active"].widget.attrs["class"] = check
        self.fields["is_staff"].widget.attrs["class"] = check
        self.fields["is_superuser"].widget.attrs["class"] = check

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Já existe um utilizador com este e-mail.")
        uname = username_a_partir_do_email(email)
        if User.objects.filter(username=uname).exists():
            raise forms.ValidationError("Não foi possível gerar um identificador de conta único.")
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("is_superuser"):
            cleaned["is_staff"] = True
        return cleaned


class EditarUtilizadorForm(forms.Form):
    """Edição de conta no backoffice para superutilizadores."""

    first_name = forms.CharField(label="Primeiro Nome", required=False, max_length=150)
    last_name = forms.CharField(label="Último Nome", required=False, max_length=150)
    departamento = forms.ModelChoiceField(
        label="Departamento",
        required=False,
        queryset=Departamento.objects.filter(ativo=True).order_by("nome"),
        empty_label="Selecione um departamento",
        widget=forms.Select(),
    )
    email = forms.EmailField(label="E-mail", required=True, widget=forms.EmailInput())
    groups = forms.ModelMultipleChoiceField(
        label="Grupos",
        queryset=Group.objects.all().order_by("name"),
        required=False,
        widget=forms.SelectMultiple(attrs={"size": 8}),
    )
    is_active = forms.BooleanField(label="Utilizador ativo", required=False)
    is_staff = forms.BooleanField(label="Membro da equipa (staff)", required=False)
    is_superuser = forms.BooleanField(label="Superutilizador", required=False)

    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop("user_instance", None)
        super().__init__(*args, **kwargs)
        base = (
            "w-full rounded-lg border border-slate-200 dark:border-slate-700 "
            "bg-white dark:bg-slate-900 px-4 py-2.5 text-sm text-slate-900 dark:text-slate-100 "
            "focus:ring-2 focus:ring-primary/50 focus:border-primary"
        )
        for n in ("first_name", "last_name", "departamento", "email", "groups"):
            self.fields[n].widget.attrs.setdefault("class", base)
        self.fields["groups"].widget.attrs["class"] = base + " min-h-[10rem] py-2"
        check = "h-5 w-5 rounded border-slate-300 text-primary focus:ring-primary/40"
        self.fields["is_active"].widget.attrs["class"] = check
        self.fields["is_staff"].widget.attrs["class"] = check
        self.fields["is_superuser"].widget.attrs["class"] = check

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.user_instance is not None:
            qs = qs.exclude(pk=self.user_instance.pk)
        if qs.exists():
            raise forms.ValidationError("Já existe um utilizador com este e-mail.")
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("is_superuser"):
            cleaned["is_staff"] = True
        return cleaned
