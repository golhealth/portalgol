from django.db import models


class Associacao(models.Model):
    ESTADO_CHOICES = [
        ("ativo", "Ativo"),
        ("inativo", "Inativo"),
        ("em_negociacao", "Em negociação"),
        ("negociacao_sem_sucesso", "Negociação sem sucesso"),
    ]

    nome_completo = models.CharField("Nome Completo", max_length=255, null=True, blank=True)
    nif = models.CharField("NIF", max_length=9, null=True, blank=True)

    inicio_protocolo_data = models.DateField(null=True, blank=True)
    inicio_protocolo_hora = models.TimeField(null=True, blank=True)
    fim_protocolo_data = models.DateField(null=True, blank=True)
    fim_protocolo_hora = models.TimeField(null=True, blank=True)

    estado = models.CharField(
        max_length=32, choices=ESTADO_CHOICES, default="ativo"
    )

    # Morada
    rua_avenida = models.CharField("Rua / Avenida", max_length=255, null=True, blank=True)
    numero = models.CharField("Número da Porta", max_length=20, null=True, blank=True)
    complemento = models.CharField("Complemento", max_length=255, null=True, blank=True)
    codigo_postal = models.CharField("Código Postal", max_length=10, null=True, blank=True)
    localidade = models.CharField("Localidade", max_length=100, null=True, blank=True)
    concelho = models.CharField("Concelho", max_length=100, null=True, blank=True)
    distrito = models.CharField("Distrito", max_length=100, null=True, blank=True)

    # Contactos
    responsavel = models.CharField("Responsável", max_length=255, null=True, blank=True)
    telefone = models.CharField("Telefone", max_length=50, null=True, blank=True)
    email = models.EmailField("E-mail", null=True, blank=True)
    fax = models.CharField("Fax", max_length=50, null=True, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Associação"
        verbose_name_plural = "Associações"

    def __str__(self) -> str:
        return self.nome_completo


class AssociacaoExameValor(models.Model):
    associacao = models.ForeignKey(
        Associacao, on_delete=models.CASCADE, related_name="exames_valores"
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
        return f"{self.associacao.nome_completo} - {self.exame_nome or 'Exame'}"

