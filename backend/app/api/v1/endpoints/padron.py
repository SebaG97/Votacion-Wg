"""Endpoints de padron: importacion (Mision 04) y administracion del panel
(Mision 10, DEC-025) -- historial de importaciones e incidencias, y marcar
una incidencia como revisada.

Todo el router esta protegido por `require_admin` (DEC-021): `POST
/padron/importaciones` puede reimportar/recrear todo el padron (personas,
matrimonios, unidades electorales e incidencias) y hasta la Mision 10 no
tenia ningun control de acceso -- un olvido, no una decision, corregido aca.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.enums import SeveridadIncidencia, TipoIncidenciaPadron
from app.schemas.padron import (
    ImportacionPadronRequest,
    ImportacionPadronResponse,
    IncidenciaPadronResponse,
    ResolverIncidenciaRequest,
)
from app.services.padron.administracion import (
    IncidenciaNoEncontradaError,
    IncidenciaYaResueltaError,
    listar_importaciones,
    listar_incidencias,
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
