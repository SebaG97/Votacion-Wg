"""Clasificacion estructural de filas de la hoja principal (Mision 02, DEC-006).

Portado sin cambios de conducta desde `backend/scripts/explorar_padron.py`.
"""

from __future__ import annotations

from typing import Any

from app.services.padron.columnas import (
    P_APELLIDOS,
    P_CELULAR,
    P_CI,
    P_CIRCULO,
    P_CIRCULO_NUEVO,
    P_CONSAGRADOS,
    P_EMAIL,
    P_GRUPOS,
    P_JEFES,
    P_JORNADA,
    P_MATRIMONIO,
    P_MIEMBROS,
    P_ML,
    P_NOMBRES,
    P_NO_ML,
    P_OBSERVACION,
    P_SIN_CIRCULO,
    P_SIN_CONSAGRACION,
    P_VIUDOS,
)
from app.services.padron.dominio import PersonaExcel
from app.services.padron.normalizacion import clave_texto, es_marca, normalizar_celular, normalizar_ci, texto


def es_fila_resumen(fila: tuple[Any, ...]) -> bool:
    """Filas de totales/porcentajes al pie de la hoja principal.

    No tienen persona ni matrimonio y acumulan agregados (o el literal
    `matrimonios` en la columna CIRCULO).
    """
    if any(texto(fila[i]) for i in (P_APELLIDOS, P_NOMBRES, P_MATRIMONIO, P_CELULAR)):
        return False
    if clave_texto(fila[P_CIRCULO]) == "MATRIMONIOS":
        return True
    for i in (P_GRUPOS, P_SIN_CIRCULO, P_ML, P_VIUDOS, P_MIEMBROS, P_SIN_CONSAGRACION, P_CONSAGRADOS):
        valor = fila[i]
        if isinstance(valor, (int, float)) and not isinstance(valor, bool) and valor > 50:
            return True
    return False


def es_fila_persona(fila: tuple[Any, ...]) -> bool:
    return bool(texto(fila[P_APELLIDOS]) or texto(fila[P_NOMBRES]))


def es_fila_encabezado_circulo(fila: tuple[Any, ...]) -> bool:
    """Fila separadora de circulo: sin persona, con conteo declarado de miembros."""
    return not es_fila_persona(fila) and texto(fila[P_MIEMBROS]) is not None


def es_fila_etiqueta(fila: tuple[Any, ...]) -> bool:
    """Fila decorativa tipo `ELLA / EL` usada como rotulo de columna."""
    valores = {clave_texto(v) for v in fila if texto(v)}
    return bool(valores) and valores <= {"EL", "ELLA", "ELLOS", "ELLAS"}


def construir_personas(
    filas: list[tuple[Any, ...]], desplazamiento: int
) -> tuple[
    list[PersonaExcel], list[tuple[int, tuple[Any, ...]]], list[int], list[int], list[int]
]:
    personas: list[PersonaExcel] = []
    encabezados: list[tuple[int, tuple[Any, ...]]] = []
    resumen: list[int] = []
    vacias: list[int] = []
    etiquetas: list[int] = []

    for i, fila in enumerate(filas):
        nro = i + desplazamiento
        if all(texto(v) is None for v in fila):
            vacias.append(nro)
            continue
        if es_fila_resumen(fila):
            resumen.append(nro)
            continue
        if es_fila_etiqueta(fila):
            etiquetas.append(nro)
            continue
        if es_fila_persona(fila):
            cel, cel_motivo = normalizar_celular(fila[P_CELULAR])
            ci, ci_motivo = normalizar_ci(fila[P_CI])
            personas.append(
                PersonaExcel(
                    fila=nro,
                    circulo=texto(fila[P_CIRCULO]),
                    circulo_nuevo=texto(fila[P_CIRCULO_NUEVO]),
                    matrimonio=texto(fila[P_MATRIMONIO]),
                    apellidos=texto(fila[P_APELLIDOS]),
                    nombres=texto(fila[P_NOMBRES]),
                    celular_crudo=fila[P_CELULAR],
                    celular=cel,
                    celular_motivo=cel_motivo,
                    email=texto(fila[P_EMAIL]),
                    ci=ci,
                    ci_motivo=ci_motivo,
                    es_consagrado=es_marca(fila[P_CONSAGRADOS]),
                    es_sin_consagracion=es_marca(fila[P_SIN_CONSAGRACION]),
                    es_ml=es_marca(fila[P_ML]),
                    es_viudo=es_marca(fila[P_VIUDOS]),
                    es_jefe=es_marca(fila[P_JEFES]),
                    tiene_jornada=es_marca(fila[P_JORNADA]),
                    marca_no_ml=es_marca(fila[P_NO_ML]),
                    observacion=texto(fila[P_OBSERVACION]),
                )
            )
            continue
        encabezados.append((nro, fila))

    return personas, encabezados, resumen, vacias, etiquetas
