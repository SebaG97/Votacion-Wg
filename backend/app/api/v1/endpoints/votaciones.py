"""Endpoints de votacion: administracion (Mision 07) y consulta publica de la
papeleta (Mision 09).

Los endpoints de administracion -- crear, cargar/listar opciones, abrir,
cerrar, estado operativo, revelar y resultados -- estan todos protegidos por
`require_admin` (`app/api/deps.py`, DEC-021, `router`). A diferencia de
`POST /api/v1/votaciones/{id}/votos` (Mision 06) y
`POST /api/v1/habilitaciones/consultar` (Mision 05), que siguen sin control
de acceso a proposito (DEC-020): esos son de uso operativo, estos son
administrativos.

`GET /api/v1/votaciones/abierta` (`public_router`, DEC-023) es la excepcion
deliberada: el frontend de votacion necesita la papeleta de la votacion
abierta para poder votar y no tiene el token administrativo, igual que los
dos endpoints operativos de arriba.
"""

from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.schemas.votacion import (
    AbrirVotacionRequest,
    CerrarVotacionRequest,
    OpcionAbiertaResponse,
    OpcionVotoCreateRequest,
    OpcionVotoResponse,
    VotacionAbiertaResponse,
    VotacionCreateRequest,
    VotacionEstadoResponse,
    VotacionResponse,
    VotacionResultadosResponse,
)
from app.services.votacion import (
    NoHayVotacionAbiertaError,
    OtraVotacionAbiertaError,
    ResultadosBloqueadosError,
    ResultadosYaReveladosError,
    VotacionNoAbiertaError,
    VotacionNoCerradaError,
    VotacionNoEncontradaError,
    VotacionNoEsBorradorError,
    VotacionSinOpcionesError,
    abrir_votacion,
    agregar_opcion,
    cerrar_votacion,
    crear_votacion,
    listar_opciones,
    listar_votaciones,
    obtener_estado_operativo,
    obtener_resultados,
    obtener_votacion_abierta,
    revelar_resultados,
)

router = APIRouter(dependencies=[Depends(require_admin)])
public_router = APIRouter()


@public_router.get(
    "/votaciones/abierta",
    response_model=VotacionAbiertaResponse,
)
def abierta(db: Session = Depends(get_db)) -> VotacionAbiertaResponse:
    """Papeleta de la unica votacion ABIERTA: sin `require_admin` (DEC-023),
    a diferencia de todo lo demas en este archivo. Reusa
    `obtener_votacion_abierta` (`app/services/votacion.py`), la misma
    busqueda que ya usaba `app/services/habilitacion.py` (DEC-018), en vez de
    repetirla."""
    try:
        votacion = obtener_votacion_abierta(db)
    except NoHayVotacionAbiertaError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    opciones = listar_opciones(db, votacion.id)
    return VotacionAbiertaResponse(
        votacion_id=votacion.id,
        nombre=votacion.nombre,
        opciones=[
            OpcionAbiertaResponse(id=o.id, nombre=o.nombre, orden=o.orden) for o in opciones
        ],
    )


@router.get(
    "/votaciones",
    response_model=list[VotacionResponse],
)
def listar_votaciones_endpoint(db: Session = Depends(get_db)) -> list[VotacionResponse]:
    """Todas las votaciones con su estado y fechas (Mision 10, DEC-025): sin
    esto el panel administrativo no tenia forma de descubrir que
    `votacion_id` administrar."""
    return [VotacionResponse.model_validate(v) for v in listar_votaciones(db)]


