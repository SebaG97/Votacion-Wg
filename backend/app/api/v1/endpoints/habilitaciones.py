from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.rate_limit import RATE_LIMIT_OPERATIVO, limiter
from app.db.session import get_db
from app.schemas.habilitacion import HabilitacionConsultaRequest, HabilitacionConsultaResponse
from app.services.habilitacion import NoHayVotacionAbiertaError, consultar_habilitacion

router = APIRouter()


@router.post(
    "/habilitaciones/consultar",
    response_model=HabilitacionConsultaResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit(RATE_LIMIT_OPERATIVO)
def consultar(
    request: Request, body: HabilitacionConsultaRequest, db: Session = Depends(get_db)
) -> HabilitacionConsultaResponse:
    try:
        return consultar_habilitacion(db, body.celular)
    except NoHayVotacionAbiertaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
