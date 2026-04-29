import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import ArbitroForm
from .models import Arbitro, RealizacaoExameArbitro
from core.models import Categoria, Epoca, EpocaAssociacao
from exames.models import MarcacaoExame
from prestador.models import Prestador
from core.forms import CategoriaForm, ModalidadeForm

_SORT_COLUNAS_LISTA_ARBITROS = frozenset({"nome", "categoria", "associacao"})


def _lista_arbitros_query_ordenar(
    col_alvo: str, search_q: str, sort_col: str, sort_dir: str
) -> str:
    new_dir = "desc" if (sort_col == col_alvo and sort_dir == "asc") else "asc"
    params: list[tuple[str, str]] = [("ordenar", col_alvo), ("dir", new_dir)]
    if search_q:
        params.insert(0, ("q", search_q))
    return urlencode(params)


def _extrair_rua_avenida(payload: dict) -> str:
    """
    Extrai rua/avenida de respostas variáveis da API de CP.
    A API pode devolver lista de strings, lista de objetos ou campos alternativos.
    """
    # 1) Formato mais comum: `ruas` (lista)
    ruas = payload.get("ruas") or payload.get("Ruas") or []
    if isinstance(ruas, list) and ruas:
        first = ruas[0]
        if isinstance(first, str):
            return first.strip()
        if isinstance(first, dict):
            for key in (
                "rua",
                "Rua",
                "nome",
                "Nome",
                "designacao",
                "Designacao",
                "arruamento",
                "Arruamento",
                "morada",
                "Morada",
            ):
                val = first.get(key)
                if val:
                    return str(val).strip()

    # 2) Formato alternativo observado: `partes` com `Artéria`
    partes = payload.get("partes") or payload.get("Partes") or []
    if isinstance(partes, list) and partes:
        first = partes[0]
        if isinstance(first, dict):
            for key in (
                "Artéria",
                "Arteria",
                "artéria",
                "arteria",
                "Art\u00e9ria",
                "art\u00e9ria",
                "Rua",
                "rua",
                "Arruamento",
                "arruamento",
            ):
                val = first.get(key)
                if val:
                    return str(val).strip()

    # 3) Campos diretos alternativos
    for key in (
        "Rua",
        "rua",
        "Arruamento",
        "arruamento",
        "Morada",
        "morada",
        "Via",
        "via",
        "Toponimo",
        "toponimo",
        "Designacao",
        "designacao",
    ):
        val = payload.get(key)
        if val:
            return str(val).strip()

    return ""


@login_required
def dashboard_arbitros(request):
    """
    Dashboard de Árbitros.
    Por enquanto usa agregações simples sobre o modelo Arbitro,
    inspirado no layout PHP original.
    """
    total_arbitros = Arbitro.objects.count()
    arbitros_ativos = Arbitro.objects.filter(ativo=True).count()

    # Placeholders até existir módulo de exames / épocas
    exames_pendentes = 0
    crescimento_percentual = 0

    categorias_stats_qs = (
        Categoria.objects.annotate(count=Count("arbitros"))
        .values("nome", "count")
        .order_by("nome")
    )
    categorias_stats = list(categorias_stats_qs)

    context = {
        "total_arbitros": total_arbitros,
        "arbitros_ativos": arbitros_ativos,
        "exames_pendentes": exames_pendentes,
        "crescimento_percentual": crescimento_percentual,
        "categorias_stats": categorias_stats,
    }
    return render(request, "arbitro/dashboard.html", context)


@login_required
def lista_arbitros(request):
    """
    Lista completa de árbitros (sem depender do admin Django).
    Pesquisa opcional: ?q= (nome, categoria ou associação).
    Ordenação: ?ordenar=nome|categoria|associacao&dir=asc|dir=desc
    """
    search_q = (request.GET.get("q") or "").strip()
    sort_col = (request.GET.get("ordenar") or "").strip().lower()
    sort_dir = (request.GET.get("dir") or "asc").strip().lower()
    if sort_dir not in ("asc", "desc"):
        sort_dir = "asc"
    if sort_col not in _SORT_COLUNAS_LISTA_ARBITROS:
        sort_col = ""

    arbitros = Arbitro.objects.select_related(
        "categoria", "associacao_futebol", "modalidade"
    )
    if sort_col == "nome":
        primary = "nome_completo" if sort_dir == "asc" else "-nome_completo"
        arbitros = arbitros.order_by(primary, "-criado_em")
    elif sort_col == "categoria":
        primary = "categoria__nome" if sort_dir == "asc" else "-categoria__nome"
        arbitros = arbitros.order_by(primary, "-criado_em")
    elif sort_col == "associacao":
        primary = (
            "associacao_futebol__nome_completo"
            if sort_dir == "asc"
            else "-associacao_futebol__nome_completo"
        )
        arbitros = arbitros.order_by(primary, "-criado_em")
    else:
        arbitros = arbitros.order_by("-criado_em")

    if search_q:
        arbitros = arbitros.filter(
            Q(nome_completo__icontains=search_q)
            | Q(categoria__nome__icontains=search_q)
            | Q(associacao_futebol__nome_completo__icontains=search_q)
        )

    sort_preserve_suffix = (
        "&" + urlencode({"ordenar": sort_col, "dir": sort_dir}) if sort_col else ""
    )

    return render(
        request,
        "arbitro/lista.html",
        {
            "arbitros": arbitros,
            "search_q": search_q,
            "sort_col": sort_col,
            "sort_dir": sort_dir,
            "sort_qs_nome": _lista_arbitros_query_ordenar(
                "nome", search_q, sort_col, sort_dir
            ),
            "sort_qs_categoria": _lista_arbitros_query_ordenar(
                "categoria", search_q, sort_col, sort_dir
            ),
            "sort_qs_associacao": _lista_arbitros_query_ordenar(
                "associacao", search_q, sort_col, sort_dir
            ),
            "sort_preserve_suffix": sort_preserve_suffix,
        },
    )


