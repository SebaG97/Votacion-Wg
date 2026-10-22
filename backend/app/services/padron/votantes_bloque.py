"""Quien vota cada bloque no consagrado (DEC-042).

Reglas confirmadas por el responsable del padron (22/10/2026):

1. Un solo voto por grupo (o agrupacion) de no consagrados.
2. Si todos los del grupo son postulantes y tienen educador, el bloque lo vota
   el educador. El educador figura en la fila separadora al inicio de cada
   lista de grupo del Excel; es un matrimonio consagrado de otro circulo y su
   celular esta en el circulo del que es miembro.
3. Si el grupo tiene una parte de consagrados y otra de postulantes, cada
   consagrado vota por su matrimonio y el jefe del grupo vota por los
   postulantes. En el padron esa parte consagrada quedo como un circulo
   aparte (".../64", "CIRCULO 58", ...), y a veces el jefe esta ahi.

Si el educador esta de baja o el grupo no tiene educador, vota el jefe del
propio circulo; si tampoco hay jefe activo, el bloque no vota.

La fila separadora del Excel trae el educador como texto libre ("Betty y
Gilberto Gauto"), asi que la correspondencia con el padron se fijo a mano,
por los apellidos de los dos integrantes del matrimonio, y queda aca para que
una reimportacion la vuelva a aplicar.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from app.models import Grupo, IncidenciaPadron, Matrimonio, Persona, UnidadElectoral
from app.models.enums import (
    EstadoPersona,
    EstadoUnidadElectoral,
    TipoIncidenciaPadron,
    TipoUnidadElectoral,
)
from app.services.padron.importador import _es_circulo_postulantes
from app.services.padron.normalizacion import clave_circulo, clave_texto

USUARIO_REGLA = "DEC-042"

# Clave de circulo del bloque -> apellidos de los dos integrantes del
# matrimonio educador.
EDUCADORES: dict[str, tuple[str, str]] = {
    "CIRCULO 2020 D": ("AQUINO", "ARGUELLO"),
    "POSTULANTES 2022 B": ("GAUTO", "BORJA"),
    "POSTULANTES 2022 C": ("BARRIOS", "ZARACHO"),
    "POSTULANTES 2022 D": ("FERNANDEZ", "FLORENTIN"),
    "POSTULANTES 2023 A": ("PEFAUR", "CALVO"),
    "POSTULANTES 2023 B": ("ORTIGOZA", "CHAMORRO"),
    "POSTULANTES 2023 C": ("BRITOS", "CACERES"),
    "POSTULANTES 2023 D": ("GONZALEZ", "BRIZUELA"),
    "POSTULANTES 2023 E": ("GONZALEZ", "LEGAL"),
    "POSTULANTES 2023 F": ("MORALES", "HELMAN"),
    "POSTULANTES 2024 A": ("KRISKOVICH", "SIMON"),
    "POSTULANTES 2024 B": ("MARTINEZ", "PERITO"),
    "POSTULANTES 2024 C": ("FLORENTIN", "ALEGRE"),
    "POSTULANTES 2024 D": ("SOSA", "RAMIREZ"),
    "POSTULANTES 2024 E": ("GONZALEZ", "PECHIN"),
    "POSTULANTES 2024 F": ("BLASSER", "MENDEZ"),
    "POSTULANTES 2025 A": ("PEREZ", "BITTAR"),
    "POSTULANTES 2026 A": ("VELAZQUEZ", "PAMPLIEGA"),
    "POSTULANTES 2026 B": ("AYALA", "LOPEZ"),
    "POSTULANTES 2026 C": ("GAMARRA", "GOMEZ"),
    "POSTULANTES 2026 D": ("VERA", "MARTINEZ"),
}

# Grupos mixtos cuyo jefe quedo en la parte consagrada: clave del bloque de
# postulantes -> clave del circulo donde esta el jefe.
JEFE_EN_OTRO_CIRCULO: dict[str, str] = {
    "CIRCULO 2019 A": "CIRCULO 58",
    "POSTULANTE 2019 C": "CIRCULO 2019 C /C60",
    "POSTULANTE 2021 A1": "POSTULANTES 2021 A /63",
    "POSTULANTES 2021 C": "POSTULANTES 2021 C /64",
    "POSTULANTES 2021 D": "POSTULANTES 2021 D /65",
}

# Incidencias que solo dicen "este circulo no tiene jefe": dejan de bloquear
# cuando el bloque ya tiene quien lo vote.
_INCIDENCIAS_DE_JEFATURA = {
    TipoIncidenciaPadron.CIRCULO_SIN_JEFE,
    TipoIncidenciaPadron.JEFE_SIN_PERSONA_EN_PADRON,
    TipoIncidenciaPadron.JEFE_SOLO_EN_LISTADO_JEFES,
}


def _tiene_integrante_activo(db: Session, matrimonio_id: int) -> bool:
    return (
        db.query(Persona)
        .filter(Persona.matrimonio_id == matrimonio_id, Persona.estado == EstadoPersona.ACTIVA)
        .count()
        > 0
    )


def _matrimonio_por_apellidos(db: Session, apellidos: tuple[str, str]) -> Matrimonio | None:
    buscados = sorted(clave_texto(a) for a in apellidos)
    candidatos = [
        m
        for m in db.query(Matrimonio).filter(Matrimonio.integrante_2_id.is_not(None)).all()
        if sorted(
            clave_texto(p.apellidos) or ""
            for p in db.query(Persona).filter(Persona.matrimonio_id == m.id).all()
        )
        == buscados
    ]
    return candidatos[0] if len(candidatos) == 1 else None


def _grupo_por_clave(db: Session, clave: str) -> Grupo | None:
    for grupo in db.query(Grupo).all():
        if clave_circulo(grupo.nombre) == clave:
            return grupo
    return None


def _votante_asignado(db: Session, grupo: Grupo) -> int | None:
    clave = clave_circulo(grupo.nombre)
    if clave in EDUCADORES:
        educador = _matrimonio_por_apellidos(db, EDUCADORES[clave])
        if educador is not None and _tiene_integrante_activo(db, educador.id):
            return educador.id
        return None
    if clave in JEFE_EN_OTRO_CIRCULO:
        otro = _grupo_por_clave(db, JEFE_EN_OTRO_CIRCULO[clave])
        if otro is None:
            return None
        jefe = (
            db.query(Persona)
            .filter(
                Persona.grupo_id == otro.id,
                Persona.es_jefe_grupo.is_(True),
                Persona.estado == EstadoPersona.ACTIVA,
                Persona.matrimonio_id.is_not(None),
            )
            .order_by(Persona.id)
            .first()
        )
        return jefe.matrimonio_id if jefe is not None else None
    return None


def tiene_quien_vote(db: Session, unidad: UnidadElectoral) -> bool:
    """Un bloque tiene quien lo vote si su votante asignado tiene un integrante
    activo o, sin votante asignado, si el circulo tiene un jefe activo."""
    if unidad.votante_matrimonio_id is not None:
        return _tiene_integrante_activo(db, unidad.votante_matrimonio_id)
    return (
        db.query(Persona)
        .filter(
            Persona.grupo_id == unidad.referencia_id,
            Persona.es_jefe_grupo.is_(True),
            Persona.estado == EstadoPersona.ACTIVA,
        )
        .count()
        > 0
    )


def estado_bloque_sin_incidencias(db: Session, unidad: UnidadElectoral) -> str:
    """Estado de un bloque sin incidencias criticas pendientes, con la misma
    precedencia que el importador: un bloque de postulantes vota solo si tiene
    educador o jefe que lo vote (DEC-042), y sin ningun integrante activo no
    vota (DEC-027)."""
    grupo = db.get(Grupo, unidad.referencia_id)
    personas = (
        db.query(Persona)
        .join(Matrimonio, Matrimonio.id == Persona.matrimonio_id)
        .filter(Matrimonio.grupo_id == unidad.referencia_id, Matrimonio.es_consagrado.is_(False))
        .all()
    )
    if grupo is not None and _es_circulo_postulantes(grupo.nombre) and not tiene_quien_vote(db, unidad):
        return EstadoUnidadElectoral.PENDIENTE_DEFINICION_POSTULANTES.value
    if personas and all(p.estado != EstadoPersona.ACTIVA for p in personas):
        return EstadoUnidadElectoral.PENDIENTE_DEFINICION_BAJA.value
    return EstadoUnidadElectoral.HABILITADA.value


def aplicar_votantes_de_bloque(db: Session) -> None:
    """Asigna el votante de cada bloque segun las reglas de arriba y recalcula
    su estado. Corre al final de cada importacion y en la migracion de DEC-042.
    No hace commit."""
    # Import local: administracion importa el importador, que llama a esta funcion.
    from app.services.habilitacion import incidencias_criticas_pendientes

    ahora = dt.datetime.now(dt.UTC).replace(tzinfo=None)
    bloques = (
        db.query(UnidadElectoral)
        .filter(UnidadElectoral.tipo == TipoUnidadElectoral.BLOQUE_NO_CONSAGRADO)
        .all()
    )
    for unidad in bloques:
        grupo = db.get(Grupo, unidad.referencia_id)
        if grupo is None:
            continue
        unidad.votante_matrimonio_id = _votante_asignado(db, grupo)
        if unidad.votante_matrimonio_id is not None:
            for incidencia in (
                db.query(IncidenciaPadron)
                .filter(
                    IncidenciaPadron.grupo_id == grupo.id,
                    IncidenciaPadron.persona_id.is_(None),
                    IncidenciaPadron.tipo.in_(_INCIDENCIAS_DE_JEFATURA),
                    IncidenciaPadron.resuelto_at.is_(None),
                )
                .all()
            ):
                incidencia.resuelto_por = USUARIO_REGLA
                incidencia.resuelto_at = ahora
        db.flush()

        if incidencias_criticas_pendientes(db, unidad):
            unidad.estado = EstadoUnidadElectoral.BLOQUEADA_POR_INCIDENCIA.value
        else:
            unidad.estado = estado_bloque_sin_incidencias(db, unidad)
    db.flush()