@router.post(
    "/votaciones",
    response_model=VotacionResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear(body: VotacionCreateRequest, db: Session = Depends(get_db)) -> VotacionResponse:
    votacion = crear_votacion(db, nombre=body.nombre)
    return VotacionResponse.model_validate(votacion)


@router.post(
    "/votaciones/{votacion_id}/opciones",
    response_model=OpcionVotoResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_opcion(
    votacion_id: int, body: OpcionVotoCreateRequest, db: Session = Depends(get_db)
) -> OpcionVotoResponse:
    try:
        opcion = agregar_opcion(
            db, votacion_id=votacion_id, nombre=body.nombre, orden=body.orden
        )
    except VotacionNoEncontradaError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VotacionNoEsBorradorError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return OpcionVotoResponse.model_validate(opcion)


@router.get(
    "/votaciones/{votacion_id}/opciones",
    response_model=list[OpcionVotoResponse],
)
def listar(votacion_id: int, db: Session = Depends(get_db)) -> list[OpcionVotoResponse]:
    try:
        opciones = listar_opciones(db, votacion_id)
    except VotacionNoEncontradaError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [OpcionVotoResponse.model_validate(o) for o in opciones]


@router.post(
    "/votaciones/{votacion_id}/abrir",
    response_model=VotacionResponse,
)
def abrir(
    votacion_id: int, body: AbrirVotacionRequest, db: Session = Depends(get_db)
) -> VotacionResponse:
    try:
        votacion = abrir_votacion(db, votacion_id=votacion_id, usuario=body.usuario)
    except VotacionNoEncontradaError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (
        VotacionNoEsBorradorError,
        VotacionSinOpcionesError,
        OtraVotacionAbiertaError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return VotacionResponse.model_validate(votacion)


@router.post(
    "/votaciones/{votacion_id}/cerrar",
    response_model=VotacionResponse,
)
def cerrar(
    votacion_id: int, body: CerrarVotacionRequest, db: Session = Depends(get_db)
) -> VotacionResponse:
    try:
        votacion = cerrar_votacion(db, votacion_id=votacion_id, usuario=body.usuario)
    except VotacionNoEncontradaError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VotacionNoAbiertaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return VotacionResponse.model_validate(votacion)


@router.get(
    "/votaciones/{votacion_id}/estado",
    response_model=VotacionEstadoResponse,
)
def estado(votacion_id: int, db: Session = Depends(get_db)) -> VotacionEstadoResponse:
    try:
        datos = obtener_estado_operativo(db, votacion_id)
    except VotacionNoEncontradaError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return VotacionEstadoResponse(**datos)


@router.post(
    "/votaciones/{votacion_id}/revelar",
    response_model=VotacionResponse,
)
def revelar(votacion_id: int, db: Session = Depends(get_db)) -> VotacionResponse:
    try:
        votacion = revelar_resultados(db, votacion_id=votacion_id)
    except VotacionNoEncontradaError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (VotacionNoCerradaError, ResultadosYaReveladosError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return VotacionResponse.model_validate(votacion)


def _resultados_a_csv(datos: dict) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow(["votacion_id", datos["votacion_id"]])
    writer.writerow(["estado", datos["estado"].value])
    writer.writerow(["total_votos", datos["total_votos"]])
    writer.writerow([])

    writer.writerow(["seccion", "opcion_id", "nombre", "votos", "porcentaje"])
    for fila in datos["totales_por_opcion"]:
        writer.writerow(
            ["opcion", fila["opcion_id"], fila["nombre"], fila["votos"], f"{fila['porcentaje']:.2f}"]
        )
    writer.writerow([])

    writer.writerow(["seccion", "tipo", "votos_emitidos", "unidades_habilitadas", "participacion"])
    for fila in datos["totales_por_tipo_unidad"]:
        participacion = "" if fila["participacion"] is None else f"{fila['participacion']:.4f}"
        writer.writerow(
            [
                "tipo_unidad",
                fila["tipo"].value,
                fila["votos_emitidos"],
                fila["unidades_habilitadas"],
                participacion,
            ]
        )
    writer.writerow([])

    writer.writerow(
        ["seccion", "grupo_id", "nombre", "votos_emitidos", "unidades_habilitadas", "participacion"]
    )
    for fila in datos["totales_por_grupo"]:
        participacion = "" if fila["participacion"] is None else f"{fila['participacion']:.4f}"
        writer.writerow(
            [
                "grupo",
                fila["grupo_id"],
                fila["nombre"],
                fila["votos_emitidos"],
                fila["unidades_habilitadas"],
                participacion,
            ]
        )

    return buffer.getvalue()


@router.get("/votaciones/{votacion_id}/resultados", response_model=None)
def resultados(
    votacion_id: int, formato: str | None = None, db: Session = Depends(get_db)
) -> VotacionResultadosResponse | Response:
    try:
        datos = obtener_resultados(db, votacion_id)
    except VotacionNoEncontradaError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ResultadosBloqueadosError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    if formato == "csv":
        return Response(content=_resultados_a_csv(datos), media_type="text/csv")

    return VotacionResultadosResponse(**datos)
