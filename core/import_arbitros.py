"""Importação resiliente de árbitros a partir de Excel."""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError

from arbitro.models import Arbitro
from associacao.models import Associacao
from core.models import Categoria, Epoca, EpocaArbitro, Modalidade

PENDENCIA_TAG = "[Importação]"


def _looks_like_epoca(value: str) -> bool:
    return bool(re.match(r"^\d{4}\s*/\s*\d{4}$", value.strip()))


def normalize_header(value) -> str:
    value = str(value or "").strip().lower()
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return " ".join(value.split())


def cell_str(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def parse_date_maybe(value) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        raw = value.strip()
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue
    return None


def normalize_nif(value) -> str:
    """Ignora NIF mascarado ou inválido (ex.: *****)."""
    if value is None or value == "":
        return ""
    nif = str(value).strip().replace(" ", "").replace(".", "").replace("-", "")
    if not nif:
        return ""
    lowered = nif.lower()
    if lowered in {"n/a", "na", "-", "—", "s/n", "sn", "null", "none"}:
        return ""
    if set(nif) <= {"*", "x", "X"}:
        return ""
    if not any(ch.isdigit() for ch in nif):
        return ""
    return nif


def normalize_address(value) -> str:
    text = cell_str(value)
    if not text:
        return ""
    compact = text.replace(" ", "")
    if compact and set(compact) <= {"*"}:
        return ""
    return text


def normalize_email(value) -> tuple[str, bool]:
    """Retorna (email, válido). Se inválido, devolve ('', False)."""
    email = cell_str(value)
    if not email:
        return "", True
    try:
        validate_email(email)
    except ValidationError:
        return "", False
    return email, True


def _build_header_map(headers: list) -> dict[str, int]:
    header_map: dict[str, int] = {}
    for idx, h in enumerate(headers):
        norm = normalize_header(h)
        if norm:
            header_map[norm] = idx
    return header_map


def _get_by_keys(row, header_map: dict[str, int], keys: list[str]):
    for key in keys:
        norm = normalize_header(key)
        if norm in header_map:
            return row[header_map[norm]]
    return None


def _parse_sexo(raw) -> str:
    sexo_raw_norm = (str(raw).strip().lower() if raw else "")
    if not sexo_raw_norm:
        return ""
    if sexo_raw_norm.startswith("m") or "masc" in sexo_raw_norm:
        return "M"
    if sexo_raw_norm.startswith("f") or "fem" in sexo_raw_norm:
        return "F"
    return ""


def _pendencias_da_linha(
    *,
    nif_raw,
    cpf_nif: str,
    email: str,
    email_valido: bool,
    morada: str,
    data_nascimento: date | None,
) -> list[str]:
    pendencias: list[str] = []
    if cell_str(nif_raw) and not cpf_nif:
        pendencias.append("NIF inválido ou mascarado — atualizar manualmente")
    if not cpf_nif:
        pendencias.append("NIF em falta")
    if not email_valido:
        pendencias.append("E-mail inválido no Excel — atualizar manualmente")
    elif not email:
        pendencias.append("E-mail em falta")
    if not morada:
        pendencias.append("Morada em falta ou mascarada")
    if data_nascimento is None:
        pendencias.append("Data de nascimento em falta")
    return pendencias


def _anexar_pendencias(observacoes: str, pendencias: list[str]) -> str:
    if not pendencias:
        return observacoes or ""
    bloco = f"{PENDENCIA_TAG} " + "; ".join(pendencias)
    base = (observacoes or "").strip()
    if not base:
        return bloco
    if PENDENCIA_TAG in base:
        return base
    return f"{base}\n{bloco}"


def _find_arbitro(
    *,
    nome_completo: str,
    data_nascimento: date | None,
    cpf_nif: str,
    email: str,
    associacao: Associacao,
) -> Arbitro | None:
    if cpf_nif:
        arbitro = Arbitro.objects.filter(cpf_nif=cpf_nif).order_by("pk").first()
        if arbitro:
            return arbitro
    if email:
        arbitro = Arbitro.objects.filter(email__iexact=email).order_by("pk").first()
        if arbitro:
            return arbitro
    if data_nascimento:
        arbitro = (
            Arbitro.objects.filter(
                nome_completo__iexact=nome_completo,
                data_nascimento=data_nascimento,
            )
            .order_by("pk")
            .first()
        )
        if arbitro:
            return arbitro
    return (
        Arbitro.objects.filter(
            nome_completo__iexact=nome_completo,
            associacao_futebol=associacao,
        )
        .order_by("pk")
        .first()
    )


def _arbitro_fields_from_row(
    row,
    header_map: dict[str, int],
    associacao: Associacao,
) -> dict:
    nome_completo = _get_by_keys(
        row, header_map, ["nome completo", "nome_completo", "nome", "nome arbitro"]
    )
    if not nome_completo and row:
        for idx in (0, 1):
            if len(row) > idx and row[idx] not in (None, ""):
                candidate = cell_str(row[idx])
                if candidate and not _looks_like_epoca(candidate):
                    nome_completo = candidate
                    break
    nome_completo = cell_str(nome_completo)

    data_nascimento = parse_date_maybe(
        _get_by_keys(
            row,
            header_map,
            [
                "data nascimento",
                "data de nascimento",
                "data_nascimento",
                "nascimento",
            ],
        )
    )

    nif_raw = _get_by_keys(row, header_map, ["cpf nif", "cpf_nif", "nif", "cpf"])
    cpf_nif = normalize_nif(nif_raw)

    sexo = _parse_sexo(_get_by_keys(row, header_map, ["sexo"]))

    telefone = cell_str(
        _get_by_keys(
            row,
            header_map,
            [
                "telemovel",
                "telemóvel",
                "telefone",
                "tel",
                "contacto telefonico",
                "contacto telefónico",
            ],
        )
    )

    email, email_valido = normalize_email(
        _get_by_keys(
            row,
            header_map,
            ["email", "e-mail", "endereco de email", "endereço de email"],
        )
    )

    codigo_postal = cell_str(
        _get_by_keys(
            row, header_map, ["codigo postal", "código postal", "codigo_postal", "cp"]
        )
    )
    localidade = cell_str(
        _get_by_keys(row, header_map, ["localidade", "concelho", "cidade"])
    )
    morada = normalize_address(
        _get_by_keys(
            row,
            header_map,
            ["morada", "rua avenida", "rua/avenida", "rua / avenida", "rua_avenida"],
        )
    )
    rua_avenida = morada or normalize_address(
        _get_by_keys(
            row, header_map, ["rua avenida", "rua/avenida", "rua / avenida", "rua_avenida"]
        )
    )
    numero = _get_by_keys(row, header_map, ["numero", "nº"])
    complemento = cell_str(_get_by_keys(row, header_map, ["complemento"]))
    observacoes_morada = cell_str(
        _get_by_keys(
            row,
            header_map,
            ["observacoes", "observacoes morada", "observações", "observacoes_morada"],
        )
    )
    cidade = cell_str(_get_by_keys(row, header_map, ["cidade", "concelho"]))

    categoria_name = _get_by_keys(row, header_map, ["categoria"])
    modalidade_name = _get_by_keys(row, header_map, ["modalidade"])
    categoria_obj = None
    if categoria_name:
        categoria_obj, _ = Categoria.objects.get_or_create(nome=cell_str(categoria_name))
    modalidade_obj = None
    if modalidade_name:
        modalidade_obj, _ = Modalidade.objects.get_or_create(nome=cell_str(modalidade_name))

    data_ultimo_exame = parse_date_maybe(
        _get_by_keys(
            row,
            header_map,
            ["data ultimo exame", "data do ultimo exame", "data_ultimo_exame"],
        )
    )

    pendencias = _pendencias_da_linha(
        nif_raw=nif_raw,
        cpf_nif=cpf_nif,
        email=email,
        email_valido=email_valido,
        morada=morada or rua_avenida,
        data_nascimento=data_nascimento,
    )
    observacoes_morada = _anexar_pendencias(observacoes_morada, pendencias)

    return {
        "nome_completo": nome_completo,
        "data_nascimento": data_nascimento,
        "cpf_nif": cpf_nif,
        "sexo": sexo,
        "email": email,
        "telefone": telefone,
        "codigo_postal": codigo_postal,
        "localidade": localidade,
        "morada": morada,
        "rua_avenida": rua_avenida,
        "numero": cell_str(numero) if numero not in (None, "") else "",
        "complemento": complemento,
        "observacoes_morada": observacoes_morada,
        "cidade": cidade,
        "categoria": categoria_obj,
        "modalidade": modalidade_obj,
        "data_ultimo_exame": data_ultimo_exame,
        "associacao_futebol": associacao,
        "pendencias": pendencias,
    }


def _save_arbitro(arbitro: Arbitro | None, fields: dict) -> tuple[Arbitro, bool]:
    """Guarda ou atualiza árbitro. Retorna (arbitro, created)."""
    payload = {k: v for k, v in fields.items() if k != "pendencias"}
    associacao = payload.pop("associacao_futebol")

    if arbitro is None:
        arbitro = Arbitro.objects.create(associacao_futebol=associacao, **payload)
        return arbitro, True

    updates: dict = {}
    for key, value in payload.items():
        if key == "nome_completo":
            if arbitro.nome_completo != value:
                updates[key] = value
            continue
        if key == "observacoes_morada" and value:
            if arbitro.observacoes_morada != value:
                updates[key] = value
            continue
        if value in (None, ""):
            continue
        if getattr(arbitro, key) != value:
            updates[key] = value

    if arbitro.associacao_futebol_id != associacao.id:
        updates["associacao_futebol"] = associacao

    if updates:
        for key, value in updates.items():
            setattr(arbitro, key, value)
        arbitro.save()
    return arbitro, False


def _import_row_resiliente(
    row,
    *,
    row_idx: int,
    header_map: dict[str, int],
    epoca: Epoca,
    associacao: Associacao,
) -> tuple[str, list[str], list[str]]:
    """
    Importa uma linha. Retorna (status, pendencias, errors).
    status: inserted | updated | skipped
    """
    fields = _arbitro_fields_from_row(row, header_map, associacao)
    nome = fields.get("nome_completo") or ""
    if not nome:
        return "skipped", [], [], ""

    pendencias = list(fields.pop("pendencias", []))
    arbitro = _find_arbitro(
        nome_completo=nome,
        data_nascimento=fields.get("data_nascimento"),
        cpf_nif=fields.get("cpf_nif") or "",
        email=fields.get("email") or "",
        associacao=associacao,
    )

    errors: list[str] = []
    created = False
    try:
        arbitro, created = _save_arbitro(arbitro, fields)
    except IntegrityError:
        fields["cpf_nif"] = ""
        pendencias.append("NIF em conflito com outro registo — atualizar manualmente")
        fields["observacoes_morada"] = _anexar_pendencias(
            fields.get("observacoes_morada") or "", pendencias
        )
        arbitro = _find_arbitro(
            nome_completo=nome,
            data_nascimento=fields.get("data_nascimento"),
            cpf_nif="",
            email=fields.get("email") or "",
            associacao=associacao,
        )
        try:
            arbitro, created = _save_arbitro(arbitro, fields)
        except Exception as exc:
            errors.append(f"Linha {row_idx}: {exc}")
            return "skipped", pendencias, errors, nome
    except Exception as exc:
        # Último recurso: registo mínimo para não perder o árbitro na importação.
        try:
            arbitro, created = Arbitro.objects.get_or_create(
                nome_completo=nome,
                associacao_futebol=associacao,
                defaults={
                    "data_nascimento": fields.get("data_nascimento"),
                    "observacoes_morada": _anexar_pendencias(
                        "",
                        pendencias + [f"Dados parciais importados ({exc})"],
                    ),
                },
            )
            created = created
        except Exception as exc2:
            errors.append(f"Linha {row_idx}: {exc2}")
            return "skipped", pendencias, errors, nome

    EpocaArbitro.objects.get_or_create(epoca=epoca, arbitro=arbitro)
    return ("inserted" if created else "updated"), pendencias, errors, nome


def importar_arbitros_worksheet(ws, *, epoca: Epoca, associacao: Associacao) -> dict:
    headers = [cell.value for cell in ws[1]]
    header_map = _build_header_map(headers)

    inserted = 0
    updated = 0
    skipped = 0
    errors: list[str] = []
    pendencias_resumo: list[str] = []

    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        status, pendencias, row_errors, nome = _import_row_resiliente(
            row,
            row_idx=row_idx,
            header_map=header_map,
            epoca=epoca,
            associacao=associacao,
        )
        if status == "inserted":
            inserted += 1
        elif status == "updated":
            updated += 1
        else:
            skipped += 1
        errors.extend(row_errors)
        if pendencias and status in {"inserted", "updated"}:
            pendencias_resumo.append(
                f"Linha {row_idx} ({nome or '?'}): " + "; ".join(pendencias)
            )

    return {
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "error_count": len(errors),
        "errors": errors[:20],
        "pendencias_count": len(pendencias_resumo),
        "pendencias": pendencias_resumo[:30],
    }
