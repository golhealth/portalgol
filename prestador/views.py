from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Prefetch, ProtectedError
from django.forms import formset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from arbitro.models import RealizacaoExameArbitro
from exames.models import Exame

from .forms import ExameValorForm, PrestadorForm
from .models import Prestador, PrestadorExameValor
from .realizacao_precos import (
    atos_display_para_linha,
    detalhes_e_subtotal,
    nomes_atos_para_precificacao,
)


def _exames_valores_iniciais(prestador: Prestador):
    rows = []
    for ev in prestador.exames_valores.all().order_by("pk"):
        ex_obj = None
        if ev.exame_nome and str(ev.exame_nome).strip():
            ex_obj = Exame.objects.filter(nome__iexact=ev.exame_nome.strip()).first()
        rows.append({"exame_nome": ex_obj, "valor": ev.valor})
    return rows


@login_required
def prestador_atos_realizados(request, pk: int):
    """
    Lista atos realizados (exames carregados) neste prestador, por árbitro,
    com valores conforme a tabela de preços do prestador.
    """
    prestador = get_object_or_404(Prestador, pk=pk)
    realizacoes = (
        RealizacaoExameArbitro.objects.filter(prestador=prestador)
        .select_related("arbitro", "arbitro__associacao_futebol")
        .order_by("-data_realizacao", "-criado_em")
    )

    precos_por_exame: dict[str, Decimal] = {}
    for ev in PrestadorExameValor.objects.filter(prestador=prestador).exclude(
        exame_nome__isnull=True
    ).exclude(exame_nome__exact=""):
        nome = (ev.exame_nome or "").strip()
        if nome and ev.valor is not None:
            precos_por_exame[nome] = ev.valor

    linhas = []
    totais_por_arbitro: dict[int, dict] = {}
    total_geral = Decimal("0")
    cache_marcacao: dict[tuple[int, int], list[str]] = {}

    for r in realizacoes:
        nomes_atos = nomes_atos_para_precificacao(
            r, cache_marcacao=cache_marcacao
        )
        detalhes, subtotal = detalhes_e_subtotal(nomes_atos, precos_por_exame)
        atos_display = atos_display_para_linha(nomes_atos)

        linhas.append(
            {
                "realizacao": r,
                "arbitro": r.arbitro,
                "associacao": r.arbitro.associacao_futebol,
                "atos_display": atos_display,
                "detalhes": detalhes,
                "subtotal": subtotal,
            }
        )

        aid = r.arbitro_id
        if aid not in totais_por_arbitro:
            totais_por_arbitro[aid] = {
                "arbitro": r.arbitro,
                "associacao": r.arbitro.associacao_futebol,
                "total": Decimal("0"),
            }
        totais_por_arbitro[aid]["total"] += subtotal
        total_geral += subtotal

    resumo_arbitros = sorted(
        totais_por_arbitro.values(),
        key=lambda x: x["arbitro"].nome_completo.lower(),
    )

    return render(
        request,
        "prestador/atos_realizados.html",
        {
            "prestador": prestador,
            "linhas": linhas,
            "resumo_arbitros": resumo_arbitros,
            "total_geral": total_geral,
            "tem_realizacoes": bool(linhas),
        },
    )


@login_required
def lista_prestadores(request):
    """Lista todos os prestadores registados."""
    prestadores = Prestador.objects.order_by("-criado_em")
    return render(
        request,
        "prestador/lista.html",
        {"prestadores": prestadores},
    )


@login_required
def detalhe_prestador(request, pk: int):
    prestador = get_object_or_404(
        Prestador.objects.prefetch_related(
            Prefetch(
                "exames_valores",
                queryset=PrestadorExameValor.objects.order_by("pk"),
            )
        ),
        pk=pk,
    )
    return render(
        request,
        "prestador/detalhe.html",
        {"prestador": prestador},
    )


