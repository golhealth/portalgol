from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import ExameForm, MarcacaoExameEditForm
from .models import Exame, MarcacaoExame, MarcacaoExameItem
from arbitro.models import Arbitro
from core.models import Epoca, EpocaArbitro, EpocaAssociacao
from prestador.models import Prestador, PrestadorExameValor


@login_required
def novo_ato(request):
    """
    Permite registar um novo ato médico (nome) que depois fica disponível
    no "Registo de Associação" para seleção.
    """
    if request.method == "POST":
        form = ExameForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Ato médico registado com sucesso.")
            return redirect("exames:dashboard")
    else:
        form = ExameForm()

    return render(request, "exames/novo.html", {"form": form})


@login_required
def dashboard_exames(request):
    exams = Exame.objects.all().order_by("nome")
    total_exames = Exame.objects.count()
    exames_ativos = Exame.objects.filter(ativo=True).count()
    exames_inativos = total_exames - exames_ativos
    epoca_atual = Epoca.objects.filter(ativo=True).order_by("-criado_em").first()
    epocas = Epoca.objects.all().order_by("-ativo", "nome")

    return render(
        request,
        "exames/dashboard.html",
        {
            "exams": exams,
            "total_exames": total_exames,
            "exames_ativos": exames_ativos,
            "exames_inativos": exames_inativos,
            "epoca_atual": epoca_atual,
            "epocas": epocas,
        },
    )


@login_required
def editar_exame(request, pk: int):
    exame = get_object_or_404(Exame, pk=pk)

    if request.method == "POST":
        form = ExameForm(request.POST, instance=exame)
        if form.is_valid():
            form.save()
            messages.success(request, "Ato médico atualizado com sucesso.")
            return redirect("exames:dashboard")
    else:
        form = ExameForm(instance=exame)

    return render(request, "exames/editar.html", {"form": form, "exame": exame})


@login_required
def novo_ato_ajax(request):
    """
    Cria um novo Ato Médico via AJAX (modal no dashboard).
    Espera POST com `nome` e `ativo`.
    """
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método não permitido."}, status=405)

    form = ExameForm(request.POST)
    if not form.is_valid():
        nome_errs = form.errors.get("nome", [])
        return JsonResponse({"ok": False, "errors": {"nome": nome_errs}}, status=400)

    exame = form.save()
    return JsonResponse({"ok": True, "id": exame.pk, "nome": exame.nome})


@login_required
def marcar_exames_dashboard(request):
    epocas = Epoca.objects.order_by("-ativo", "nome")
    prestadores = Prestador.objects.order_by("nome_completo")

    epoca_id = request.GET.get("epoca")
    associacao_id = request.GET.get("associacao")

    epoca_selecionada = None
    associacao_selecionada = None
    associacoes = []
    arbitros_pendentes = []

    if epoca_id:
        epoca_selecionada = Epoca.objects.filter(pk=epoca_id).first()
        if epoca_selecionada:
            associacoes = (
                EpocaAssociacao.objects.filter(epoca=epoca_selecionada)
                .select_related("associacao")
                .order_by("associacao__nome_completo")
            )

    if epoca_selecionada and associacao_id:
        associacao_selecionada = (
            EpocaAssociacao.objects.filter(
                epoca=epoca_selecionada,
                associacao_id=associacao_id,
            )
            .select_related("associacao")
            .first()
        )
        if associacao_selecionada:
            arbitros_qs = Arbitro.objects.filter(
                epocas__epoca=epoca_selecionada,
                associacao_futebol=associacao_selecionada.associacao,
            ).distinct()

            arbitros_pendentes = arbitros_qs.exclude(
                marcacoes_exames__epoca=epoca_selecionada
            ).order_by("nome_completo")

    return render(
        request,
        "exames/marcar_exames.html",
        {
            "epocas": epocas,
            "prestadores": prestadores,
            "epoca_selecionada": epoca_selecionada,
            "associacoes": associacoes,
            "associacao_selecionada": associacao_selecionada.associacao if associacao_selecionada else None,
            "arbitros_pendentes": arbitros_pendentes,
        },
    )


