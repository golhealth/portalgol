from django.db import models
from django.db.models import Q


class Arbitro(models.Model):
    ESTADO_APTIDAO_CHOICES = (
        ("ativo", "Ativo"),
        ("inativo", "Inativo"),
        ("aguardando_exame", "Aguardando o exame"),
    )

    nome_completo = models.CharField("Nome completo", max_length=255)
    data_nascimento = models.DateField("Data de nascimento", null=True, blank=True)
    cpf_nif = models.CharField("NIF", max_length=9, blank=True)
    SEXO_CHOICES = (
        ("M", "Masculino"),
        ("F", "Feminino"),
    )
    sexo = models.CharField("Sexo", max_length=1, choices=SEXO_CHOICES, blank=True)
    email = models.EmailField("Email", blank=True)
    telefone = models.CharField("Telemóvel", max_length=30, blank=True)
    # Campos de endereço (mantém `morada` antigo para compatibilidade,
    # mas o formulário vai usar estes campos novos).
    morada = models.CharField("Morada", max_length=255, blank=True)
    codigo_postal = models.CharField("Código postal", max_length=20, blank=True)
    localidade = models.CharField("Localidade", max_length=100, blank=True)
    rua_avenida = models.CharField("Rua / Avenida", max_length=255, blank=True)
    numero = models.CharField("Número", max_length=20, blank=True)
    complemento = models.CharField("Complemento", max_length=100, blank=True)
    observacoes_morada = models.TextField("Observações da morada", blank=True)
    cidade = models.CharField("Cidade", max_length=100, blank=True)
    categoria = models.ForeignKey(
        "core.Categoria",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="arbitros",
    )
    associacao_futebol = models.ForeignKey(
        "associacao.Associacao",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="arbitros",
        verbose_name="Associação de futebol",
    )
    modalidade = models.ForeignKey(
        "core.Modalidade",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="arbitros",
        verbose_name="Modalidade",
    )
    data_ultimo_exame = models.DateField(
        "Data do último exame médico", null=True, blank=True
    )
    estado_aptidao = models.CharField(
        "Situação de aptidão",
        max_length=32,
        choices=ESTADO_APTIDAO_CHOICES,
        default="ativo",
    )
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Árbitro"
        verbose_name_plural = "Árbitros"
        constraints = [
            # Garante unicidade do NIF apenas quando não estiver vazio.
            models.UniqueConstraint(
                fields=["cpf_nif"],
                condition=~Q(cpf_nif=""),
                name="uniq_arbitro_cpf_nif_not_empty",
            )
        ]

    def save(self, *args, **kwargs) -> None:
        self.ativo = self.estado_aptidao != "inativo"
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.nome_completo


class RealizacaoExameArbitro(models.Model):
    """Registo de exame médico carregado (realização) para histórico."""

    arbitro = models.ForeignKey(
        Arbitro,
        on_delete=models.CASCADE,
        related_name="realizacoes_exame",
    )
    data_realizacao = models.DateField("Data da realização")
    prestador = models.ForeignKey(
        "prestador.Prestador",
        on_delete=models.PROTECT,
        related_name="realizacoes_exame_arbitro",
    )
    exames_complementares = models.TextField("Exames complementares", blank=True)
    data_marcacao_complementar = models.DateTimeField(
        "Data marcada para exame complementar",
        null=True,
        blank=True,
    )
    observacoes = models.TextField("Observações", blank=True)
    arquivo_exame = models.FileField(
        "Ficheiro do exame",
        upload_to="exames/arbitros/",
        blank=True,
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Realização de exame (árbitro)"
        verbose_name_plural = "Realizações de exame (árbitros)"
        ordering = ["-criado_em"]

    def __str__(self) -> str:
        return f"{self.arbitro} — {self.data_realizacao}"