@login_required
def editar_prestador(request, pk: int):
    prestador = get_object_or_404(Prestador, pk=pk)
    ExameValorFormSet = formset_factory(ExameValorForm, extra=1)

    if request.method == "POST":
        form = PrestadorForm(request.POST, instance=prestador)
        exames_formset = ExameValorFormSet(request.POST, prefix="exames")

        if form.is_valid() and exames_formset.is_valid():
            with transaction.atomic():
                form.save()
                prestador.exames_valores.all().delete()
                for f in exames_formset:
                    data = f.cleaned_data
                    if not data:
                        continue
                    exame = data.get("exame_nome")
                    exame_nome = exame.nome if exame else None
                    valor = data.get("valor")
                    if exame_nome or valor is not None:
                        PrestadorExameValor.objects.create(
                            prestador=prestador,
                            exame_nome=exame_nome or None,
                            valor=valor,
                        )
            messages.success(request, "Prestador atualizado com sucesso.")
            return redirect("prestador:detalhe", pk=prestador.pk)

        errors = form.errors
    else:
        form = PrestadorForm(instance=prestador)
        iniciais = _exames_valores_iniciais(prestador)
        if iniciais:
            exames_formset = ExameValorFormSet(prefix="exames", initial=iniciais)
        else:
            exames_formset = ExameValorFormSet(prefix="exames")
        errors = {}

    return render(
        request,
        "prestador/novo.html",
        {
            "form": form,
            "errors": errors,
            "exames": exames_formset,
            "is_edit": True,
            "prestador": prestador,
        },
    )


@login_required
@require_POST
def excluir_prestador(request, pk: int):
    prestador = get_object_or_404(Prestador, pk=pk)
    nome = prestador.nome_completo
    try:
        prestador.delete()
    except ProtectedError:
        messages.error(
            request,
            "Não é possível excluir este prestador: existem registos de exames realizados "
            "ou outras dependências ligadas a ele.",
        )
        return redirect("prestador:lista")
    messages.success(request, f"Prestador \"{nome}\" removido com sucesso.")
    return redirect("prestador:lista")


@login_required
def dashboard_prestadores(request):
    """
    Dashboard de Prestadores.
    Usa contagens reais do modelo Prestador.
    """
    total = Prestador.objects.count()
    ativos = Prestador.objects.filter(estado="ativo").count()
    conformes = Prestador.objects.filter(estado="ativo").count()  # placeholder
    em_negociacao = Prestador.objects.filter(estado="em_negociacao").count()
    inativos = Prestador.objects.filter(estado__in=["inativo", "negociacao_sem_sucesso"]).count()

    context = {
        "total_prestadores": total,
        "prestadores_ativos": ativos,
        "prestadores_conformes": conformes,
        "prestadores_em_negociacao": em_negociacao,
        "prestadores_inativos": inativos,
        "crescimento_percentual": 0,
    }
    return render(request, "prestador/dashboard.html", context)


@login_required
def novo_prestador(request):
    """
    Página de criação de novo prestador com o layout fornecido.
    """
    if request.method == "POST":
        form = PrestadorForm(request.POST)
        ExameValorFormSet = formset_factory(ExameValorForm, extra=1)
        exames_formset = ExameValorFormSet(request.POST, prefix="exames")

        if form.is_valid() and exames_formset.is_valid():
            prestador = form.save()

            for f in exames_formset:
                data = f.cleaned_data
                exame = data.get("exame_nome")
                exame_nome = exame.nome if exame else None
                valor = data.get("valor")

                if exame_nome or valor is not None:
                    PrestadorExameValor.objects.create(
                        prestador=prestador,
                        exame_nome=exame_nome or None,
                        valor=valor,
                    )

            messages.success(request, "Prestador registado com sucesso.")
            return redirect("prestador:dashboard")

        errors = form.errors
    else:
        form = PrestadorForm()
        ExameValorFormSet = formset_factory(ExameValorForm, extra=1)
        exames_formset = ExameValorFormSet(prefix="exames")
        errors = {}

    return render(
        request,
        "prestador/novo.html",
        {
            "form": form,
            "errors": errors,
            "exames": exames_formset,
        },
    )