@login_required
@require_POST
def marcar_exame_ajax(request):
    epoca_id = request.POST.get("epoca_id")
    associacao_id = request.POST.get("associacao_id")
    arbitro_id = request.POST.get("arbitro_id")
    prestador_id = request.POST.get("prestador_id")

    if not all([epoca_id, associacao_id, arbitro_id, prestador_id]):
        return JsonResponse({"ok": False, "error": "Dados incompletos."}, status=400)

    epoca = Epoca.objects.filter(pk=epoca_id).first()
    if not epoca:
        return JsonResponse({"ok": False, "error": "Época inválida."}, status=404)

    epoca_assoc = EpocaAssociacao.objects.filter(
        epoca=epoca,
        associacao_id=associacao_id,
    ).first()
    if not epoca_assoc:
        return JsonResponse({"ok": False, "error": "Associação não está vinculada à época."}, status=400)

    arbitro = Arbitro.objects.filter(
        pk=arbitro_id,
        associacao_futebol_id=associacao_id,
    ).first()
    if not arbitro:
        return JsonResponse(
            {"ok": False, "error": "Árbitro inválido ou não pertence a esta associação."},
            status=400,
        )
    EpocaArbitro.objects.get_or_create(epoca=epoca, arbitro=arbitro)

    prestador = Prestador.objects.filter(pk=prestador_id).first()
    if not prestador:
        return JsonResponse({"ok": False, "error": "Prestador inválido."}, status=404)

    exames_selecionados = [e.strip() for e in request.POST.getlist("exames[]") if e and e.strip()]
    if not exames_selecionados:
        return JsonResponse({"ok": False, "error": "Selecione pelo menos um exame."}, status=400)

    exames_disponiveis = set(
        PrestadorExameValor.objects.filter(prestador=prestador)
        .exclude(exame_nome__isnull=True)
        .exclude(exame_nome__exact="")
        .values_list("exame_nome", flat=True)
    )
    if not exames_disponiveis:
        return JsonResponse(
            {"ok": False, "error": "Este prestador não possui exames cadastrados."},
            status=400,
        )

    exames_invalidos = [e for e in exames_selecionados if e not in exames_disponiveis]
    if exames_invalidos:
        return JsonResponse(
            {"ok": False, "error": "Há exames inválidos para este prestador."},
            status=400,
        )

    raw_dh = (request.POST.get("data_hora_consulta") or "").strip()
    if not raw_dh:
        return JsonResponse(
            {"ok": False, "error": "Indique a data e hora da consulta."},
            status=400,
        )
    try:
        dt_naive = datetime.fromisoformat(raw_dh)
    except ValueError:
        return JsonResponse(
            {"ok": False, "error": "Data e hora da consulta inválidas."},
            status=400,
        )
    if timezone.is_naive(dt_naive):
        data_hora_consulta = timezone.make_aware(
            dt_naive, timezone.get_current_timezone()
        )
    else:
        data_hora_consulta = dt_naive

    marcacao, created = MarcacaoExame.objects.get_or_create(
        epoca=epoca,
        arbitro=arbitro,
        defaults={
            "associacao": epoca_assoc.associacao,
            "prestador": prestador,
            "observacao": request.POST.get("observacao", "").strip(),
            "data_hora_consulta": data_hora_consulta,
        },
    )
    if not created:
        return JsonResponse({"ok": False, "error": "Este árbitro já foi marcado nesta época."}, status=400)

    for exame_nome in sorted(set(exames_selecionados)):
        MarcacaoExameItem.objects.create(
            marcacao=marcacao,
            exame_nome=exame_nome,
        )

    return JsonResponse(
        {
            "ok": True,
            "message": "Exame marcado com sucesso.",
            "arbitro_id": arbitro.pk,
        }
    )


@login_required
@require_GET
def prestador_exames_ajax(request):
    prestador_id = request.GET.get("prestador_id")
    if not prestador_id:
        return JsonResponse({"ok": False, "error": "Prestador não informado."}, status=400)

    prestador = Prestador.objects.filter(pk=prestador_id).first()
    if not prestador:
        return JsonResponse({"ok": False, "error": "Prestador inválido."}, status=404)

    exames = sorted(
        set(
            PrestadorExameValor.objects.filter(prestador=prestador)
            .exclude(exame_nome__isnull=True)
            .exclude(exame_nome__exact="")
            .values_list("exame_nome", flat=True)
        )
    )

    return JsonResponse({"ok": True, "exames": exames})


@login_required
def exames_marcados(request):
    """
    Lista exames já marcados (árbitro + época + associação + prestador).
    Filtros opcionais: ?epoca=&associacao=
    """
    epocas = Epoca.objects.order_by("-ativo", "nome")

    epoca_id = request.GET.get("epoca")
    associacao_id = request.GET.get("associacao")

    epoca_selecionada = None
    associacoes = []
    associacao_selecionada = None

    marcacoes = MarcacaoExame.objects.select_related(
        "epoca",
        "associacao",
        "arbitro",
        "arbitro__categoria",
        "prestador",
    ).prefetch_related("itens").order_by(
        F("data_hora_consulta").desc(nulls_last=True),
        "-criado_em",
    )

    if epoca_id:
        epoca_selecionada = Epoca.objects.filter(pk=epoca_id).first()
        if epoca_selecionada:
            associacoes = (
                EpocaAssociacao.objects.filter(epoca=epoca_selecionada)
                .select_related("associacao")
                .order_by("associacao__nome_completo")
            )
            marcacoes = marcacoes.filter(epoca=epoca_selecionada)

    if epoca_selecionada and associacao_id:
        ea = (
            EpocaAssociacao.objects.filter(
                epoca=epoca_selecionada,
                associacao_id=associacao_id,
            )
            .select_related("associacao")
            .first()
        )
        if ea:
            associacao_selecionada = ea.associacao
            marcacoes = marcacoes.filter(associacao=associacao_selecionada)

    total_marcacoes = marcacoes.count()

    return render(
        request,
        "exames/exames_marcados.html",
        {
            "epocas": epocas,
            "epoca_selecionada": epoca_selecionada,
            "associacoes": associacoes,
            "associacao_selecionada": associacao_selecionada,
            "marcacoes": marcacoes,
            "total_marcacoes": total_marcacoes,
        },
    )


