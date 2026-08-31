"""Seed minimo de desarrollo para probar el modelo de la Mision 03.

No carga datos reales del padron (eso es la Mision 04): crea un puñado de
filas que ejercitan los casos que motivaron los ajustes al modelo -- un
matrimonio consagrado de dos integrantes, un viudo consagrado (DEC-011), un
matrimonio sin marca de consagracion (es_consagrado=None) y un bloque no
consagrado con jefe -- mas una votacion en borrador con sus opciones.

Requiere que las migraciones ya hayan corrido (`alembic upgrade head`).

Uso:

    cd backend
    python scripts/seed_dev.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models import Grupo, Matrimonio, OpcionVoto, Persona, UnidadElectoral, Votacion  # noqa: E402
from app.models.enums import EstadoVotacion, TipoUnidadElectoral  # noqa: E402


def seed() -> None:
    session = SessionLocal()
    try:
        circulo = Grupo(
            nombre='CIRCULO 34 "VIA LUCIS"',
            nombre_normalizado="CIRCULO 34 VIA LUCIS",
            tipo="MIXTO",
        )
        session.add(circulo)
        session.flush()

        marido = Persona(nombres="Roberto Gerardo", apellidos="Bauer", celular="0971659963")
        esposa = Persona(nombres="Alicia", apellidos="De Simone", celular="0971659963")
        session.add_all([marido, esposa])
        session.flush()

        matrimonio_consagrado = Matrimonio(
            codigo_externo="BAUER DE SIMONE",
            integrante_1_id=marido.id,
            integrante_2_id=esposa.id,
            es_consagrado=True,
            grupo_id=circulo.id,
        )
        session.add(matrimonio_consagrado)

        viudo = Persona(nombres="Viudo", apellidos="Consagrado")
        session.add(viudo)
        session.flush()

        matrimonio_viudo = Matrimonio(
            codigo_externo="VIUDO CONSAGRADO",
            integrante_1_id=viudo.id,
            integrante_2_id=None,
            es_consagrado=True,
            grupo_id=circulo.id,
        )
        session.add(matrimonio_viudo)

        sin_definir_1 = Persona(nombres="Sin Definir 1", apellidos="Apellido")
        sin_definir_2 = Persona(nombres="Sin Definir 2", apellidos="Apellido")
        session.add_all([sin_definir_1, sin_definir_2])
        session.flush()

        matrimonio_sin_definir = Matrimonio(
            codigo_externo="SIN CONSAGRACION DEFINIDA",
            integrante_1_id=sin_definir_1.id,
            integrante_2_id=sin_definir_2.id,
            es_consagrado=None,
            grupo_id=circulo.id,
        )
        session.add(matrimonio_sin_definir)

        jefe = Persona(
            nombres="Jefe De Bloque",
            apellidos="No Consagrado",
            celular="0981000000",
            es_jefe_grupo=True,
            grupo_id=circulo.id,
        )
        session.add(jefe)
        session.flush()

        session.flush()

        unidad_matrimonio = UnidadElectoral(
            tipo=TipoUnidadElectoral.MATRIMONIO_CONSAGRADO,
            referencia_id=matrimonio_consagrado.id,
            grupo_id=circulo.id,
            descripcion="Matrimonio consagrado Bauer / De Simone",
        )
        unidad_bloque = UnidadElectoral(
            tipo=TipoUnidadElectoral.BLOQUE_NO_CONSAGRADO,
            referencia_id=circulo.id,
            grupo_id=circulo.id,
            descripcion='Bloque no consagrado de CIRCULO 34 "VIA LUCIS"',
        )
        session.add_all([unidad_matrimonio, unidad_bloque])

        votacion = Votacion(nombre="Votacion De Prueba (dev)", estado=EstadoVotacion.BORRADOR)
        session.add(votacion)
        session.flush()

        session.add_all(
            [
                OpcionVoto(votacion_id=votacion.id, nombre="Opcion A", orden=1),
                OpcionVoto(votacion_id=votacion.id, nombre="Opcion B", orden=2),
            ]
        )

        session.commit()
        print("Seed de desarrollo insertado correctamente.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
