"""Enums de dominio, mapeados como Enum generico de SQLAlchemy (no nativo de Postgres).

`native_enum=False` hace que SQLAlchemy cree una columna VARCHAR con un CHECK
constraint tanto en SQLite como en PostgreSQL, en lugar de un tipo `CREATE TYPE`
nativo de Postgres. Esto evita el costo de migraciones ALTER TYPE al agregar
valores y mantiene el esquema identico entre los dos motores.
"""

from enum import Enum


class EstadoPersona(str, Enum):
    ACTIVA = "ACTIVA"
    BAJA_NO_ML = "BAJA_NO_ML"
    BAJA_OBSERVACION = "BAJA_OBSERVACION"


class TipoUnidadElectoral(str, Enum):
    MATRIMONIO_CONSAGRADO = "MATRIMONIO_CONSAGRADO"
    BLOQUE_NO_CONSAGRADO = "BLOQUE_NO_CONSAGRADO"


class EstadoVotacion(str, Enum):
    BORRADOR = "BORRADOR"
    ABIERTA = "ABIERTA"
    CERRADA = "CERRADA"
    RESULTADOS_REVELADOS = "RESULTADOS_REVELADOS"


class SeveridadIncidencia(str, Enum):
    CRITICA = "CRITICA"
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"


class EstadoImportacion(str, Enum):
    EN_PROCESO = "EN_PROCESO"
    COMPLETADA = "COMPLETADA"
    FALLIDA = "FALLIDA"


class EstadoUnidadElectoral(str, Enum):
    """Estado de habilitacion de una `UnidadElectoral` generada por el importador.

    `unidades_electorales.estado` es `String(50)` libre (Mision 03), pero el
    importador (Mision 04) solo escribe estos cuatro valores. `PENDIENTE_*`
    cubre las decisiones de negocio todavia sin resolver (DEC-013, DEC-012):
    la unidad se crea igual, pero no puede recibir voto automatico hasta que
    el negocio decida y alguien la pase a HABILITADA con un UPDATE.
    """

    HABILITADA = "HABILITADA"
    BLOQUEADA_POR_INCIDENCIA = "BLOQUEADA_POR_INCIDENCIA"
    PENDIENTE_DEFINICION_POSTULANTES = "PENDIENTE_DEFINICION_POSTULANTES"
    PENDIENTE_DEFINICION_BAJA = "PENDIENTE_DEFINICION_BAJA"


class TipoIncidenciaPadron(str, Enum):
    """Taxonomia tomada de `backend/scripts/explorar_padron.py` (Mision 02),
    mas `MATRIMONIO_SIN_CELULAR_DISPONIBLE` agregado en la Mision 04 (DEC-017)
    para la aclaracion textual del dueño del padron sobre DEC-005: si ningun
    integrante del matrimonio tiene un celular valido, nadie puede consultar
    la habilitacion de esa unidad electoral.
    """

    CELULAR_PLACEHOLDER = "CELULAR_PLACEHOLDER"
    CELULAR_FORMATO_INVALIDO = "CELULAR_FORMATO_INVALIDO"
    CELULAR_FALTANTE = "CELULAR_FALTANTE"
    CELULAR_COMPARTIDO_CONYUGES = "CELULAR_COMPARTIDO_CONYUGES"
    CELULAR_DUPLICADO = "CELULAR_DUPLICADO"
    CELULAR_DUPLICADO_EN_LISTADO_JEFES = "CELULAR_DUPLICADO_EN_LISTADO_JEFES"
    CELULAR_DISCREPANTE_ENTRE_HOJAS = "CELULAR_DISCREPANTE_ENTRE_HOJAS"
    CI_FALTANTE = "CI_FALTANTE"
    CI_COPIADA_ENTRE_CONYUGES = "CI_COPIADA_ENTRE_CONYUGES"
    CI_DUPLICADA = "CI_DUPLICADA"
    MATRIMONIO_SIN_ETIQUETA = "MATRIMONIO_SIN_ETIQUETA"
    MATRIMONIO_INCOMPLETO = "MATRIMONIO_INCOMPLETO"
    CONSAGRACION_INCONSISTENTE = "CONSAGRACION_INCONSISTENTE"
    CONSAGRACION_SIN_DEFINIR = "CONSAGRACION_SIN_DEFINIR"
    NOMBRE_COPIADO_ENTRE_CONYUGES = "NOMBRE_COPIADO_ENTRE_CONYUGES"
    NOMBRE_NO_ALFABETICO = "NOMBRE_NO_ALFABETICO"
    NOMBRE_DISCREPANTE_ENTRE_HOJAS = "NOMBRE_DISCREPANTE_ENTRE_HOJAS"
    CIRCULO_FALTANTE = "CIRCULO_FALTANTE"
    CIRCULO_ETIQUETA_VARIANTE = "CIRCULO_ETIQUETA_VARIANTE"
    CIRCULO_SIN_JEFE = "CIRCULO_SIN_JEFE"
    JEFE_SIN_PERSONA_EN_PADRON = "JEFE_SIN_PERSONA_EN_PADRON"
    JEFE_SOLO_EN_LISTADO_JEFES = "JEFE_SOLO_EN_LISTADO_JEFES"
    JEFE_SOLO_EN_HOJA_PRINCIPAL = "JEFE_SOLO_EN_HOJA_PRINCIPAL"
    MATRIMONIO_SIN_CELULAR_DISPONIBLE = "MATRIMONIO_SIN_CELULAR_DISPONIBLE"