@login_required
def marcar_exame_detalhe(request, pk: int):
    marcacao = get_object_or_404(
        MarcacaoExame.objects.select_related(
            "epoca",
            "associacao",
            "arbitro",
            "arbitro__categoria",
            "prestador",
        ).prefetch_related("itens"),
        pk=pk,
    )
    voltar = reverse("exames:exames_marcados")
    q = []
    if marcacao.epoca_id:
        q.append(f"epoca={marcacao.epoca_id}")
    if marcacao.associacao_id:
        q.append(f"associacao={marcacao.associacao_id}")
    if q:
        voltar = f"{voltar}?{'&'.join(q)}"
    return render(
        request,
        "exames/marcacao_detalhe.html",
        {"marcacao": marcacao, "voltar_url": voltar},
    )


@login_required
@require_http_methods(["GET", "POST"])
def marcar_exame_editar(request, pk: int):
    marcacao = get_object_or_404(
        MarcacaoExame.objects.select_related(
            "epoca", "associacao", "arbitro", "arbitro__categoria", "prestador"
        ).prefetch_related("itens"),
        pk=pk,
    )
    voltar = reverse("exames:exames_marcados")
    q = []
    if marcacao.epoca_id:
        q.append(f"epoca={marcacao.epoca_id}")
    if marcacao.associacao_id:
        q.append(f"associacao={marcacao.associacao_id}")
    if q:
        voltar = f"{voltar}?{'&'.join(q)}"

    errors: list[str] = []
    if request.method == "POST":
        form = MarcacaoExameEditForm(request.POST, instance=marcacao)
        exames_sel = [
            e.strip()
            for e in request.POST.getlist("exames[]")
            if e and str(e).strip()
        ]
        if not exames_sel:
            errors.append("Selecione pelo menos um exame.")

        prestador = None
        if form.is_valid():
            prestador = form.cleaned_data.get("prestador")
            if prestador:
                disp = set(
                    PrestadorExameValor.objects.filter(prestador=prestador)
                    .exclude(exame_nome__isnull=True)
                    .exclude(exame_nome__exact="")
                    .values_list("exame_nome", flat=True)
                )
                if not disp:
                    errors.append("Este prestador não possui exames cadastrados.")
                elif any(x not in disp for x in exames_sel):
                    errors.append("Há exames inválidos para o prestador selecionado.")
            else:
                errors.append("Selecione um prestador.")

        if form.is_valid() and not errors:
            with transaction.atomic():
                m = form.save()
                m.itens.all().delete()
                for nome in sorted(set(exames_sel)):
                    MarcacaoExameItem.objects.create(marcacao=m, exame_nome=nome)
            messages.success(request, "Consulta atualizada com sucesso.")
            return redirect(voltar)
    else:
        form = MarcacaoExameEditForm(instance=marcacao)

    if request.method == "POST":
        pid = request.POST.get("prestador")
        prestador_lista = (
            Prestador.objects.filter(pk=pid).first() if pid else marcacao.prestador
        )
        exames_marcados_nomes = [
            e.strip()
            for e in request.POST.getlist("exames[]")
            if e and str(e).strip()
        ]
    else:
        prestador_lista = marcacao.prestador
        exames_marcados_nomes = list(
            marcacao.itens.values_list("exame_nome", flat=True)
        )

    exames_disponiveis = []
    if prestador_lista:
        exames_disponiveis = sorted(
            set(
                PrestadorExameValor.objects.filter(prestador=prestador_lista)
                .exclude(exame_nome__isnull=True)
                .exclude(exame_nome__exact="")
                .values_list("exame_nome", flat=True)
            )
        )

    return render(
        request,
        "exames/marcacao_editar.html",
        {
            "marcacao": marcacao,
            "form": form,
            "voltar_url": voltar,
            "exames_disponiveis": exames_disponiveis,
            "exames_marcados": exames_marcados_nomes,
            "edit_errors": errors,
        },
    )


@login_required
@require_POST
def marcar_exame_excluir(request, pk: int):
    marcacao = get_object_or_404(MarcacaoExame, pk=pk)
    next_url = request.POST.get("next") or reverse("exames:exames_marcados")
    nome_arbitro = marcacao.arbitro.nome_completo
    marcacao.delete()
    messages.success(
        request,
        f"Consulta de {nome_arbitro} removida. O árbitro volta à lista de não marcados.",
    )
    return redirect(next_url)

