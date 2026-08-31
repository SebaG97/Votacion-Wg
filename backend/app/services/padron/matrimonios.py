"""Agrupamiento de matrimonios por etiqueta + contiguidad (Mision 02, DEC-007).

Portado sin cambios de conducta desde `backend/scripts/explorar_padron.py`.
"""

from __future__ import annotations

from app.services.padron.dominio import MatrimonioExcel, PersonaExcel
from app.services.padron.normalizacion import clave_texto


def agrupar_matrimonios(personas: list[PersonaExcel]) -> list[MatrimonioExcel]:
    """Agrupa por etiqueta MATRIMONIO + contiguidad de filas, con tope de 2.

    La etiqueta sola no alcanza: hay 7 etiquetas repetidas en circulos distintos
    (`PEREIRA FERNANDEZ`, `Reyes`, ...). La contiguidad si es fiable: en la hoja
    los conyuges estan siempre en filas consecutivas.
    """
    grupos: list[MatrimonioExcel] = []
    actual: MatrimonioExcel | None = None
    for p in personas:
        clave = clave_texto(p.matrimonio)
        if (
            actual is not None
            and clave is not None
            and clave_texto(actual.etiqueta) == clave
            and p.fila == actual.filas[-1] + 1
            and len(actual.filas) < 2
        ):
            actual.filas.append(p.fila)
            actual.personas.append(p)
            continue
        actual = MatrimonioExcel(
            etiqueta=p.matrimonio,
            circulo=p.circulo,
            filas=[p.fila],
            personas=[p],
        )
        grupos.append(actual)
    return grupos
