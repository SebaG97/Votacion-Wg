from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.padron import ImportacionPadronRequest, ImportacionPadronResponse
from app.services.padron.importador import ImportacionRechazadaError, ejecutar_importacion
from app.services.padron.importar import EXCEL_POR_DEFECTO

router = APIRouter()


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
