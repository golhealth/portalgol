"""Resolução de nomes de atos para precificação de RealizacaoExameArbitro."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from exames.models import MarcacaoExame

from .models import PrestadorExameValor


def valor_para_ato(precos: dict[str, Decimal], nome: str) -> Decimal | None:
    if nome in precos:
        return precos[nome]
    alvo = nome.lower()
    for chave, valor in precos.items():
        if chave.lower() == alvo:
            return valor
    return None


def _nomes_da_marcacao(
    arbitro_id: int,
    prestador_id: int,
    cache: dict[tuple[int, int], list[str]] | None,
) -> list[str]:
    key = (arbitro_id, prestador_id)
    if cache is not None and key in cache:
        return cache[key]

    marcacao = (
        MarcacaoExame.objects.filter(arbitro_id=arbitro_id, prestador_id=prestador_id)
        .order_by("-data_hora_consulta", "-criado_em")
        .prefetch_related("itens")
        .first()
    )
    nomes: list[str] = []
    if marcacao:
        for it in marcacao.itens.all():
            n = (it.exame_nome or "").strip()
            if n:
                nomes.append(n)

    if cache is not None:
        cache[key] = nomes
    return nomes


def _unico_nome_preco_prestador(prestador_id: int) -> str | None:
    linhas = list(
        PrestadorExameValor.objects.filter(prestador_id=prestador_id)
        .exclude(exame_nome__isnull=True)
        .exclude(exame_nome__exact="")
        .exclude(valor__isnull=True)
    )
    if len(linhas) != 1:
        return None
    n = (linhas[0].exame_nome or "").strip()
    return n or None


def nomes_atos_para_precificacao(
    realizacao,
    *,
    cache_marcacao: dict[tuple[int, int], list[str]] | None = None,
    unico_nome_fallback: Callable[[], str | None] | None = None,
) -> list[str]:
    raw = (realizacao.exames_complementares or "").strip()
    if raw:
        return [x.strip() for x in raw.split(",") if x.strip()]

    nomes = _nomes_da_marcacao(
        realizacao.arbitro_id,
        realizacao.prestador_id,
        cache_marcacao,
    )
    if nomes:
        return nomes

    if unico_nome_fallback is not None:
        unico = unico_nome_fallback()
    else:
        unico = _unico_nome_preco_prestador(realizacao.prestador_id)
    if unico:
        return [unico]

    return []


def detalhes_e_subtotal(
    nomes_atos: list[str], precos: dict[str, Decimal]
) -> tuple[list[dict], Decimal]:
    detalhes: list[dict] = []
    subtotal = Decimal("0")
    for nome in nomes_atos:
        valor = valor_para_ato(precos, nome)
        if valor is not None:
            detalhes.append({"nome": nome, "valor": valor, "sem_preco": False})
            subtotal += valor
        else:
            detalhes.append({"nome": nome, "valor": None, "sem_preco": True})
    return detalhes, subtotal


def atos_display_para_linha(nomes_atos: list[str]) -> str:
    if nomes_atos:
        return ", ".join(nomes_atos)
    return "Exame médico (registo geral)"
