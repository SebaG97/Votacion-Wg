"""Importador real del padron (Mision 04).

Persiste personas, matrimonios, grupos, unidades electorales e incidencias en
base de datos a partir del Excel ya validado en la Mision 02
(`docs/PADRON_ANALISIS.md`), reusando la logica de `app.services.padron.analisis`.

Reglas de negocio pendientes (DEC-012, DEC-013, DEC-014): el importador NO las
resuelve. Importa todo y genera las unidades electorales igual, pero las dos
que dependen de una decision de negocio quedan con un estado que las distingue
(`PENDIENTE_DEFINICION_POSTULANTES`, `PENDIENTE_DEFINICION_BAJA`) en vez de
`HABILITADA`, para que aplicar la decision del negocio despues sea un UPDATE y
no una reimportacion (ver DEC-016).
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import (
    Grupo,
    ImportacionPadron,
    IncidenciaPadron,
    Matrimonio,
    Persona,
    UnidadElectoral,
    Votacion,
    Voto,
)
from app.models.enums import (
    EstadoImportacion,
    EstadoPersona,
    EstadoVotacion,
    SeveridadIncidencia,
    TipoIncidenciaPadron,
    TipoUnidadElectoral,
)
from app.models.enums import EstadoUnidadElectoral as Estado
from app.services.padron.analisis import ResultadoAnalisis, analizar_excel
from app.services.padron.columnas import HOJA_PRINCIPAL
from app.services.padron.dominio import MatrimonioExcel, PersonaExcel
from app.services.padron.normalizacion import clave_circulo, clave_texto


class ImportacionRechazadaError(RuntimeError):
    """La votacion asociada ya esta abierta o cerrada: no se puede reimportar."""


def _hay_votacion_bloqueante(db: Session) -> Votacion | None:
    return db.query(Votacion).filter(Votacion.estado != EstadoVotacion.BORRADOR).first()


def _vaciar_padron_actual(db: Session) -> None:
    """Borra todo lo generado por una corrida previa del importador.

    Solo se llama despues de confirmar que no hay ninguna votacion mas alla de
    BORRADOR (DEC-015): en ese estado no puede haber votos reales todavia, asi
    que el reemplazo total es seguro. El orden de borrado respeta las FK,
    incluida la referencia circular `personas.matrimonio_id` <->
    `matrimonios.integrante_1_id/integrante_2_id`.
    """
    db.query(Voto).delete(synchronize_session=False)
    db.query(IncidenciaPadron).delete(synchronize_session=False)
    db.query(UnidadElectoral).delete(synchronize_session=False)
    db.execute(update(Persona).values(matrimonio_id=None))
    db.query(Matrimonio).delete(synchronize_session=False)
    db.query(Persona).delete(synchronize_session=False)
    db.query(Grupo).delete(synchronize_session=False)
    db.flush()


def _es_circulo_postulantes(nombre_circulo: str | None) -> bool:
    clave = clave_texto(nombre_circulo) or ""
    return "POSTULANTE" in clave


def _resolver_estado_persona(p: PersonaExcel) -> tuple[EstadoPersona, str | None]:
    if p.marca_no_ml:
        return EstadoPersona.BAJA_NO_ML, p.observacion
    if p.observacion:
        return EstadoPersona.BAJA_OBSERVACION, p.observacion
    return EstadoPersona.ACTIVA, None


def _crear_grupos(db: Session, resultado: ResultadoAnalisis) -> dict[str, Grupo]:
    """Un `Grupo` por clave de circulo normalizada (DEC-006 3.4).

    Se agrupa por `clave_circulo` (no por el texto crudo) para blindar el
    `UNIQUE` de `grupos.nombre_normalizado` ante dos etiquetas que, pese a ser
    distintas en el Excel, normalizaran igual. En los datos reales esto no
    reduce el conteo de 93 circulos (verificado en la corrida contra el Excel
    real), pero evita un `IntegrityError` si algun dia deja de ser cierto.
    """
    nombre_por_clave: dict[str, str] = {}
    for p in resultado.personas:
        if not p.circulo:
            continue
        clave = clave_circulo(p.circulo)
        if clave is None:
            continue
        nombre_por_clave.setdefault(clave, p.circulo)

    grupos_por_clave: dict[str, Grupo] = {}
    for clave, nombre in sorted(nombre_por_clave.items()):
        grupo = Grupo(nombre=nombre, nombre_normalizado=clave)
        db.add(grupo)
        grupos_por_clave[clave] = grupo
    db.flush()
    return grupos_por_clave


def _crear_personas(
    db: Session, resultado: ResultadoAnalisis, grupos_por_clave: dict[str, Grupo]
) -> dict[int, Persona]:
    orm_por_fila: dict[int, Persona] = {}
    for p in resultado.personas:
        celular = p.celular
        if not celular:
            celular = resultado.celular_resuelto_por_fila.get(p.fila)

        estado, observacion_baja = _resolver_estado_persona(p)
        grupo = grupos_por_clave.get(clave_circulo(p.circulo)) if p.circulo else None
        es_jefe_grupo = p.es_jefe or p.fila in resultado.personas_jefe_confirmado

        persona = Persona(
            nombres=p.nombres or "",
            apellidos=p.apellidos or "",
            celular=celular,
            documento=p.ci,
            estado=estado,
            observacion_baja=observacion_baja,
            grupo_id=grupo.id if grupo else None,
            es_jefe_grupo=es_jefe_grupo,
        )
        db.add(persona)
        orm_por_fila[p.fila] = persona
    db.flush()
    return orm_por_fila


def _resolver_es_consagrado(m: MatrimonioExcel) -> bool | None:
    if m.es_consagrado:
        return True
    if m.es_sin_consagracion:
        return False
    return None


def _crear_matrimonios(
    db: Session,
    resultado: ResultadoAnalisis,
    orm_personas_por_fila: dict[int, Persona],
    grupos_por_clave: dict[str, Grupo],
) -> list[tuple[MatrimonioExcel, Matrimonio]]:
    pares: list[tuple[MatrimonioExcel, Matrimonio]] = []
    for m in resultado.matrimonios:
        integrante_1 = orm_personas_por_fila[m.filas[0]]
        integrante_2 = orm_personas_por_fila[m.filas[1]] if len(m.filas) == 2 else None
        grupo = grupos_por_clave.get(clave_circulo(m.circulo)) if m.circulo else None

        matrimonio = Matrimonio(
            codigo_externo=m.etiqueta,
            integrante_1_id=integrante_1.id,
            integrante_2_id=integrante_2.id if integrante_2 else None,
            es_consagrado=_resolver_es_consagrado(m),
            grupo_id=grupo.id if grupo else None,
        )
        db.add(matrimonio)
        pares.append((m, matrimonio))
    db.flush()

    for m, matrimonio in pares:
        for fila in m.filas:
            orm_personas_por_fila[fila].matrimonio_id = matrimonio.id
    db.flush()

    return pares


def _crear_incidencias(
    db: Session,
    resultado: ResultadoAnalisis,
    importacion: ImportacionPadron,
    orm_personas_por_fila: dict[int, Persona],
    grupos_por_clave: dict[str, Grupo],
) -> list[IncidenciaPadron]:
    """Persiste cada `IncidenciaDetectada`. `persona_id` solo se resuelve para
    incidencias de la hoja principal: un numero de fila de `LISTADO JEFES` no
    es comparable con uno de la hoja principal (las dos hojas numeran sus
    propias filas desde 2)."""
    creadas: list[IncidenciaPadron] = []
    for inc in resultado.incidencias:
        persona_id = None
        if inc.hoja == HOJA_PRINCIPAL and isinstance(inc.fila_excel, int):
            persona = orm_personas_por_fila.get(inc.fila_excel)
            persona_id = persona.id if persona else None

        grupo_id = None
        if inc.circulo:
            grupo = grupos_por_clave.get(clave_circulo(inc.circulo))
            grupo_id = grupo.id if grupo else None

        descripcion = (
            f"Hoja: {inc.hoja} | Fila: {inc.fila_excel} | Circulo: {inc.circulo or '-'} | "
            f"Persona: {inc.persona or '-'} | {inc.detalle}"
        )

        registro = IncidenciaPadron(
            tipo=TipoIncidenciaPadron(inc.tipo),
            severidad=SeveridadIncidencia(inc.severidad),
            descripcion=descripcion,
            persona_id=persona_id,
            grupo_id=grupo_id,
            importacion_id=importacion.id,
        )
        db.add(registro)
        creadas.append(registro)
    db.flush()
    return creadas


def _personas_con_incidencia_critica(incidencias: list[IncidenciaPadron]) -> set[int]:
    return {
        i.persona_id
        for i in incidencias
        if i.severidad == SeveridadIncidencia.CRITICA and i.persona_id is not None
    }


def _personas_jefe_por_grupo(orm_personas_por_fila: dict[int, Persona]) -> dict[int, set[int]]:
    resultado: dict[int, set[int]] = {}
    for persona in orm_personas_por_fila.values():
        if persona.es_jefe_grupo and persona.grupo_id is not None:
            resultado.setdefault(persona.grupo_id, set()).add(persona.id)
    return resultado


def _grupos_con_incidencia_de_jefe_o_circulo(
    incidencias: list[IncidenciaPadron], personas_jefe_por_grupo: dict[int, set[int]]
) -> set[int]:
    """Circulos con una incidencia CRITICA que compromete al bloque no consagrado
    (DEC-019): sobre el circulo en si (`persona_id IS NULL`, p.ej. `CIRCULO_SIN_JEFE`
    o `JEFE_SIN_PERSONA_EN_PADRON`) o sobre alguno de sus jefes. Una incidencia
    con `grupo_id` de este circulo pero `persona_id` de alguien que no es jefe
    -- por ejemplo, un matrimonio consagrado del mismo circulo con su propio
    problema -- no compromete al bloque: ese problema es de ese matrimonio, no
    del bloque que representa el jefe.
    """
    grupos: set[int] = set()
    for i in incidencias:
        if i.severidad != SeveridadIncidencia.CRITICA or i.grupo_id is None:
            continue
        if i.persona_id is None or i.persona_id in personas_jefe_por_grupo.get(i.grupo_id, set()):
            grupos.add(i.grupo_id)
    return grupos


def _crear_unidades_electorales(
    db: Session,
    resultado: ResultadoAnalisis,
    pares_matrimonio: list[tuple[MatrimonioExcel, Matrimonio]],
    grupos_por_clave: dict[str, Grupo],
    orm_personas_por_fila: dict[int, Persona],
    incidencias_orm: list[IncidenciaPadron],
) -> list[UnidadElectoral]:
    personas_con_critica = _personas_con_incidencia_critica(incidencias_orm)
    personas_jefe_por_grupo = _personas_jefe_por_grupo(orm_personas_por_fila)
    grupos_con_critica_de_bloque = _grupos_con_incidencia_de_jefe_o_circulo(
        incidencias_orm, personas_jefe_por_grupo
    )

    unidades: list[UnidadElectoral] = []

    # --- MATRIMONIO_CONSAGRADO: una por matrimonio consagrado (DEC-011). ---
    # Se bloquea unicamente por una incidencia CRITICA sobre sus propios
    # integrantes (DEC-019): lo que le pase a otro matrimonio del mismo
    # circulo no compromete su elegibilidad.
    for m, matrimonio in pares_matrimonio:
        if matrimonio.es_consagrado is not True:
            continue

        integrantes_ids = {orm_personas_por_fila[f].id for f in m.filas}
        tiene_critica = bool(integrantes_ids & personas_con_critica)
        personas_matrimonio = [orm_personas_por_fila[f] for f in m.filas]
        todos_de_baja = all(p.estado != EstadoPersona.ACTIVA for p in personas_matrimonio)

        if tiene_critica:
            estado = Estado.BLOQUEADA_POR_INCIDENCIA.value
        elif todos_de_baja:
            estado = Estado.PENDIENTE_DEFINICION_BAJA.value
        else:
            estado = Estado.HABILITADA.value

        unidad = UnidadElectoral(
            tipo=TipoUnidadElectoral.MATRIMONIO_CONSAGRADO,
            referencia_id=matrimonio.id,
            grupo_id=matrimonio.grupo_id,
            descripcion=f"Matrimonio consagrado: {m.etiqueta or '(sin etiqueta)'}",
            cantidad_personas_control=len(m.filas),
            estado=estado,
        )
        db.add(unidad)
        unidades.append(unidad)

    # --- BLOQUE_NO_CONSAGRADO: uno por circulo con matrimonio no consagrado. -
    # Se bloquea unicamente por una incidencia CRITICA sobre el circulo en si
    # o sobre alguno de sus jefes (DEC-019): una incidencia de un matrimonio
    # consagrado puntual del mismo circulo no compromete al bloque.
    matrimonios_no_consagrados_por_grupo: dict[int, list[tuple[MatrimonioExcel, Matrimonio]]] = {}
    for m, matrimonio in pares_matrimonio:
        if matrimonio.es_consagrado is not False or matrimonio.grupo_id is None:
            continue
        matrimonios_no_consagrados_por_grupo.setdefault(matrimonio.grupo_id, []).append((m, matrimonio))

    for grupo in grupos_por_clave.values():
        pares_grupo = matrimonios_no_consagrados_por_grupo.get(grupo.id)
        if not pares_grupo:
            continue

        tiene_critica = grupo.id in grupos_con_critica_de_bloque
        es_postulantes = _es_circulo_postulantes(grupo.nombre)

        personas_bloque = [
            orm_personas_por_fila[f]
            for m, _ in pares_grupo
            for f in m.filas
        ]
        todos_de_baja = bool(personas_bloque) and all(
            p.estado != EstadoPersona.ACTIVA for p in personas_bloque
        )

        if tiene_critica:
            estado = Estado.BLOQUEADA_POR_INCIDENCIA.value
        elif es_postulantes:
            estado = Estado.PENDIENTE_DEFINICION_POSTULANTES.value
        elif todos_de_baja:
            estado = Estado.PENDIENTE_DEFINICION_BAJA.value
        else:
            estado = Estado.HABILITADA.value

        unidad = UnidadElectoral(
            tipo=TipoUnidadElectoral.BLOQUE_NO_CONSAGRADO,
            referencia_id=grupo.id,
            grupo_id=grupo.id,
            descripcion=f"Bloque no consagrado de {grupo.nombre}",
            cantidad_personas_control=len(pares_grupo),
            estado=estado,
        )
        db.add(unidad)
        unidades.append(unidad)

    db.flush()
    return unidades


def _construir_resumen(
    resultado: ResultadoAnalisis,
    orm_personas_por_fila: dict[int, Persona],
    pares_matrimonio: list[tuple[MatrimonioExcel, Matrimonio]],
    grupos_por_clave: dict[str, Grupo],
    unidades: list[UnidadElectoral],
    incidencias_orm: list[IncidenciaPadron],
) -> dict:
    personas_por_estado: dict[str, int] = {}
    for p in orm_personas_por_fila.values():
        personas_por_estado[p.estado.value] = personas_por_estado.get(p.estado.value, 0) + 1

    matrimonios_por_consagracion = {"consagrado": 0, "no_consagrado": 0, "sin_definir": 0}
    for _, matrimonio in pares_matrimonio:
        if matrimonio.es_consagrado is True:
            matrimonios_por_consagracion["consagrado"] += 1
        elif matrimonio.es_consagrado is False:
            matrimonios_por_consagracion["no_consagrado"] += 1
        else:
            matrimonios_por_consagracion["sin_definir"] += 1

    unidades_por_tipo: dict[str, int] = {}
    unidades_por_estado: dict[str, int] = {}
    votos_maximos_por_tipo: dict[str, int] = {}
    votos_maximos_por_grupo: dict[str, int] = {}
    for u in unidades:
        unidades_por_tipo[u.tipo.value] = unidades_por_tipo.get(u.tipo.value, 0) + 1
        unidades_por_estado[u.estado] = unidades_por_estado.get(u.estado, 0) + 1
        if u.estado == Estado.HABILITADA.value:
            votos_maximos_por_tipo[u.tipo.value] = votos_maximos_por_tipo.get(u.tipo.value, 0) + 1
            nombre_grupo = next(
                (g.nombre for g in grupos_por_clave.values() if g.id == u.grupo_id), "(sin circulo)"
            )
            votos_maximos_por_grupo[nombre_grupo] = votos_maximos_por_grupo.get(nombre_grupo, 0) + 1

    incidencias_por_severidad: dict[str, int] = {}
    incidencias_por_tipo: dict[str, int] = {}
    for i in incidencias_orm:
        incidencias_por_severidad[i.severidad.value] = (
            incidencias_por_severidad.get(i.severidad.value, 0) + 1
        )
        incidencias_por_tipo[i.tipo.value] = incidencias_por_tipo.get(i.tipo.value, 0) + 1

    return {
        "personas": {"total": len(orm_personas_por_fila), "por_estado": personas_por_estado},
        "matrimonios": {"total": len(pares_matrimonio), **matrimonios_por_consagracion},
        "grupos": {"total": len(grupos_por_clave)},
        "unidades_electorales": {
            "total": len(unidades),
            "por_tipo": unidades_por_tipo,
            "por_estado": unidades_por_estado,
        },
        "incidencias": {
            "total": len(incidencias_orm),
            "por_severidad": incidencias_por_severidad,
            "por_tipo": incidencias_por_tipo,
        },
        "reconciliacion_listado_jefes": resultado.reconciliacion_conteos,
        "votos_maximos": {
            "por_tipo": votos_maximos_por_tipo,
            "por_grupo": votos_maximos_por_grupo,
            "total": sum(votos_maximos_por_tipo.values()),
        },
    }


def _persistir(db: Session, resultado: ResultadoAnalisis, importacion: ImportacionPadron) -> dict:
    _vaciar_padron_actual(db)

    grupos_por_clave = _crear_grupos(db, resultado)
    orm_personas_por_fila = _crear_personas(db, resultado, grupos_por_clave)
    pares_matrimonio = _crear_matrimonios(db, resultado, orm_personas_por_fila, grupos_por_clave)
    incidencias_orm = _crear_incidencias(
        db, resultado, importacion, orm_personas_por_fila, grupos_por_clave
    )
    unidades = _crear_unidades_electorales(
        db, resultado, pares_matrimonio, grupos_por_clave, orm_personas_por_fila, incidencias_orm
    )

    return _construir_resumen(
        resultado, orm_personas_por_fila, pares_matrimonio, grupos_por_clave, unidades, incidencias_orm
    )


def ejecutar_importacion(
    db: Session, ruta_excel: Path, usuario: str | None = None
) -> ImportacionPadron:
    """Corre el importador completo dentro de una transaccion.

    Rechaza la corrida si existe una votacion mas alla de BORRADOR (DEC-015).
    Si no, reemplaza por completo lo generado por una corrida anterior
    (idempotente) y vuelve a generar personas, matrimonios, grupos, unidades
    electorales e incidencias desde cero.
    """
    votacion_bloqueante = _hay_votacion_bloqueante(db)
    if votacion_bloqueante is not None:
        raise ImportacionRechazadaError(
            f"La votacion {votacion_bloqueante.id} ({votacion_bloqueante.nombre!r}) esta en "
            f"estado {votacion_bloqueante.estado.value}: no se puede reimportar el padron "
            "mientras haya una votacion abierta o cerrada."
        )

    if not ruta_excel.exists():
        raise FileNotFoundError(f"No se encontro el Excel del padron: {ruta_excel}")

    importacion = ImportacionPadron(
        archivo_origen=str(ruta_excel),
        usuario=usuario,
        estado=EstadoImportacion.EN_PROCESO,
    )
    db.add(importacion)
    db.commit()
    db.refresh(importacion)

    try:
        resultado = analizar_excel(ruta_excel)
        resumen = _persistir(db, resultado, importacion)
        importacion.estado = EstadoImportacion.COMPLETADA
        importacion.resumen = resumen
        db.commit()
    except Exception as exc:
        db.rollback()
        importacion.estado = EstadoImportacion.FALLIDA
        importacion.error = str(exc)
        db.commit()
        raise

    return importacion