@login_required
def detalhe_arbitro(request, pk: int):
    arbitro = get_object_or_404(
        Arbitro.objects.select_related(
            "categoria", "associacao_futebol", "modalidade"
        ),
        pk=pk,
    )
    epoca_ativa = Epoca.objects.filter(ativo=True).order_by("-criado_em").first()
    marcacoes_historico = list(
        MarcacaoExame.objects.filter(arbitro=arbitro)
        .select_related("prestador", "epoca", "associacao")
        .prefetch_related("itens")
        .order_by("-data_hora_consulta", "-criado_em")[:100]
    )

    today = timezone.now().date()
    dias_proximo_exame = None
    progress_exame_anual = 0
    data_limite_exame = None
    exame_anual_atrasado = False
    dias_atraso_exame = 0
    if arbitro.data_ultimo_exame:
        ultimo = arbitro.data_ultimo_exame
        data_limite_exame = ultimo + timedelta(days=365)
        delta_fim = (data_limite_exame - today).days
        if delta_fim < 0:
            exame_anual_atrasado = True
            dias_atraso_exame = abs(delta_fim)
            dias_proximo_exame = 0
            progress_exame_anual = 100
        else:
            dias_proximo_exame = delta_fim
            elapsed = (today - ultimo).days
            if elapsed < 0:
                elapsed = 0
            progress_exame_anual = min(100, max(0, int((elapsed / 365) * 100)))

    pode_agendar_modal = False
    if epoca_ativa and arbitro.associacao_futebol_id:
        pode_agendar_modal = EpocaAssociacao.objects.filter(
            epoca=epoca_ativa,
            associacao_id=arbitro.associacao_futebol_id,
        ).exists()

    prestadores = Prestador.objects.order_by("nome_completo")
    realizacoes_exame = list(
        RealizacaoExameArbitro.objects.filter(arbitro=arbitro)
        .select_related("prestador")
        .order_by("-criado_em")[:50]
    )

    prefill_carregar = None
    if marcacoes_historico:
        ultima_m = marcacoes_historico[0]
        if ultima_m.prestador_id and ultima_m.data_hora_consulta:
            nomes_atos = [
                it.exame_nome.strip()
                for it in ultima_m.itens.all()
                if (it.exame_nome or "").strip()
            ]
            prefill_carregar = {
                "marcacao_id": ultima_m.id,
                "data_realizacao": ultima_m.data_hora_consulta.date().isoformat(),
                "prestador_id": ultima_m.prestador_id,
                "exames_realizados": ", ".join(nomes_atos),
            }
    prefill_carregar_exame_json = json.dumps(prefill_carregar)

    return render(
        request,
        "arbitro/detalhe.html",
        {
            "arbitro": arbitro,
            "epoca_ativa": epoca_ativa,
            "marcacoes_historico": marcacoes_historico,
            "realizacoes_exame": realizacoes_exame,
            "dias_proximo_exame": dias_proximo_exame,
            "progress_exame_anual": progress_exame_anual,
            "data_limite_exame": data_limite_exame,
            "exame_anual_atrasado": exame_anual_atrasado,
            "dias_atraso_exame": dias_atraso_exame,
            "pode_agendar_modal": pode_agendar_modal,
            "prestadores": prestadores,
            "prefill_carregar_exame_json": prefill_carregar_exame_json,
            "marcar_exame_ajax_url": reverse("exames:marcar_exame_ajax"),
            "prestador_exames_ajax_url": reverse("exames:prestador_exames_ajax"),
            "carregar_exame_ajax_url": reverse("arbitro:carregar_exame_ajax"),
            "atualizar_estado_aptidao_ajax_url": reverse(
                "arbitro:atualizar_estado_aptidao_ajax"
            ),
            "estado_aptidao_choices": Arbitro.ESTADO_APTIDAO_CHOICES,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def editar_arbitro(request, pk: int):
    arbitro = get_object_or_404(Arbitro, pk=pk)

    if request.method == "POST":
        form = ArbitroForm(request.POST, instance=arbitro)
        if form.is_valid():
            form.save()
            messages.success(request, "Árbitro atualizado com sucesso.")
            return redirect("arbitro:lista")
    else:
        form = ArbitroForm(instance=arbitro)

    return render(request, "arbitro/editar.html", {"form": form, "arbitro": arbitro})


@login_required
@require_POST
def excluir_arbitro(request, pk: int):
    arbitro = get_object_or_404(Arbitro, pk=pk)
    arbitro.delete()
    messages.success(request, "Árbitro excluído com sucesso.")
    return redirect("arbitro:lista")


@login_required
def novo_arbitro(request):
    """
    Página de registo de novo árbitro.
    Usa o layout fornecido e o ArbitroForm.
    """
    if request.method == "POST":
        form = ArbitroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Árbitro registado com sucesso.")
            return redirect("arbitro:dashboard")
    else:
        form = ArbitroForm()

    categoria_form = CategoriaForm()
    modalidade_form = ModalidadeForm()
    return render(
        request,
        "arbitro/novo.html",
        {
            "form": form,
            "categoria_form": categoria_form,
            "modalidade_form": modalidade_form,
        },
    )


def _normalizar_codigo_postal(valor: str) -> str | None:
    """
    Normaliza Portugal CP em formato `NNNN-NNN` (7 dígitos).
    Ex: '1950449' ou '1950-449' -> '1950-449'
    """
    if not valor:
        return None
    digits = re.sub(r"\D+", "", str(valor))
    if len(digits) != 7:
        return None
    return f"{digits[:4]}-{digits[4:]}"


@login_required
@require_GET
def lookup_codigo_postal(request):
    """
    Devolve localidade e rua por código postal (Portugal).

    Fonte: https://json.geoapi.pt/cp/{cp}
    """
    raw = request.GET.get("codigo_postal", "")
    cp = _normalizar_codigo_postal(raw)
    if not cp:
        return JsonResponse({"error": "Código postal inválido."}, status=400)

    cache_key = f"cp_lookup:{cp}"
    cached = cache.get(cache_key)
    if isinstance(cached, dict) and cached.get("codigo_postal"):
        return JsonResponse(cached)

    payload = None
    cp_digits = cp.replace("-", "")
    urls = [
        f"https://json.geoapi.pt/cp/{cp}",
        f"https://json.geoapi.pt/cp/{cp}/",
        f"https://json.geoapi.pt/cp/{cp_digits}",
    ]

    last_http_error = None
    for url in urls:
        try:
            req = Request(
                url,
                headers={
                    "User-Agent": "gol-health/1.0 (+postal-lookup)",
                    "Accept": "application/json",
                },
            )
            with urlopen(req, timeout=8) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
                if isinstance(payload, dict):
                    break
                payload = None
        except HTTPError as exc:
            last_http_error = exc
            # 404 pode acontecer numa variante da URL; tentamos as restantes.
            if exc.code == 404:
                continue
            if exc.code == 429:
                return JsonResponse(
                    {
                        "error": "Serviço de moradas temporariamente indisponível (limite atingido). Tente novamente em instantes."
                    },
                    status=503,
                )
            if 500 <= exc.code <= 599:
                return JsonResponse(
                    {"error": "Serviço de moradas temporariamente indisponível."},
                    status=503,
                )
            return JsonResponse(
                {"error": f"Falha no serviço de moradas (HTTP {exc.code})."},
                status=503,
            )
        except URLError:
            return JsonResponse({"error": "Falha ao consultar serviço de moradas."}, status=503)
        except Exception:
            return JsonResponse({"error": "Erro inesperado na pesquisa de morada."}, status=500)

    if not payload:
        if last_http_error and last_http_error.code == 404:
            return JsonResponse({"error": "Código postal não encontrado."}, status=404)
        return JsonResponse({"error": "Não foi possível consultar a morada."}, status=503)

    localidade = payload.get("Localidade") or payload.get("Concelho") or ""
    rua_avenida = _extrair_rua_avenida(payload)
    concelho = payload.get("Concelho") or ""
    distrito = payload.get("Distrito") or ""
    freguesia = (
        payload.get("Freguesia")
        or payload.get("freguesia")
        or payload.get("Designação Postal")
        or payload.get("Designacao Postal")
        or ""
    )

    result = {
        "codigo_postal": cp,
        "localidade": localidade,
        "rua_avenida": rua_avenida,
        "concelho": concelho,
        "distrito": distrito,
        "freguesia": freguesia,
    }
    cache.set(cache_key, result, timeout=60 * 60 * 24)
    return JsonResponse(result)


def _parse_datetime_local_bruto(valor: str):
    valor = (valor or "").strip()
    if not valor:
        return None
    dt = parse_datetime(valor)
    if dt is None and len(valor) == 16 and "T" in valor:
        dt = parse_datetime(valor + ":00")
    if dt is None:
        return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


@login_required
@require_POST
def atualizar_estado_aptidao_ajax(request):
    try:
        arbitro_id = int(request.POST.get("arbitro_id", ""))
    except ValueError:
        return JsonResponse({"ok": False, "error": "Árbitro inválido."}, status=400)
    estado = (request.POST.get("estado_aptidao") or "").strip()
    valid = {c[0] for c in Arbitro.ESTADO_APTIDAO_CHOICES}
    if estado not in valid:
        return JsonResponse({"ok": False, "error": "Estado inválido."}, status=400)
    arbitro = get_object_or_404(Arbitro, pk=arbitro_id)
    arbitro.estado_aptidao = estado
    arbitro.save()
    return JsonResponse(
        {
            "ok": True,
            "estado_aptidao": arbitro.estado_aptidao,
            "estado_label": arbitro.get_estado_aptidao_display(),
            "ativo": arbitro.ativo,
        }
    )


@login_required
@require_POST
def carregar_exame_ajax(request):
    try:
        arbitro_id = int(request.POST.get("arbitro_id", ""))
    except ValueError:
        return JsonResponse({"ok": False, "error": "Árbitro inválido."}, status=400)

    arbitro = get_object_or_404(Arbitro, pk=arbitro_id)
    data_realizacao = parse_date((request.POST.get("data_realizacao") or "").strip())
    if not data_realizacao:
        return JsonResponse(
            {"ok": False, "error": "Indique uma data de realização válida."},
            status=400,
        )

    try:
        prestador_id = int(request.POST.get("prestador_id", ""))
    except ValueError:
        return JsonResponse({"ok": False, "error": "Prestador inválido."}, status=400)
    prestador = get_object_or_404(Prestador, pk=prestador_id)

    marcacao_id_raw = (request.POST.get("marcacao_id") or "").strip()
    marcacao_para_baixar = None
    if marcacao_id_raw:
        try:
            marcacao_id = int(marcacao_id_raw)
        except ValueError:
            marcacao_id = None
        if marcacao_id:
            marcacao_para_baixar = MarcacaoExame.objects.filter(
                pk=marcacao_id,
                arbitro=arbitro,
            ).first()

    exames_realizados = (request.POST.get("exames_realizados") or "").strip()
    exames_comp = (request.POST.get("exames_complementares") or "").strip()
    partes_texto: list[str] = []
    if exames_realizados:
        partes_texto.append(exames_realizados)
    if exames_comp:
        partes_texto.append(f"Adicionais: {exames_comp}")
    texto_exames_guardar = " | ".join(partes_texto)

    observacoes = (request.POST.get("observacoes") or "").strip()
    arquivo_exame = request.FILES.get("arquivo_exame")
    data_compl_raw = (request.POST.get("data_marcacao_complementar") or "").strip()
    decisao = (request.POST.get("decisao_aptidao") or "").strip()

    if exames_comp:
        data_compl_dt = _parse_datetime_local_bruto(data_compl_raw)
        if data_compl_dt is None:
            return JsonResponse(
                {
                    "ok": False,
                    "error": "Com exames complementares, indique a data e hora para marcar o exame complementar.",
                },
                status=400,
            )
        novo_estado = "aguardando_exame"
    else:
        data_compl_dt = None
        if decisao not in ("ativo", "inativo"):
            return JsonResponse(
                {
                    "ok": False,
                    "error": "Sem exames complementares, escolha se o árbitro fica ativo ou inativo.",
                },
                status=400,
            )
        novo_estado = decisao

    arbitro.data_ultimo_exame = data_realizacao
    arbitro.estado_aptidao = novo_estado
    arbitro.save()

    RealizacaoExameArbitro.objects.create(
        arbitro=arbitro,
        data_realizacao=data_realizacao,
        prestador=prestador,
        exames_complementares=texto_exames_guardar,
        data_marcacao_complementar=data_compl_dt,
        observacoes=observacoes,
        arquivo_exame=arquivo_exame,
    )

    if marcacao_para_baixar is not None:
        marcacao_para_baixar.delete()

    return JsonResponse(
        {
            "ok": True,
            "estado_aptidao": arbitro.estado_aptidao,
            "estado_label": arbitro.get_estado_aptidao_display(),
            "data_ultimo_exame": arbitro.data_ultimo_exame.isoformat()
            if arbitro.data_ultimo_exame
            else None,
        }
    )

