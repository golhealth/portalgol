from django.conf import settings
from django.db import models, transaction


class Epoca(models.Model):
    """
    Registo da época (ex.: temporada/despacho de validade) para usar em
    validações futuras (exames, credenciações, etc.).
    """

    nome = models.CharField("Nome da Época", max_length=100, unique=True)

    inicio_data = models.DateField("Início", null=True, blank=True)
    fim_data = models.DateField("Fim", null=True, blank=True)

    ativo = models.BooleanField("Ativa", default=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        verbose_name = "Época"
        verbose_name_plural = "Épocas"
        ordering = ["-criado_em", "nome"]

    def __str__(self) -> str:
        return self.nome

    def save(self, *args, **kwargs) -> None:
        """
        Garante que só existe uma época marcada como ativa.
        """
        with transaction.atomic():
            if self.ativo:
                Epoca.objects.exclude(pk=self.pk).update(ativo=False)
            super().save(*args, **kwargs)


class EpocaAssociacao(models.Model):
    """
    Liga associações de futebol a uma época específica.

    Assim conseguimos, na página da época, selecionar quais associações
    devem ser apresentadas/ativadas para aquela época.
    """

    epoca = models.ForeignKey(
        Epoca,
        on_delete=models.CASCADE,
        related_name="associacoes_epoca",
    )
    associacao = models.ForeignKey(
        "associacao.Associacao",
        on_delete=models.CASCADE,
        related_name="epocas",
    )
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        verbose_name = "Associação na Época"
        verbose_name_plural = "Associações nas Épocas"
        unique_together = ("epoca", "associacao")
        ordering = ["-criado_em"]

    def __str__(self) -> str:
        return f"{self.associacao} - {self.epoca}"


class EpocaArbitro(models.Model):
    """
    Liga árbitros a uma época específica.

    Permite depois filtrar os árbitros “daquela época” mesmo sem ter
    `epoca` diretamente no model `Arbitro`.
    """

    epoca = models.ForeignKey(
        Epoca,
        on_delete=models.CASCADE,
        related_name="arbitros_epoca",
    )
    arbitro = models.ForeignKey(
        "arbitro.Arbitro",
        on_delete=models.CASCADE,
        related_name="epocas",
    )
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        verbose_name = "Árbitro na Época"
        verbose_name_plural = "Árbitros nas Épocas"
        unique_together = ("epoca", "arbitro")
        ordering = ["-criado_em"]

    def __str__(self) -> str:
        return f"{self.arbitro} - {self.epoca}"


class Categoria(models.Model):
    """Categoria para o registo de árbitros."""

    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class Modalidade(models.Model):
    """Modalidade para o registo de árbitros."""

    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Modalidade"
        verbose_name_plural = "Modalidades"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class Departamento(models.Model):
    """Departamento organizacional para contas do backoffice."""

    nome = models.CharField(max_length=120, unique=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class PerfilConta(models.Model):
    """
    Extensão mínima do utilizador Django para fluxos do backoffice
    (ex.: primeira alteração obrigatória de palavra-passe).
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_conta",
    )
    forcar_troca_password = models.BooleanField(
        "Obrigar troca de palavra-passe no próximo acesso",
        default=False,
    )
    avatar = models.FileField(
        "Foto de perfil",
        upload_to="perfil/avatar/",
        blank=True,
        null=True,
    )
    departamento = models.CharField(
        "Departamento",
        max_length=120,
        blank=True,
        default="",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Perfil de conta"
        verbose_name_plural = "Perfis de conta"

    def __str__(self) -> str:
        return f"Perfil: {self.user}"
