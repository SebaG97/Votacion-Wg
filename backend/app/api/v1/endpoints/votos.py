from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.voto import VotoRequest, VotoResponse
from app.services.voto import (
    CelularNoResuelveUnidadError,
    OpcionInvalidaError,
    PersonaNoAutorizadaError,
    UnidadElectoralNoDisponibleError,
    UnidadElectoralNoEncontradaError,
    VotacionNoDisponibleError,
    VotoDuplicadoError,
    registrar_voto,
)

router = APIRouter()


@router.post(
    "/votaciones/{votacion_id}/votos",
    response_model=VotoResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_voto(
    votacion_id: int, body: VotoRequest, db: Session = Depends(get_db)
) -> VotoResponse:
    try:
        voto = registrar_voto(
            db,
            votacion_id=votacion_id,
            celular_consultado=body.celular_consultado,
            unidad_electoral_id=body.unidad_electoral_id,
            opcion_id=body.opcion_id,
            emitido_por_persona_id=body.emitido_por_persona_id,
            canal=body.canal,
        )
    except UnidadElectoralNoEncontradaError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (
        VotacionNoDisponibleError,
        UnidadElectoralNoDisponibleError,
        VotoDuplicadoError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (
        OpcionInvalidaError,
        CelularNoResuelveUnidadError,
        PersonaNoAutorizadaError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return VotoResponse.model_validate(voto)
