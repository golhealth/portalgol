from decimal import Decimal
from functools import partial

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.forms import formset_factory
from django.views.decorators.http import require_http_methods

from arbitro.models import Arbitro, RealizacaoExameArbitro
from prestador.realizacao_precos import (
    atos_display_para_linha,
    detalhes_e_subtotal,
    nomes_atos_para_precificacao,
)

from .forms import AssociacaoForm, ExameValorForm
from .models import Associacao, AssociacaoExameValor


def _precos_exames_por_associacao(associacao: Associacao) -> dict[str, Decimal]:
    precos: dict[str, Decimal] = {}
    for ev in AssociacaoExameValor.objects.filter(associacao=associacao).exclude(
        exame_nome__isnull=True
    ).exclude(exame_nome__exact=""):
        nome = (ev.exame_nome or "").strip()
        if nome and ev.valor is not None:
            precos[nome] = ev.valor
    return precos


def _unico_nome_preco_associacao(associacao_id: int) -> str | None:
    linhas = list(
        AssociacaoExameValor.objects.filter(associacao_id=associacao_id)
        .exclude(exame_nome__isnull=True)
        .exclude(exame_nome__exact="")
        .exclude(valor__isnull=True)
    )
    if len(linhas) != 1:
        return None
    n = (linhas[0].exame_nome or "").strip()
    return n or None


@login_required
def dashboard_associacoes(request):
    """
    Dashboard das associações de futebol.
    """
    total = Associacao.objects.count()
    ativas = Associacao.objects.filter(estado="ativo").count()

    associacoes = Associacao.objects.all().order_by("-criado_em")

    # Placeholder: ainda não há estados de negócio definidos para a associação.
    context = {
        "total_associacoes": total,
        "associacoes_ativas": ativas,
        "crescimento_percentual": 0,
        "associacoes_inativas": total - ativas,
        "associacoes": associacoes,
    }
    return render(request, "associacao/dashboard.html", context)


@login_required
def associacao_fatura_exames(request, pk: int):
    """
    Resumo de exames realizados pelos árbitros desta associação (Carregar exame),
    com prestador, atos e valores conforme a tabela de preços **desta associação**
    (o que se cobra à associação), não a tabela do prestador.
    """
    associacao = get_object_or_404(Associacao, pk=pk)
    realizacoes = (
        RealizacaoExameArbitro.objects.filter(arbitro__associacao_futebol=associacao)
        .select_related("arbitro", "arbitro__associacao_futebol", "prestador")
        .order_by("-data_realizacao", "-criado_em")
    )

    precos_associacao = _precos_exames_por_associacao(associacao)
    fallback_nome_unico = partial(_unico_nome_preco_associacao, associacao.pk)

    arbitros_associacao = list(
        Arbitro.objects.filter(associacao_futebol=associacao).order_by("nome_completo")
    )
    totais_por_arbitro: dict[int, dict] = {
        a.pk: {"arbitro": a, "total": Decimal("0"), "qtd_realizacoes": 0}
        for a in arbitros_associacao
    }

    linhas = []
    total_geral = Decimal("0")
    cache_marcacao: dict[tuple[int, int], list[str]] = {}

    for r in realizacoes:
        nomes_atos = nomes_atos_para_precificacao(
            r,
            cache_marcacao=cache_marcacao,
            unico_nome_fallback=fallback_nome_unico,
        )
        detalhes, subtotal = detalhes_e_subtotal(nomes_atos, precos_associacao)
        atos_display = atos_display_para_linha(nomes_atos)

        linhas.append(
            {
                "realizacao": r,
                "arbitro": r.arbitro,
                "prestador": r.prestador,
                "atos_display": atos_display,
                "detalhes": detalhes,
                "subtotal": subtotal,
            }
        )

        aid = r.arbitro_id
        if aid not in totais_por_arbitro:
            totais_por_arbitro[aid] = {
                "arbitro": r.arbitro,
                "total": Decimal("0"),
                "qtd_realizacoes": 0,
            }
        totais_por_arbitro[aid]["total"] += subtotal
        totais_por_arbitro[aid]["qtd_realizacoes"] += 1
        total_geral += subtotal

    resumo_arbitros = sorted(
        totais_por_arbitro.values(),
        key=lambda x: x["arbitro"].nome_completo.lower(),
    )

    return render(
        request,
        "associacao/fatura_exames.html",
        {
            "associacao": associacao,
            "linhas": linhas,
            "resumo_arbitros": resumo_arbitros,
            "total_arbitros": len(arbitros_associacao),
            "total_geral": total_geral,
            "tem_realizacoes": bool(linhas),
        },
    )


@login_required
def novo_associacao(request):
    if request.method == "POST":
        form = AssociacaoForm(request.POST)
        ExameValorFormSet = formset_factory(ExameValorForm, extra=1)
        exames_formset = ExameValorFormSet(request.POST, prefix="exames")

        if form.is_valid() and exames_formset.is_valid():
            associacao = form.save()

            for f in exames_formset:
                data = f.cleaned_data
                exame = data.get("exame_nome")
                exame_nome = exame.nome if exame else None
                valor = data.get("valor")

                # Guarda apenas linhas preenchidas
                if exame_nome or valor is not None:
                    AssociacaoExameValor.objects.create(
                        associacao=associacao,
                        exame_nome=exame_nome or None,
                        valor=valor,
                    )

            messages.success(request, "Associação registada com sucesso.")
            return redirect("associacao:dashboard")
    else:
        form = AssociacaoForm()
        ExameValorFormSet = formset_factory(ExameValorForm, extra=1)
        exames_formset = ExameValorFormSet(prefix="exames")

    return render(
        request,
        "associacao/novo.html",
        {"form": form, "exames": exames_formset},
    )


@login_required
def detalhe_associacao(request, pk: int):
    associacao = get_object_or_404(
        Associacao.objects.prefetch_related(
            Prefetch(
                "exames_valores",
                queryset=AssociacaoExameValor.objects.order_by("pk"),
            )
        ),
        pk=pk,
    )
    return render(
        request,
        "associacao/detalhe.html",
        {"associacao": associacao},
    )


@login_required
@require_http_methods(["GET", "POST"])
def editar_associacao(request, pk: int):
    associacao = get_object_or_404(Associacao, pk=pk)

    if request.method == "POST":
        form = AssociacaoForm(request.POST, instance=associacao)
        if form.is_valid():
            form.save()
            messages.success(request, "Associação atualizada com sucesso.")
            return redirect("associacao:dashboard")
    else:
        form = AssociacaoForm(instance=associacao)

    return render(
        request,
        "associacao/editar.html",
        {"form": form, "associacao": associacao},
    )


@login_required
@require_http_methods(["POST"])
def excluir_associacao(request, pk: int):
    associacao = get_object_or_404(Associacao, pk=pk)
    associacao.delete()
    messages.success(request, "Associação excluída com sucesso.")
    return redirect("associacao:dashboard")

