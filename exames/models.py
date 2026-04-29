from django.db import models


class Exame(models.Model):
    # Mantemos o mesmo model (para não quebrar relações), mas mudamos os
    # textos para o termo "Ato Médico" conforme pedido.
    nome = models.CharField("Nome do Ato Médico", max_length=255, unique=True)
    ativo = models.BooleanField("Ativo", default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ato Médico"
        verbose_name_plural = "Atos Médicos"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class MarcacaoExame(models.Model):
    epoca = models.ForeignKey(
        "core.Epoca",
        on_delete=models.CASCADE,
        related_name="marcacoes_exames",
    )
    associacao = models.ForeignKey(
        "associacao.Associacao",
        on_delete=models.CASCADE,
        related_name="marcacoes_exames",
    )
    arbitro = models.ForeignKey(
        "arbitro.Arbitro",
        on_delete=models.CASCADE,
        related_name="marcacoes_exames",
    )
    prestador = models.ForeignKey(
        "prestador.Prestador",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marcacoes_exames",
    )
    observacao = models.TextField("Observação", blank=True)
    data_hora_consulta = models.DateTimeField(
        "Data e hora da consulta",
        null=True,
        blank=True,
    )
    criado_em = models.DateTimeField("Marcado em", auto_now_add=True)

    class Meta:
        verbose_name = "Marcação de Exame"
        verbose_name_plural = "Marcações de Exames"
        ordering = ["-criado_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["epoca", "arbitro"],
                name="uniq_marcacao_epoca_arbitro",
            )
        ]

    def __str__(self) -> str:
        return f"{self.arbitro} - {self.epoca}"


class MarcacaoExameItem(models.Model):
    marcacao = models.ForeignKey(
        MarcacaoExame,
        on_delete=models.CASCADE,
        related_name="itens",
    )
    exame_nome = models.CharField("Exame", max_length=255)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Exame da Marcação"
        verbose_name_plural = "Exames da Marcação"
        ordering = ["exame_nome"]

    def __str__(self) -> str:
        return self.exame_nome

