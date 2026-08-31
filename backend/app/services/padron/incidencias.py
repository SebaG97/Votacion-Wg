"""Deteccion de incidencias y reconciliacion de las dos hojas (Mision 02).

La deteccion base fue portada sin cambios de conducta desde
`backend/scripts/explorar_padron.py`. Ver DEC-008 (celular compartido entre
conyuges), DEC-009 (reconciliacion), DEC-010 (jefe solo donde hay bloque no
consagrado) y DEC-017 (matrimonio sin ningun celular valido, agregado en la
Mision 04 a partir de la aclaracion textual del dueño del padron sobre
DEC-005).
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any

from app.services.padron.columnas import (
    HOJA_JEFES,
    HOJA_PRINCIPAL,
    J_APELLIDOS,
    J_CELULAR,
    J_CIRCULO,
    J_NOMBRES,
    P_CIRCULO,
    P_JEFES,
    P_MATRIMONIO,
    SEVERIDAD_ALTA,
    SEVERIDAD_BAJA,
    SEVERIDAD_CRITICA,
    SEVERIDAD_MEDIA,
)
from app.services.padron.dominio import IncidenciaDetectada, MatrimonioExcel, PersonaExcel
from app.services.padron.normalizacion import clave_circulo, clave_texto, es_marca, normalizar_celular, texto


def detectar_incidencias(
    personas: list[PersonaExcel],
    matrimonios: list[MatrimonioExcel],
    encabezados: list[tuple[int, tuple[Any, ...]]],
) -> list[IncidenciaDetectada]:
    inc: list[IncidenciaDetectada] = []

    def agregar(tipo, sev, hoja, fila, circulo, persona, detalle):
        inc.append(IncidenciaDetectada(tipo, sev, hoja, fila, circulo, persona, detalle))

    # --- celular -----------------------------------------------------------
    por_celular: dict[str, list[PersonaExcel]] = defaultdict(list)
    for p in personas:
        if p.celular:
            por_celular[p.celular].append(p)
        elif p.celular_motivo == "PLACEHOLDER_CERO":
            agregar(
                "CELULAR_PLACEHOLDER", SEVERIDAD_ALTA, HOJA_PRINCIPAL, p.fila,
                p.circulo, p.etiqueta,
                f"Celular cargado como {p.celular_crudo!r}: es marcador de 'no tiene', no un numero.",
            )
        elif p.celular_motivo == "FORMATO_INVALIDO":
            agregar(
                "CELULAR_FORMATO_INVALIDO", SEVERIDAD_ALTA, HOJA_PRINCIPAL, p.fila,
                p.circulo, p.etiqueta, f"Celular no interpretable: {p.celular_crudo!r}.",
            )
        else:
            agregar(
                "CELULAR_FALTANTE", SEVERIDAD_ALTA, HOJA_PRINCIPAL, p.fila,
                p.circulo, p.etiqueta, "Persona sin celular: no podra consultar habilitacion.",
            )

    filas_matrimonio: dict[int, MatrimonioExcel] = {}
    for m in matrimonios:
        for f in m.filas:
            filas_matrimonio[f] = m

    for cel, grupo in sorted(por_celular.items()):
        if len(grupo) < 2:
            continue
        mismo_matrimonio = len({id(filas_matrimonio.get(p.fila)) for p in grupo}) == 1
        tipo = "CELULAR_COMPARTIDO_CONYUGES" if mismo_matrimonio else "CELULAR_DUPLICADO"
        sev = SEVERIDAD_ALTA if mismo_matrimonio else SEVERIDAD_CRITICA
        detalle = "Celular repetido en filas " + ", ".join(str(p.fila) for p in grupo)
        detalle += " (" + " / ".join(p.etiqueta for p in grupo) + ")."
        if mismo_matrimonio:
            detalle += " Ambos son conyuges del mismo matrimonio."
        for p in grupo:
            agregar(tipo, sev, HOJA_PRINCIPAL, p.fila, p.circulo, p.etiqueta, f"{cel}: {detalle}")

    # --- CI ----------------------------------------------------------------
    for p in personas:
        if p.ci is None:
            sev = SEVERIDAD_BAJA if p.celular else SEVERIDAD_MEDIA
            agregar(
                "CI_FALTANTE", sev, HOJA_PRINCIPAL, p.fila, p.circulo, p.etiqueta,
                f"Sin CI utilizable (motivo: {p.ci_motivo}).",
            )
    por_ci: dict[str, list[PersonaExcel]] = defaultdict(list)
    for p in personas:
        if p.ci:
            por_ci[p.ci].append(p)
    for ci, grupo in sorted(por_ci.items()):
        if len(grupo) < 2:
            continue
        mismo_matrimonio = len({id(filas_matrimonio.get(p.fila)) for p in grupo}) == 1
        tipo = "CI_COPIADA_ENTRE_CONYUGES" if mismo_matrimonio else "CI_DUPLICADA"
        detalle = "CI repetida en filas " + ", ".join(str(p.fila) for p in grupo)
        detalle += " (" + " / ".join(p.etiqueta for p in grupo) + ")."
        if mismo_matrimonio:
            detalle += " Arrastre de la CI de un conyuge sobre el otro."
        for p in grupo:
            agregar(tipo, SEVERIDAD_MEDIA, HOJA_PRINCIPAL, p.fila, p.circulo, p.etiqueta, f"{ci}: {detalle}")

    # --- matrimonio / consagracion ----------------------------------------
    for m in matrimonios:
        if not texto(m.etiqueta):
            for p in m.personas:
                agregar(
                    "MATRIMONIO_SIN_ETIQUETA", SEVERIDAD_ALTA, HOJA_PRINCIPAL, p.fila,
                    p.circulo, p.etiqueta,
                    "Columna MATRIMONIO vacia: la persona no se puede agrupar con su conyuge.",
                )
        if len(m.personas) == 1:
            p = m.personas[0]
            if not p.es_viudo:
                agregar(
                    "MATRIMONIO_INCOMPLETO", SEVERIDAD_ALTA, HOJA_PRINCIPAL, p.fila,
                    p.circulo, p.etiqueta,
                    "Matrimonio con un solo integrante y sin marca de viudez.",
                )
        if len(m.personas) == 2:
            a, b = m.personas
            if a.es_consagrado != b.es_consagrado or a.es_sin_consagracion != b.es_sin_consagracion:
                agregar(
                    "CONSAGRACION_INCONSISTENTE", SEVERIDAD_CRITICA, HOJA_PRINCIPAL, a.fila,
                    m.circulo, f"{a.etiqueta} / {b.etiqueta}",
                    "Los dos conyuges tienen marcas de consagracion distintas: "
                    f"fila {a.fila} consagrado={a.es_consagrado} sin_consagracion={a.es_sin_consagracion}; "
                    f"fila {b.fila} consagrado={b.es_consagrado} sin_consagracion={b.es_sin_consagracion}.",
                )
            if clave_texto(a.nombres) and clave_texto(a.nombres) == clave_texto(b.nombres):
                agregar(
                    "NOMBRE_COPIADO_ENTRE_CONYUGES", SEVERIDAD_MEDIA, HOJA_PRINCIPAL, a.fila,
                    m.circulo, f"{a.etiqueta} / {b.etiqueta}",
                    f"Ambos conyuges figuran con el mismo nombre de pila ({a.nombres!r}).",
                )
        if not m.es_consagrado and not m.es_sin_consagracion:
            for p in m.personas:
                agregar(
                    "CONSAGRACION_SIN_DEFINIR", SEVERIDAD_CRITICA, HOJA_PRINCIPAL, p.fila,
                    p.circulo, p.etiqueta,
                    "Sin marca en 'Consagrados' ni en 'sin consagracion': no se puede asignar "
                    "unidad electoral.",
                )
        if not any(p.celular for p in m.personas):
            # Aclaracion textual del dueño del padron sobre DEC-005: si ningun
            # integrante tiene un celular valido (no None, no PLACEHOLDER_CERO,
            # no FORMATO_INVALIDO -- `PersonaExcel.celular` ya es None en los
            # tres casos), nadie puede consultar la habilitacion de esta unidad
            # electoral. Se evalua con el celular crudo de la hoja principal,
            # antes de la reconciliacion con LISTADO JEFES (DEC-009): esta es
            # la condicion real del matrimonio como pareja, no la del jefe que
            # eventualmente representa a su circulo.
            for p in m.personas:
                agregar(
                    "MATRIMONIO_SIN_CELULAR_DISPONIBLE", SEVERIDAD_CRITICA, HOJA_PRINCIPAL, p.fila,
                    p.circulo, p.etiqueta,
                    "Ningun integrante del matrimonio tiene un celular valido: no se puede "
                    "consultar habilitacion para esta unidad electoral (DEC-017).",
                )

    # --- identidad de la persona ------------------------------------------
    for p in personas:
        texto_nombre = " ".join(x for x in (p.apellidos, p.nombres) if x)
        if texto_nombre and not re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", texto_nombre):
            agregar(
                "NOMBRE_NO_ALFABETICO", SEVERIDAD_ALTA, HOJA_PRINCIPAL, p.fila, p.circulo,
                p.etiqueta,
                f"Las columnas de nombre contienen {texto_nombre!r}: dato cargado en la "
                "columna equivocada.",
            )

    # --- circulo -----------------------------------------------------------
    for p in personas:
        if not p.circulo:
            agregar(
                "CIRCULO_FALTANTE", SEVERIDAD_ALTA, HOJA_PRINCIPAL, p.fila, None, p.etiqueta,
                "Persona sin circulo asignado.",
            )

    etiquetas_circulo = sorted({p.circulo for p in personas if p.circulo})
    claves = {c: clave_circulo(c) for c in etiquetas_circulo}
    for a in etiquetas_circulo:
        for b in etiquetas_circulo:
            if a is b or claves[a] is None or claves[b] is None:
                continue
            if claves[a] != claves[b] and claves[b].startswith(claves[a] + " "):
                agregar(
                    "CIRCULO_ETIQUETA_VARIANTE", SEVERIDAD_MEDIA, HOJA_PRINCIPAL, "-", a, None,
                    f"{a!r} parece una escritura abreviada de {b!r}: normalizar antes de agrupar.",
                )

    # --- jefes -------------------------------------------------------------
    # Solo importa el jefe donde hay bloque no consagrado: un circulo integramente
    # consagrado vota matrimonio por matrimonio y no necesita representante.
    circulos_con_jefe = {clave_circulo(m.circulo) for m in matrimonios if m.es_jefe}
    circulos_con_bloque = {
        clave_circulo(m.circulo)
        for m in matrimonios
        if m.circulo and not m.es_consagrado
    }
    for c in etiquetas_circulo:
        if claves[c] in circulos_con_bloque and claves[c] not in circulos_con_jefe:
            agregar(
                "CIRCULO_SIN_JEFE", SEVERIDAD_CRITICA, HOJA_PRINCIPAL, "-", c, None,
                "El circulo tiene matrimonios no consagrados pero ningun integrante lleva la "
                "marca 'Jefes': el bloque no consagrado quedaria sin representante habilitado.",
            )

    for nro, fila in encabezados:
        if es_marca(fila[P_JEFES]):
            agregar(
                "JEFE_SIN_PERSONA_EN_PADRON", SEVERIDAD_CRITICA, HOJA_PRINCIPAL, nro,
                texto(fila[P_CIRCULO]), texto(fila[P_MATRIMONIO]),
                "La marca 'Jefes' esta en la fila separadora del circulo y el matrimonio jefe "
                "no tiene filas de persona (sin celular ni CI en la hoja principal).",
            )

    return inc


def reconciliar_hojas(
    personas: list[PersonaExcel], jefes_filas: list[tuple[int, tuple[Any, ...]]]
) -> tuple[list[IncidenciaDetectada], dict[str, Any], dict[int, str], set[int]]:
    """Reconciliacion en cascada de DEC-009 / PADRON_ANALISIS.md 6.2.

    Ademas de las incidencias y los conteos por paso de la cascada, devuelve:

    - `celular_resuelto_por_fila`: el celular de `LISTADO JEFES` para cada fila
      de la hoja principal que matcheo por nombre+celular o solo por nombre
      (pasos 1 y 2) y no tenia celular propio, para que el importador pueda
      completarlo. El paso 3 (solo nombre, celular discrepante) NO se incluye
      a proposito: DEC-009 exige confirmacion humana antes de aceptar ese
      celular.
    - `personas_jefe_confirmado`: filas de la hoja principal cuya persona
      quedo confirmada como jefe/educador por `LISTADO JEFES` via los pasos 1,
      2 o 3 de la cascada (con o sin completar celular). Es lo que le da jefe
      habilitable a un circulo cuya marca `Jefes` de la hoja principal esta en
      la fila separadora en vez de en una fila de persona (DEC-009).
    """
    inc: list[IncidenciaDetectada] = []
    por_nombre: dict[tuple[str | None, str | None], list[PersonaExcel]] = defaultdict(list)
    por_celular: dict[str, list[PersonaExcel]] = defaultdict(list)
    for p in personas:
        por_nombre[(clave_texto(p.apellidos), clave_texto(p.nombres))].append(p)
        if p.celular:
            por_celular[p.celular].append(p)

    conteos: Counter = Counter()
    nombres_jefes: set[tuple[str | None, str | None]] = set()
    celulares_jefes: set[str] = set()
    celular_resuelto_por_fila: dict[int, str] = {}
    personas_jefe_confirmado: set[int] = set()

    # Duplicados internos de LISTADO JEFES: dos jefes distintos con el mismo
    # numero bloquearian la habilitacion por celular.
    jefes_por_celular: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for nro, fila in jefes_filas:
        cel, _ = normalizar_celular(fila[J_CELULAR])
        if not cel:
            continue
        etq = " ".join(
            x for x in (texto(fila[J_APELLIDOS]), texto(fila[J_NOMBRES])) if x
        ) or "(sin nombre)"
        jefes_por_celular[cel].append((nro, etq))
    for cel, grupo in sorted(jefes_por_celular.items()):
        if len(grupo) < 2:
            continue
        for nro, etq in grupo:
            inc.append(IncidenciaDetectada(
                "CELULAR_DUPLICADO_EN_LISTADO_JEFES", SEVERIDAD_CRITICA, HOJA_JEFES, nro, None, etq,
                f"{cel} figura en las filas "
                + ", ".join(f"{n} ({e})" for n, e in grupo)
                + ": no se puede resolver a que bloque habilita.",
            ))

    for nro, fila in jefes_filas:
        apellidos, nombres = texto(fila[J_APELLIDOS]), texto(fila[J_NOMBRES])
        circulo = texto(fila[J_CIRCULO])
        etiqueta = " ".join(x for x in (apellidos, nombres) if x) or "(sin nombre)"
        clave = (clave_texto(apellidos), clave_texto(nombres))
        cel, _ = normalizar_celular(fila[J_CELULAR])
        nombres_jefes.add(clave)
        if cel:
            celulares_jefes.add(cel)

        por_n = por_nombre.get(clave, [])
        por_c = por_celular.get(cel, []) if cel else []
        if por_n and por_c:
            conteos["match_nombre_y_celular"] += 1
            for p in por_n:
                personas_jefe_confirmado.add(p.fila)
                if cel and not p.celular:
                    celular_resuelto_por_fila[p.fila] = cel
        elif por_n:
            conteos["match_solo_nombre"] += 1
            for p in por_n:
                personas_jefe_confirmado.add(p.fila)
                if p.celular and cel and p.celular != cel:
                    inc.append(IncidenciaDetectada(
                        "CELULAR_DISCREPANTE_ENTRE_HOJAS", SEVERIDAD_CRITICA, HOJA_JEFES, nro,
                        circulo, etiqueta,
                        f"LISTADO JEFES tiene {fila[J_CELULAR]!r} y la hoja principal "
                        f"(fila {p.fila}) tiene {p.celular_crudo!r}.",
                    ))
                elif not p.celular and cel:
                    celular_resuelto_por_fila[p.fila] = cel
        elif por_c:
            conteos["match_solo_celular"] += 1
            for p in por_c:
                personas_jefe_confirmado.add(p.fila)
            inc.append(IncidenciaDetectada(
                "NOMBRE_DISCREPANTE_ENTRE_HOJAS", SEVERIDAD_BAJA, HOJA_JEFES, nro, circulo, etiqueta,
                "Coincide el celular con la hoja principal (fila "
                + ", ".join(str(p.fila) for p in por_c)
                + ") pero la escritura del nombre difiere.",
            ))
        else:
            conteos["sin_match"] += 1
            inc.append(IncidenciaDetectada(
                "JEFE_SOLO_EN_LISTADO_JEFES", SEVERIDAD_CRITICA, HOJA_JEFES, nro, circulo, etiqueta,
                "Jefe presente en LISTADO JEFES sin correspondencia por nombre ni por celular "
                "en la hoja principal.",
            ))

    for p in personas:
        if not p.es_jefe:
            continue
        clave = (clave_texto(p.apellidos), clave_texto(p.nombres))
        if clave in nombres_jefes:
            continue
        if p.celular and p.celular in celulares_jefes:
            continue
        inc.append(IncidenciaDetectada(
            "JEFE_SOLO_EN_HOJA_PRINCIPAL", SEVERIDAD_ALTA, HOJA_PRINCIPAL, p.fila, p.circulo,
            p.etiqueta,
            "Marcado como jefe en la hoja principal pero ausente de LISTADO JEFES.",
        ))

    return inc, dict(conteos), celular_resuelto_por_fila, personas_jefe_confirmado
