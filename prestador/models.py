from django.db import models


class Prestador(models.Model):
    ESTADO_CHOICES = [
        ("ativo", "Ativo"),
        ("inativo", "Inativo"),
        ("em_negociacao", "Em negociação"),
        ("negociacao_sem_sucesso", "Negociação sem sucesso"),
    ]

    nome_completo = models.CharField(max_length=255)
    nif = models.CharField(max_length=9)

    inicio_protocolo_data = models.DateField(null=True, blank=True)
    inicio_protocolo_hora = models.TimeField(null=True, blank=True)
    fim_protocolo_data = models.DateField(null=True, blank=True)
    fim_protocolo_hora = models.TimeField(null=True, blank=True)

    estado = models.CharField(
        max_length=32,
        choices=ESTADO_CHOICES,
        default="ativo",
    )

    codigo_postal = models.CharField(max_length=10, blank=True)
    localidade = models.CharField(max_length=100, blank=True)
    concelho = models.CharField(max_length=100, blank=True)
    distrito = models.CharField(max_length=100, blank=True)
    rua_avenida = models.CharField(max_length=255, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    complemento = models.CharField(max_length=100, blank=True)
    observacoes_morada = models.TextField(blank=True)

    responsavel = models.CharField(max_length=255, blank=True)
    telefone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    fax = models.CharField(max_length=50, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Prestador"
        verbose_name_plural = "Prestadores"

    def __str__(self) -> str:
        return self.nome_completo


class PrestadorExameValor(models.Model):
    prestador = models.ForeignKey(
        Prestador, on_delete=models.CASCADE, related_name="exames_valores"
    )
    exame_nome = models.CharField("Exame", max_length=255, blank=True, null=True)
    valor = models.DecimalField(
        "Valor", max_digits=12, decimal_places=2, blank=True, null=True
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Exame e Valor"
        verbose_name_plural = "Exames e Valores"

    def __str__(self) -> str:
        return f"{self.prestador.nome_completo} - {self.exame_nome or 'Exame'}"

