"""Endpoints de padron: importacion (Mision 04) y administracion del panel
(Mision 10, DEC-025) -- historial de importaciones e incidencias, marcar una
incidencia como revisada, y el visor de padron (Mision 12, DEC-031).

Todo el router esta protegido por `require_admin` (DEC-021): `POST
/padron/importaciones` puede reimportar/recrear todo el padron (personas,
matrimonios, unidades electorales e incidencias) y hasta la Mision 10 no
tenia ningun control de acceso -- un olvido, no una decision, corregido aca.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.enums import (
    EstadoPersona,
    EstadoUnidadElectoral,
    SeveridadIncidencia,
    TipoIncidenciaPadron,
    TipoUnidadElectoral,
)
from app.schemas.padron import (
    ImportacionPadronRequest,
    ImportacionPadronResponse,
    IncidenciaPadronResponse,
    PadronListadoResponse,
    PadronPersonaResponse,
    ResolverIncidenciaRequest,
)
from app.services.padron.administracion import (
    IncidenciaNoEncontradaError,
    IncidenciaYaResueltaError,
    listar_importaciones,
    listar_incidencias,
    listar_padron,
    resolver_incidencia,
)
from app.services.padron.importador import ImportacionRechazadaError, ejecutar_importacion
from app.services.padron.importar import EXCEL_POR_DEFECTO

router = APIRouter(dependencies=[Depends(require_admin)])


@router.post(
    "/padron/importaciones",
    response_model=ImportacionPadronResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_importacion(
    body: ImportacionPadronRequest, db: Session = Depends(get_db)
) -> ImportacionPadronResponse:
    ruta_excel = Path(body.excel_path) if body.excel_path else EXCEL_POR_DEFECTO

    try:
        importacion = ejecutar_importacion(db, ruta_excel, usuario=body.usuario)
    except ImportacionRechazadaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return ImportacionPadronResponse.model_validate(importacion)


@router.get(
    "/padron/importaciones",
    response_model=list[ImportacionPadronResponse],
)
def listar_importaciones_endpoint(
    db: Session = Depends(get_db),
) -> list[ImportacionPadronResponse]:
    return [
        ImportacionPadronResponse.model_validate(i) for i in listar_importaciones(db)
    ]


@router.get(
    "/padron/incidencias",
    response_model=list[IncidenciaPadronResponse],
)
def listar_incidencias_endpoint(
    severidad: SeveridadIncidencia | None = None,
    tipo: TipoIncidenciaPadron | None = None,
    resuelta: bool | None = None,
    db: Session = Depends(get_db),
) -> list[IncidenciaPadronResponse]:
    incidencias = listar_incidencias(db, severidad=severidad, tipo=tipo, resuelta=resuelta)
    return [IncidenciaPadronResponse.model_validate(i) for i in incidencias]


@router.get(
    "/padron/personas",
    response_model=PadronListadoResponse,
)
def listar_padron_endpoint(
    circulo: str | None = None,
    grupo_id: int | None = None,
    estado_persona: EstadoPersona | None = None,
    estado_unidad_electoral: EstadoUnidadElectoral | None = None,
    tipo_unidad_electoral: TipoUnidadElectoral | None = None,
    nombre: str | None = None,
    documento: str | None = None,
    celular: str | None = None,
    pagina: int = Query(default=1, ge=1),
    tamanio_pagina: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> PadronListadoResponse:
    """Visor de padron filtrable y paginado (Mision 12, DEC-031): personas,
    su circulo, su matrimonio y sus unidades electorales. Deliberadamente no
    incluye ni permite filtrar por `Voto` -- ver DEC-031 en `docs/DECISIONES.md`."""
    filas, total = listar_padron(
        db,
        circulo=circulo,
        grupo_id=grupo_id,
        estado_persona=estado_persona,
        estado_unidad_electoral=estado_unidad_electoral.value if estado_unidad_electoral else None,
        tipo_unidad_electoral=tipo_unidad_electoral,
        nombre=nombre,
        documento=documento,
        celular=celular,
        pagina=pagina,
        tamanio_pagina=tamanio_pagina,
    )
    return PadronListadoResponse(
        total=total,
        pagina=pagina,
        tamanio_pagina=tamanio_pagina,
        items=[PadronPersonaResponse.model_validate(f) for f in filas],
    )


@router.post(
    "/padron/incidencias/{incidencia_id}/resolver",
    response_model=IncidenciaPadronResponse,
)
def resolver_incidencia_endpoint(
    incidencia_id: int, body: ResolverIncidenciaRequest, db: Session = Depends(get_db)
) -> IncidenciaPadronResponse:
    try:
        incidencia = resolver_incidencia(db, incidencia_id=incidencia_id, usuario=body.usuario)
    except IncidenciaNoEncontradaError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except IncidenciaYaResueltaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return IncidenciaPadronResponse.model_validate(incidencia)
