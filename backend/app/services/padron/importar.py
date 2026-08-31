"""CLI del importador del padron (Mision 04).

Uso:

    cd backend
    python -m app.services.padron.importar
    python -m app.services.padron.importar --excel "../docs/Padron de ML con Jefes 2026.xlsx"

Equivalente en desarrollo/pruebas a `POST /api/v1/padron/importaciones`, sin
depender de que el servidor este corriendo.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from app.db.session import SessionLocal
from app.services.padron.importador import ImportacionRechazadaError, ejecutar_importacion

RAIZ = Path(__file__).resolve().parents[4]
EXCEL_POR_DEFECTO = RAIZ / "docs" / "Padron de ML con Jefes 2026.xlsx"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--excel", type=Path, default=EXCEL_POR_DEFECTO)
    parser.add_argument("--usuario", type=str, default=None)
    args = parser.parse_args(argv)

    db = SessionLocal()
    try:
        importacion = ejecutar_importacion(db, args.excel, usuario=args.usuario)
    except ImportacionRechazadaError as exc:
        print(f"Importacion rechazada: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        print(f"Importacion #{importacion.id} -> {importacion.estado.value}")
        print(json.dumps(importacion.resumen, ensure_ascii=False, indent=2))
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
