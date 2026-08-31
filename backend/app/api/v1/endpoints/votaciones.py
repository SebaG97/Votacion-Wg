"""Endpoints de administracion de votacion (Mision 07): crear, cargar/listar
opciones, abrir, cerrar y consultar el estado operativo.

Todos protegidos por `require_admin` (`app/api/deps.py`, DEC-021). A
diferencia de `POST /api/v1/votaciones/{id}/votos` (Mision 06) y
`POST /api/v1/habilitaciones/consultar` (Mision 05), que siguen sin control
de acceso a proposito (DEC-020): esos son de uso operativo, estos son
administrativos.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.schemas.votacion import (
    AbrirVotacionRequest,
    CerrarVotacionRequest,
    OpcionVotoCreateRequest,
    OpcionVotoResponse,
    VotacionCreateRequest,
    VotacionEstadoResponse,
    VotacionResponse,
)
from app.services.votacion import (
    OtraVotacionAbiertaError,
    VotacionNoAbiertaError,
    VotacionNoEncontradaError,
    VotacionNoEsBorradorError,
    VotacionSinOpcionesError,
    abrir_votacion,
    agregar_opcion,
    cerrar_votacion,
    crear_votacion,
    listar_opciones,
    obtener_estado_operativo,
)

router = APIRouter(dependencies=[Depends(require_admin)])


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
