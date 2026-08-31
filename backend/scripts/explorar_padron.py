"""Explorador del Excel del padron (Mision 02).

Lee `docs/Padron de ML con Jefes 2026.xlsx` en modo solo lectura, documenta la
estructura real de las tres hojas y genera los informes de calidad de datos que
alimentan `docs/PADRON_ANALISIS.md`.

El script NO modifica el Excel y NO persiste nada en base de datos: la
importacion real es la Mision 04 (`app.services.padron.importar`).

La logica de lectura, normalizacion, clasificacion de filas, agrupamiento de
matrimonios y deteccion de incidencias vive en `app.services.padron` (Mision
04), para que este script y el importador real compartan las mismas reglas
validadas. Este script solo agrega el perfilado de columnas y los reportes
(CSV/JSON) que no necesita el importador.

Uso:

    cd backend
    python scripts/explorar_padron.py

Salidas:

    docs/padron_incidencias.csv   una fila por incidencia detectada
    docs/padron_estructura.json   estructura y metricas agregadas
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.padron.clasificacion import construir_personas  # noqa: E402
from app.services.padron.columnas import (  # noqa: E402
    COLUMNAS_JEFES,
    COLUMNAS_PRINCIPAL,
    HOJA_JEFES,
    HOJA_PIVOT,
    HOJA_PRINCIPAL,
    J_APELLIDOS,
    J_NOMBRES,
    J_ORDEN,
    SEVERIDAD_ALTA,
    SEVERIDAD_BAJA,
    SEVERIDAD_CRITICA,
    SEVERIDAD_MEDIA,
)
from app.services.padron.dominio import IncidenciaDetectada  # noqa: E402
from app.services.padron.incidencias import detectar_incidencias, reconciliar_hojas  # noqa: E402
from app.services.padron.lectura import auditar_combinadas, leer_celdas_combinadas, leer_hoja  # noqa: E402
from app.services.padron.matrimonios import agrupar_matrimonios  # noqa: E402
from app.services.padron.normalizacion import clave_circulo, texto  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
EXCEL_POR_DEFECTO = RAIZ / "docs" / "Padron de ML con Jefes 2026.xlsx"
DIR_SALIDA_POR_DEFECTO = RAIZ / "docs"


# --------------------------------------------------------------------------- #
# Perfilado de columnas (solo para el reporte exploratorio)
# --------------------------------------------------------------------------- #


def perfilar_columnas(
    filas: list[tuple[Any, ...]], encabezado: tuple[Any, ...], max_col: int
) -> list[dict[str, Any]]:
    perfil = []
    for i in range(max_col):
        valores = [f[i] for f in filas]
        no_nulos = [v for v in valores if texto(v) is not None]
        blancos = sum(1 for v in valores if isinstance(v, str) and not v.strip())
        perfil.append({
            "columna": chr(65 + i) if i < 26 else f"col{i}",
            "encabezado": encabezado[i],
            "no_nulos": len(no_nulos),
            "solo_espacios": blancos,
            "tipos": dict(Counter(type(v).__name__ for v in no_nulos)),
            "muestra": [str(v) for v, _ in Counter(map(str, no_nulos)).most_common(5)],
        })
    return perfil


def construir_estructura(ruta: Path) -> tuple[dict[str, Any], list[IncidenciaDetectada]]:
    filas_principal = leer_hoja(ruta, HOJA_PRINCIPAL, COLUMNAS_PRINCIPAL)
    filas_jefes = leer_hoja(ruta, HOJA_JEFES, COLUMNAS_JEFES)
    filas_pivot = leer_hoja(ruta, HOJA_PIVOT, 6)
    combinadas = leer_celdas_combinadas(ruta)

    enc_principal, cuerpo_principal = filas_principal[0], filas_principal[1:]
    enc_jefes, cuerpo_jefes = filas_jefes[0], filas_jefes[1:]

    personas, encabezados, resumen, vacias, etiquetas = construir_personas(cuerpo_principal, 2)
    matrimonios = agrupar_matrimonios(personas)
    jefes_personas = [
        (i + 2, f) for i, f in enumerate(cuerpo_jefes)
        if texto(f[J_APELLIDOS]) or texto(f[J_NOMBRES])
    ]

    incidencias = detectar_incidencias(personas, matrimonios, encabezados)
    inc_cruce, conteos_cruce, _celular_resuelto, _jefe_confirmado = reconciliar_hojas(
        personas, jefes_personas
    )
    incidencias.extend(inc_cruce)

    consagrados = [m for m in matrimonios if m.es_consagrado]
    no_consagrados = [m for m in matrimonios if not m.es_consagrado and m.es_sin_consagracion]
    sin_definir = [m for m in matrimonios if not m.es_consagrado and not m.es_sin_consagracion]
    jefes_mat = [m for m in matrimonios if m.es_jefe]

    circulos = sorted({p.circulo for p in personas if p.circulo})
    circulos_con_bloque = sorted({
        clave_circulo(m.circulo) for m in no_consagrados if m.circulo
    })

    estructura = {
        "archivo": ruta.name,
        "hojas": {
            HOJA_PRINCIPAL: {
                "rol": "fuente principal de personas",
                "filas_totales": len(filas_principal),
                "columnas_reales": COLUMNAS_PRINCIPAL,
                "encabezados": [str(v) if v is not None else None for v in enc_principal],
                "filas_persona": len(personas),
                "filas_encabezado_circulo": len(encabezados),
                "filas_resumen_descartadas": resumen,
                "filas_vacias": vacias,
                "filas_etiqueta_descartadas": etiquetas,
                "perfil_columnas": perfilar_columnas(cuerpo_principal, enc_principal, COLUMNAS_PRINCIPAL),
                "celdas_combinadas": auditar_combinadas(
                    combinadas.get(HOJA_PRINCIPAL, []), cuerpo_principal, 2, COLUMNAS_PRINCIPAL
                ),
            },
            HOJA_JEFES: {
                "rol": "listado operativo de jefes/educadores por circulo",
                "filas_totales": len(filas_jefes),
                "columnas_reales": COLUMNAS_JEFES,
                "encabezados": [str(v) if v is not None else None for v in enc_jefes],
                "filas_persona": len(jefes_personas),
                "grupos_declarados": sum(1 for f in cuerpo_jefes if texto(f[J_ORDEN])),
                "perfil_columnas": perfilar_columnas(cuerpo_jefes, enc_jefes, COLUMNAS_JEFES),
                "celdas_combinadas": auditar_combinadas(
                    combinadas.get(HOJA_JEFES, []), cuerpo_jefes, 2, COLUMNAS_JEFES
                ),
            },
            HOJA_PIVOT: {
                "rol": "tabla dinamica de conteo por circulo; excluir de la importacion",
                "filas_totales": len(filas_pivot),
                "muestra": [[str(v) if v is not None else None for v in f] for f in filas_pivot[:5]],
            },
        },
        "metricas": {
            "personas": len(personas),
            "personas_con_celular": sum(1 for p in personas if p.celular),
            "personas_sin_celular": sum(1 for p in personas if not p.celular),
            "celulares_distintos": len({p.celular for p in personas if p.celular}),
            "personas_con_ci": sum(1 for p in personas if p.ci),
            "personas_sin_ci": sum(1 for p in personas if not p.ci),
            "personas_consagradas": sum(1 for p in personas if p.es_consagrado),
            "personas_sin_consagracion": sum(1 for p in personas if p.es_sin_consagracion),
            "personas_sin_marca_consagracion": sum(
                1 for p in personas if not p.es_consagrado and not p.es_sin_consagracion
            ),
            "personas_viudas": sum(1 for p in personas if p.es_viudo),
            "personas_marca_no_ml": sum(1 for p in personas if p.marca_no_ml),
            "personas_con_observacion": sum(1 for p in personas if p.observacion),
            "personas_jefe": sum(1 for p in personas if p.es_jefe),
            "matrimonios": len(matrimonios),
            "matrimonios_de_dos": sum(1 for m in matrimonios if len(m.personas) == 2),
            "matrimonios_de_uno": sum(1 for m in matrimonios if len(m.personas) == 1),
            "matrimonios_consagrados": len(consagrados),
            "matrimonios_consagrados_unipersonales": sum(
                1 for m in consagrados if len(m.personas) == 1
            ),
            "matrimonios_no_consagrados": len(no_consagrados),
            "matrimonios_sin_definir": len(sin_definir),
            "matrimonios_jefe": len(jefes_mat),
            "matrimonios_jefe_consagrados": sum(1 for m in jefes_mat if m.es_consagrado),
            "matrimonios_jefe_no_consagrados": sum(
                1 for m in jefes_mat if not m.es_consagrado
            ),
            "circulos_distintos": len(circulos),
            "circulos_con_bloque_no_consagrado": len(circulos_con_bloque),
            "circulos_con_jefe": len({clave_circulo(m.circulo) for m in jefes_mat if m.circulo}),
            "jefes_en_listado": len(jefes_personas),
            "grupos_en_listado": sum(1 for f in cuerpo_jefes if texto(f[J_ORDEN])),
            "reconciliacion_listado_jefes": conteos_cruce,
        },
        "votos_maximos_estimados": {
            "MATRIMONIO_CONSAGRADO": len(consagrados),
            "BLOQUE_NO_CONSAGRADO": len(circulos_con_bloque),
            "total": len(consagrados) + len(circulos_con_bloque),
            "nota": "Estimacion previa a resolver las incidencias criticas; no es el padron final.",
        },
        "circulos": circulos,
        "incidencias_por_tipo": dict(Counter(i.tipo for i in incidencias)),
        "incidencias_por_severidad": dict(Counter(i.severidad for i in incidencias)),
    }
    return estructura, incidencias


def escribir_salidas(
    estructura: dict[str, Any], incidencias: list[IncidenciaDetectada], dir_salida: Path
) -> tuple[Path, Path]:
    dir_salida.mkdir(parents=True, exist_ok=True)
    ruta_csv = dir_salida / "padron_incidencias.csv"
    ruta_json = dir_salida / "padron_estructura.json"

    orden = {SEVERIDAD_CRITICA: 0, SEVERIDAD_ALTA: 1, SEVERIDAD_MEDIA: 2, SEVERIDAD_BAJA: 3}
    ordenadas = sorted(
        incidencias,
        key=lambda i: (orden.get(i.severidad, 9), i.tipo, str(i.fila_excel).rjust(6)),
    )
    with ruta_csv.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["tipo", "severidad", "hoja", "fila_excel", "circulo", "persona", "detalle"],
        )
        writer.writeheader()
        for i in ordenadas:
            writer.writerow(i.como_fila())

    with ruta_json.open("w", encoding="utf-8") as fh:
        json.dump(estructura, fh, ensure_ascii=False, indent=2)

    return ruta_csv, ruta_json


def imprimir_resumen(estructura: dict[str, Any]) -> None:
    m = estructura["metricas"]
    print(f"Archivo: {estructura['archivo']}")
    print("\n== Hojas ==")
    for nombre, datos in estructura["hojas"].items():
        print(f"  {nombre!r}: {datos['rol']} ({datos['filas_totales']} filas leidas)")
    print("\n== Personas ==")
    for clave in (
        "personas", "personas_con_celular", "personas_sin_celular", "celulares_distintos",
        "personas_sin_ci", "personas_consagradas", "personas_sin_consagracion",
        "personas_sin_marca_consagracion", "personas_viudas", "personas_jefe",
    ):
        print(f"  {clave:38s} {m[clave]}")
    print("\n== Matrimonios y grupos ==")
    for clave in (
        "matrimonios", "matrimonios_de_dos", "matrimonios_de_uno", "matrimonios_consagrados",
        "matrimonios_consagrados_unipersonales", "matrimonios_no_consagrados",
        "matrimonios_sin_definir", "matrimonios_jefe", "matrimonios_jefe_consagrados",
        "circulos_distintos", "circulos_con_jefe", "circulos_con_bloque_no_consagrado",
    ):
        print(f"  {clave:38s} {m[clave]}")
    print("\n== Votos maximos estimados ==")
    for clave, valor in estructura["votos_maximos_estimados"].items():
        print(f"  {clave:38s} {valor}")
    print("\n== Incidencias por severidad ==")
    for sev, n in sorted(estructura["incidencias_por_severidad"].items()):
        print(f"  {sev:38s} {n}")
    print("\n== Incidencias por tipo ==")
    for tipo, n in sorted(estructura["incidencias_por_tipo"].items(), key=lambda x: -x[1]):
        print(f"  {tipo:38s} {n}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--excel", type=Path, default=EXCEL_POR_DEFECTO)
    parser.add_argument("--salida", type=Path, default=DIR_SALIDA_POR_DEFECTO)
    args = parser.parse_args(argv)

    if not args.excel.exists():
        print(f"No se encontro el Excel: {args.excel}", file=sys.stderr)
        return 1

    estructura, incidencias = construir_estructura(args.excel)
    ruta_csv, ruta_json = escribir_salidas(estructura, incidencias, args.salida)
    imprimir_resumen(estructura)
    print(f"\nIncidencias: {ruta_csv}")
    print(f"Estructura:  {ruta_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
