"""Orquesta lectura + clasificacion + agrupamiento + incidencias de un Excel.

Punto de entrada compartido por `backend/scripts/explorar_padron.py` (solo
reporte, no persiste) y `app.services.padron.importador` (persiste en base).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.services.padron.clasificacion import construir_personas
from app.services.padron.columnas import (
    COLUMNAS_JEFES,
    COLUMNAS_PRINCIPAL,
    HOJA_JEFES,
    HOJA_PRINCIPAL,
    J_APELLIDOS,
    J_NOMBRES,
)
from app.services.padron.dominio import IncidenciaDetectada, MatrimonioExcel, PersonaExcel
from app.services.padron.incidencias import detectar_incidencias, reconciliar_hojas
from app.services.padron.lectura import leer_hoja
from app.services.padron.matrimonios import agrupar_matrimonios
from app.services.padron.normalizacion import texto


@dataclass
class ResultadoAnalisis:
    personas: list[PersonaExcel]
    encabezados: list[tuple[int, tuple[Any, ...]]]
    filas_resumen: list[int]
    filas_vacias: list[int]
    filas_etiqueta: list[int]
    matrimonios: list[MatrimonioExcel]
    jefes_filas: list[tuple[int, tuple[Any, ...]]]
    incidencias: list[IncidenciaDetectada]
    reconciliacion_conteos: dict[str, int]
    celular_resuelto_por_fila: dict[int, str]
    personas_jefe_confirmado: set[int]


def analizar_excel(ruta: Path) -> ResultadoAnalisis:
    filas_principal = leer_hoja(ruta, HOJA_PRINCIPAL, COLUMNAS_PRINCIPAL)
    filas_jefes = leer_hoja(ruta, HOJA_JEFES, COLUMNAS_JEFES)
    cuerpo_principal = filas_principal[1:]
    cuerpo_jefes = filas_jefes[1:]

    personas, encabezados, resumen, vacias, etiquetas = construir_personas(cuerpo_principal, 2)
    matrimonios = agrupar_matrimonios(personas)
    jefes_filas = [
        (i + 2, f) for i, f in enumerate(cuerpo_jefes)
        if texto(f[J_APELLIDOS]) or texto(f[J_NOMBRES])
    ]

    incidencias = detectar_incidencias(personas, matrimonios, encabezados)
    inc_cruce, conteos_cruce, celular_resuelto, jefe_confirmado = reconciliar_hojas(
        personas, jefes_filas
    )
    incidencias.extend(inc_cruce)

    return ResultadoAnalisis(
        personas=personas,
        encabezados=encabezados,
        filas_resumen=resumen,
        filas_vacias=vacias,
        filas_etiqueta=etiquetas,
        matrimonios=matrimonios,
        jefes_filas=jefes_filas,
        incidencias=incidencias,
        reconciliacion_conteos=conteos_cruce,
        celular_resuelto_por_fila=celular_resuelto,
        personas_jefe_confirmado=jefe_confirmado,
    )
