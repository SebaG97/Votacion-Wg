# Misiones Del Proyecto

Este documento organiza el proyecto en misiones ejecutables. Cada mision debe terminar con entregables verificables, documentacion actualizada y pruebas cuando aplique.

## Mision 00 - Preparacion Del Terreno

Estado: completada

Objetivo: crear la estructura base del proyecto y dejar documentacion inicial para trabajar con Codex en VS Code.

Entregables:

- Carpeta principal del proyecto.
- Separacion `backend/` y `frontend/`.
- Documentacion inicial en `docs/`.
- Instrucciones de trabajo en `AGENTS.md`.
- Variables de entorno de ejemplo.

Criterios de aceptacion:

- El proyecto tiene una estructura clara.
- Codex puede leer las reglas iniciales antes de implementar.
- Existen documentos para arquitectura, reglas de negocio, modelo de datos y backlog.

## Mision 01 - Inventario Tecnico Y Scaffolding Base

Estado: completada

Objetivo: crear el esqueleto real del backend y frontend con la misma tecnologia definida para el proyecto.

Entregables backend:

- Proyecto FastAPI inicial.
- Configuracion de settings por entorno.
- Endpoint de salud `GET /api/v1/health`.
- Estructura `app/api`, `app/core`, `app/db`, `app/models`, `app/schemas`, `app/services`, `tests`.
- Configuracion inicial de pytest.

Entregables frontend:

- Proyecto React + TypeScript + Vite inicial.
- Configuracion de cliente API apuntando a `VITE_API_BASE_URL`.
- Pantalla base con estado de conexion.
- Estructura inicial de rutas y componentes.

Criterios de aceptacion:

- Backend levanta localmente.
- Frontend levanta localmente.
- Frontend puede consultar el endpoint de salud.
- Quedan comandos documentados en los README de cada aplicacion.

## Mision 02 - Analisis Del Excel Del Padron

Estado: completada (2026-08-31)

Objetivo: recibir el Excel del padron y generar un informe tecnico de estructura y calidad de datos antes de importarlo.

Entregables reales:

- `backend/scripts/explorar_padron.py`: script exploratorio que lee las tres hojas con `openpyxl` en modo `read_only`, acotando las columnas reales (19 y 9) para evitar las ~16.000 columnas fantasma, audita las celdas combinadas leyendo el XML crudo del `.xlsx`, clasifica las filas, agrupa matrimonios y emite las incidencias. No modifica el Excel.
- `docs/PADRON_ANALISIS.md`: informe completo con estructura real de las tres hojas, perfil por columna, mapeo hoja -> entidad del modelo, informe de duplicados de celular, informe de registros incompletos y recomendacion de reconciliacion de las dos hojas de personas.
- `docs/padron_incidencias.csv`: 682 incidencias con tipo, severidad, hoja, fila de Excel, circulo, persona y detalle.
- `docs/padron_estructura.json`: estructura, perfil por columna, auditoria de celdas combinadas y metricas agregadas, en formato consumible por la Mision 04.
- `openpyxl` agregado a `backend/requirements-dev.txt` y a `pyproject.toml` (`optional-dependencies.dev`). No se agrego `pandas`: la lectura acotada con `openpyxl` cubre el caso y evita el problema de las columnas fantasma sin dependencia adicional.
- Decisiones DEC-005 a DEC-010 en `docs/DECISIONES.md`.

Hallazgos principales:

- La hoja `Copia de Jefes ML 2026. betty(1` es la fuente de verdad: 1113 personas reales sobre 1190 filas (el resto son 73 filas separadoras de circulo, 2 de resumen, 1 vacia y 1 rotulo).
- 571 matrimonios: 260 consagrados, 292 no consagrados, 19 sin definir. 93 circulos, 74 matrimonios jefe.
- Votos maximos estimados: 260 `MATRIMONIO_CONSAGRADO` + 54 `BLOQUE_NO_CONSAGRADO` = 314, sujeto a resolver las incidencias criticas.
- La columna `Consagrados` no esta corrupta: los valores anomalos son el pie de totales del Excel.
- Las celdas combinadas casi no requieren propagacion en la hoja principal (38 de 954, ninguna en persona, celular, matrimonio, consagracion ni jefatura); en `LISTADO JEFES` si (67 de 71).
- No hay duplicados reales de celular entre personas distintas en la hoja principal: los 4 casos son conyuges compartiendo telefono. Los duplicados criticos estan en `LISTADO JEFES` (2 pares) y entre hojas (3 discrepancias).
- 64 incidencias criticas, entre ellas 19 matrimonios sin marca de consagracion, 11 circulos con bloque no consagrado y sin jefe, y 5 jefes que no existen como persona en el padron.

Criterios de aceptacion:

- Cumplido: sabemos que columnas del Excel alimentan cada entidad (`PADRON_ANALISIS.md`, seccion 3).
- Cumplido: tenemos el listado de incidencias antes de tocar la base definitiva (`padron_incidencias.csv`).
- Cumplido: la unicidad del celular fue validada y refutada; los duplicados quedaron clasificados por tipo y severidad (DEC-008).

Pendiente para el negocio, no bloquea la Mision 03: viudos consagrados, personas dadas de baja, circulos de postulantes, los 19 matrimonios sin clasificar y el doble rol de los 43 jefes consagrados. Detalle en `PADRON_ANALISIS.md`, seccion 7.

## Mision 03 - Modelo De Datos Y Migraciones

Estado: completada (2026-08-31)

Objetivo: implementar el modelo persistente inicial y migraciones de base de datos, ya ajustado a lo que el Excel real contiene (`PADRON_ANALISIS.md`, seccion 6.4) y no al modelo preliminar sin validar.

Entregables reales:

- `backend/app/models/`: modelos SQLAlchemy 2.0 (`DeclarativeBase`) para `Persona`, `Matrimonio`, `Grupo`, `UnidadElectoral`, `Votacion`, `OpcionVoto`, `Voto` e `IncidenciaPadron`, mas `enums.py` (enums de dominio) y `mixins.py` (`TimestampMixin` para `created_at`/`updated_at`).
- `backend/app/db/`: `base_class.py` (`Base`), `session.py` (`engine`/`SessionLocal`/`get_db`, construidos desde `settings.database_url`; activa `PRAGMA foreign_keys=ON` por conexion cuando el motor es SQLite, porque SQLite no lo hace por defecto).
- `backend/alembic/`: setup de Alembic con `env.py` leyendo `settings.database_url` (permite override programatico para pruebas) y `render_as_batch` activado en SQLite. Primera revision `19b5c6d93c4b_esquema_inicial.py` con las 8 tablas, sus indices y sus restricciones, mas `downgrade()` completo.
- `backend/scripts/seed_dev.py`: seed minimo de desarrollo (no carga datos reales del padron, eso es la Mision 04) que ejercita un matrimonio consagrado de dos integrantes, un viudo consagrado, un matrimonio sin marca de consagracion y un bloque no consagrado con jefe.
- `backend/tests/test_migrations.py` + `conftest.py`: 10 pruebas que corren `alembic upgrade head` / `downgrade base` sobre un SQLite descartable por test (no `create_all`) y verifican en base, no en codigo: unicidad de voto por `(votacion_id, unidad_electoral_id)`, nullability de `celular`/`documento`/`integrante_2_id`/`es_consagrado`, el CHECK constraint que genera el enum de `personas.estado`, la unicidad de `grupos.nombre_normalizado`, el CHECK de integrantes distintos en `matrimonios`, y que las foreign keys se aplican de verdad en SQLite.
- `sqlalchemy`, `alembic` y `psycopg[binary]` agregados a `backend/requirements.txt` y `pyproject.toml` (no solo a `-dev`, porque el motor de base de datos es parte del runtime, no solo de las pruebas).

Ajustes aplicados respecto al modelo preliminar (`PADRON_ANALISIS.md` 6.4):

- `personas.celular` y `personas.documento`: nullable, sin `UNIQUE` en base. La duplicidad real se controla como incidencia de importacion (DEC-002, DEC-008), no como restriccion de base.
- `matrimonios.integrante_2_id`: nullable, con `CHECK (integrante_2_id IS NULL OR integrante_1_id <> integrante_2_id)` para que nunca sea la misma persona dos veces. Soporta los 29 matrimonios de un solo integrante, incluidos los 22 viudos consagrados (DEC-011).
- `matrimonios.es_consagrado`: `Boolean` nullable (tri-estado real: `True` / `False` / `NULL` = sin definir), sin `default`. Cubre los 19 matrimonios sin marca en el Excel.
- `grupos.nombre_normalizado`: agregado ademas del `nombre` literal, con `UNIQUE` en base, para las 9 variantes de escritura del mismo circulo.
- Relacion grupo -> jefe modelada como 1:N: no existe `jefe_persona_id` en `grupos`; la jefatura vive en `personas.es_jefe_grupo` + `personas.grupo_id`, porque 3 circulos tienen dos matrimonios jefe.
- `personas.estado`: enum `ACTIVA` / `BAJA_NO_ML` / `BAJA_OBSERVACION` (distingue la marca estructurada `No ML` de la observacion textual libre) mas `personas.observacion_baja` para el detalle. No se implementa ninguna exclusion automatica del padron votante (DEC-012, pendiente de negocio).
- `unidades_electorales`: mismo diseño del modelo preliminar (`tipo` + `referencia_id` + `grupo_id` + `descripcion` + `cantidad_personas_control` + `estado`), con `UNIQUE (tipo, referencia_id)` agregado para que no se dupliquen unidades para el mismo matrimonio o circulo.
- `incidencias_padron.tipo`: enum con los ~20 tipos reales que ya emite `backend/scripts/explorar_padron.py` (documentados en `padron_estructura.json`/`padron_incidencias.csv`), no una taxonomia nueva. `severidad` es enum `CRITICA`/`ALTA`/`MEDIA`/`BAJA`.
- Todos los enums (`EstadoPersona`, `TipoUnidadElectoral`, `EstadoVotacion`, `SeveridadIncidencia`, `TipoIncidenciaPadron`) usan `sa.Enum(..., native_enum=False, create_constraint=True)`: en SQLite y en PostgreSQL por igual se traduce a una columna `VARCHAR` con un `CHECK` de valores permitidos, nunca a un tipo nativo `CREATE TYPE` de Postgres. Se verifico manualmente que `create_constraint=True` es necesario en SQLAlchemy 2.0: sin el, el `CHECK` no se genera.
- `personas.matrimonio_id` y `matrimonios.integrante_1_id`/`integrante_2_id` forman una referencia circular entre dos tablas. La migracion crea `personas` sin esa FK, luego `matrimonios`, y agrega la FK a `personas` con `batch_alter_table` (en SQLite esto recrea la tabla preservando el resto de columnas y constraints; en PostgreSQL es un `ALTER TABLE` directo). Se verifico que la recreacion no pierde el CHECK del enum de `estado`.

Nota de versionado (Paso 0 de esta mision): el repositorio ya tenia `git init`, un commit inicial (`627e9d8`) y un remoto configurado antes de empezar esta mision -no hizo falta inicializarlo-. Se reviso `.gitignore` y se agrego la exclusion de `*.db`/`*.db-journal` (bases SQLite locales), que faltaba.

Criterios de aceptacion:

- Cumplido: la base se crea desde cero solo con `alembic upgrade head` (sin `create_all`), verificado en pruebas y a mano contra SQLite.
- Cumplido: las restricciones criticas estan en base de datos: unicidad de voto, nullability de celular/documento/integrante_2_id, tri-estado de `es_consagrado`, CHECK de los enums, unicidad de `nombre_normalizado`, y foreign keys reforzadas via `PRAGMA foreign_keys=ON` en SQLite.
- Cumplido: los modelos soportan matrimonios consagrados (con y sin segundo integrante), bloques no consagrados y circulos mixtos (`grupos.tipo` libre, sin forzar una clasificacion que la Mision 04 todavia no calcula).

Pendiente para el negocio, no bloquea la Mision 04: bajas de personas (DEC-012), circulos de postulantes (DEC-013) y doble rol de jefes consagrados (DEC-014). El modelo ya soporta cualquiera de los desenlaces posibles de las tres sin migracion adicional.

## Mision 04 - Importador Y Normalizador Del Padron

Estado: completada (2026-08-31)

Objetivo: convertir el Excel validado en personas, matrimonios, grupos, jefes y unidades electorales.

Entregables reales:

- `backend/app/services/padron/`: la logica de la Mision 02 (normalizacion de celular/CI, clasificacion estructural de filas, agrupamiento de matrimonios, deteccion de incidencias y reconciliacion de las dos hojas) se extrajo de `backend/scripts/explorar_padron.py` a este paquete (`normalizacion.py`, `columnas.py`, `dominio.py`, `lectura.py`, `clasificacion.py`, `matrimonios.py`, `incidencias.py`, `analisis.py`), sin cambiar ninguna regla de negocio. `explorar_padron.py` ahora importa esas funciones en vez de duplicarlas; se verifico que su salida (`padron_estructura.json`, `padron_incidencias.csv`) sigue siendo byte por byte identica a la de la Mision 02.
- `backend/app/services/padron/importador.py`: el importador real. Reemplaza por completo -dentro de una transaccion- lo generado por una corrida anterior (personas, matrimonios, grupos, unidades electorales e incidencias), aplica la cascada de reconciliacion de DEC-009 para completar el celular de jefes que faltan en la hoja principal, genera las unidades electorales y les asigna un estado segun DEC-016, y rechaza la corrida si existe una `Votacion` mas alla de `BORRADOR` (DEC-015).
- `backend/app/services/padron/importar.py`: comando de CLI (`python -m app.services.padron.importar [--excel RUTA] [--usuario NOMBRE]`), para probar el importador sin levantar el servidor.
- `POST /api/v1/padron/importaciones` (`backend/app/api/v1/endpoints/padron.py`, `backend/app/schemas/padron.py`): dispara la misma logica; devuelve 201 con el registro de importacion y su resumen, 404 si no encuentra el Excel, 409 si hay una votacion que bloquea la reimportacion.
- `backend/app/models/importacion_padron.py`: modelo `ImportacionPadron` (`importaciones_padron`: `fecha`, `archivo_origen`, `usuario` nullable, `estado` `EN_PROCESO`/`COMPLETADA`/`FALLIDA`, `resumen` JSON, `error`). `incidencias_padron` gano la FK `importacion_id`. Migracion `77ba051c28a4_registro_de_importacion_del_padron.py`.
- `backend/app/models/enums.py`: `TipoIncidenciaPadron.MATRIMONIO_SIN_CELULAR_DISPONIBLE` (DEC-017), con su CHECK constraint ampliado en la migracion `b02555d5ef5b_matrimonio_sin_celular_disponible.py`.
- `backend/tests/test_importador_padron.py`: 15 pruebas rapidas contra un `.xlsx` sintetico de 14 filas (`_construir_excel_fixture`) que reproduce a proposito un matrimonio de un solo integrante sin viudez, dos etiquetas `MATRIMONIO` repetidas en circulos distintos, un celular compartido entre conyuges, una fila de resumen al pie, una celda combinada, un jefe que solo existe en `LISTADO JEFES` (con y sin correspondencia), un matrimonio consagrado sin ningun celular valido en ninguno de sus dos integrantes (DEC-017, bloquea la unidad) y un matrimonio donde solo uno de los dos tiene celular propio (no bloquea, aunque el otro dependa de la reconciliacion de `LISTADO JEFES` para completar el suyo). Mas 2 pruebas de regresion (`_construir_excel_fixture_alcance_incidencias`, DEC-019, agregadas en el fix posterior a esta mision) y 1 prueba `@pytest.mark.slow` que corre contra el Excel real y verifica los totales exactos de `PADRON_ANALISIS.md`. `backend/tests/test_padron_endpoint.py`: 3 pruebas del endpoint HTTP (201, 404, 409) con `TestClient` y un SQLite migrado por prueba.
- `openpyxl` se movio de `requirements-dev.txt` a `requirements.txt`/`dependencies` (ya no es solo una herramienta de analisis: el importador la usa en runtime).

Resultado de correr el importador contra el Excel real (`python -m app.services.padron.importar`), verificado contra `PADRON_ANALISIS.md`:

- 1113 personas, 571 matrimonios (260 consagrados, 292 no consagrados, 19 sin definir), 93 grupos -- coinciden exactamente con el analisis de la Mision 02.
- 690 incidencias (72 CRITICA, 43 ALTA, 168 MEDIA, 407 BAJA). Los 682/64 originales de la Mision 02 coinciden salvo por las 8 incidencias `MATRIMONIO_SIN_CELULAR_DISPONIBLE` (CRITICA) agregadas por DEC-017: 7 matrimonios (8 personas -- seis de un solo integrante, uno de dos) donde ningun integrante tiene un celular que normalice a un numero valido.
- Reconciliacion de `LISTADO JEFES`: 110 por nombre+celular, 29 por celular, 4 por nombre (celular discrepante, no completado automaticamente), 3 sin correspondencia -- coincide con DEC-009. Se verifico ademas, contra el Excel real, que ninguno de los 7 circulos con bloque no consagrado y jefe resuelto queda sin un celular valido tras esta reconciliacion (0 casos sobre 54 circulos), asi que `BLOQUE_SIN_CELULAR_JEFE_DISPONIBLE` no se agrego a la taxonomia -- no hay ningun caso real que lo justifique (DEC-017).
- 314 unidades electorales (260 `MATRIMONIO_CONSAGRADO` + 54 `BLOQUE_NO_CONSAGRADO`): **265** `HABILITADA`, **16** `BLOQUEADA_POR_INCIDENCIA`, **25** `PENDIENTE_DEFINICION_POSTULANTES`, **8** `PENDIENTE_DEFINICION_BAJA`. Votos maximos habilitables hoy: **249** `MATRIMONIO_CONSAGRADO` + **16** `BLOQUE_NO_CONSAGRADO` = **265**. (Numeros corregidos por el fix de DEC-019, ver mas abajo; los numeros originales de esta mision -- 216 `HABILITADA`, 70 `BLOQUEADA_POR_INCIDENCIA`, 22 `PENDIENTE_DEFINICION_POSTULANTES`, 6 `PENDIENTE_DEFINICION_BAJA` -- estaban inflados porque el calculo de bloqueo tomaba por error cualquier incidencia CRITICA del circulo, sin importar a que matrimonio o bloque correspondia.)

Decisiones nuevas: DEC-015 (rechazo de reimportacion con votacion abierta/cerrada; reemplazo transaccional mientras este en borrador), DEC-016 (prioridad de estados de unidad electoral: incidencia critica > postulantes pendiente > baja pendiente > habilitada) y DEC-017 (matrimonio sin ningun celular valido, a partir de la aclaracion textual del dueño del padron sobre DEC-005).

**Fix posterior (mismo dia, antes de la Mision 06): DEC-019** -- el calculo de `BLOQUEADA_POR_INCIDENCIA` tenia un alcance incorrecto: un `MATRIMONIO_CONSAGRADO` se bloqueaba si *cualquier* incidencia CRITICA del circulo existia (via `matrimonio.grupo_id in grupos_con_critica`), y lo mismo para `BLOQUE_NO_CONSAGRADO` (`grupo.id in grupos_con_critica`), sin verificar si esa incidencia tenia algo que ver con ese matrimonio o con el jefe del bloque. Como casi toda incidencia lleva el circulo de la persona afectada, esto bloqueaba unidades sanas solo por compartir circulo con una que si tenia un problema. Corregido en `backend/app/services/padron/importador.py` (`_crear_unidades_electorales`): `MATRIMONIO_CONSAGRADO` se bloquea unicamente por una incidencia CRITICA sobre sus propios integrantes; `BLOQUE_NO_CONSAGRADO` unicamente por una incidencia CRITICA sobre el circulo en si (`persona_id IS NULL`) o sobre alguno de sus jefes (`_grupos_con_incidencia_de_jefe_o_circulo`, nueva funcion que reemplaza a `_grupos_con_incidencia_critica`). `backend/app/services/habilitacion.py` (`_incidencias_criticas_matrimonio`, `_incidencias_criticas_grupo`) se corrigio en paralelo para que la Mision 05 explique el bloqueo con exactamente las mismas incidencias que ahora lo causan. Resultado sobre el Excel real: `HABILITADA` sube de 216 a 265 (+49), `BLOQUEADA_POR_INCIDENCIA` baja de 70 a 16 (-54); parte de esa diferencia no cae directo en `HABILITADA` sino en `PENDIENTE_DEFINICION_POSTULANTES` (22 -> 25) o `PENDIENTE_DEFINICION_BAJA` (6 -> 8), porque esas unidades, al dejar de estar bloqueadas por una incidencia ajena, quedan expuestas a la siguiente regla de precedencia de DEC-016 que si les aplica. 72 incidencias CRITICA reales no cambiaron: lo que cambio es a cuantas unidades electorales distintas "contagiaba" cada una. Pruebas de regresion en `test_importador_padron.py` (`test_incidencia_critica_de_un_matrimonio_no_bloquea_a_otro_del_mismo_circulo`, `test_incidencia_critica_de_un_matrimonio_no_bloquea_el_bloque_no_consagrado_del_circulo`).

Criterios de aceptacion:

- Cumplido: el importador no deja habilitada ninguna unidad electoral con una incidencia CRITICA propia asociada (`BLOQUEADA_POR_INCIDENCIA`); una incidencia de otra unidad del mismo circulo ya no la bloquea (DEC-019).
- Cumplido: los duplicados de celular entre matrimonios distintos (`CELULAR_DUPLICADO`, `CELULAR_DUPLICADO_EN_LISTADO_JEFES`, `CELULAR_DISCREPANTE_ENTRE_HOJAS`) son CRITICA y bloquean la unidad electoral asociada; el celular compartido entre conyuges (`CELULAR_COMPARTIDO_CONYUGES`, DEC-008) no bloquea.
- Cumplido: un matrimonio donde ningun integrante tiene celular valido (`MATRIMONIO_SIN_CELULAR_DISPONIBLE`, DEC-017) bloquea su unidad electoral; un matrimonio donde al menos uno de los dos si tiene celular valido no se ve afectado, aunque el otro dependa de `LISTADO JEFES` para completar el suyo.
- Cumplido: cada matrimonio consagrado (incluidos los 22 viudos, DEC-011) genera una unidad `MATRIMONIO_CONSAGRADO`.
- Cumplido: cada circulo con al menos un matrimonio no consagrado genera una unidad `BLOQUE_NO_CONSAGRADO` (54, DEC-010), independientemente de si el jefe se resuelve por la hoja principal o por `LISTADO JEFES`.

Pendiente para el negocio, no bloquea la Mision 06: bajas de personas (DEC-012), circulos de postulantes (DEC-013) y doble rol de jefes consagrados (DEC-014). Aplicar cualquiera de las tres es un `UPDATE` sobre `unidades_electorales`/`incidencias_padron`, no una reimportacion (DEC-016).

## Mision 05 - Motor De Habilitacion Por Celular

Estado: completada (2026-08-31)

Objetivo: resolver que puede votar una persona a partir de su celular.

Entregables reales:

- `backend/app/services/habilitacion.py`: `consultar_habilitacion(db, celular)`. Resuelve siempre contra la unica `Votacion` en estado `ABIERTA` (DEC-018); levanta `NoHayVotacionAbiertaError` si no hay ninguna. Normaliza el celular con `app/services/padron/normalizacion.normalizar_celular` (no reimplementa el parseo); un celular que no normaliza a 10 digitos validos, o que no matchea ninguna `Persona`, responde `habilitado=False` sin excepcion. Busca todas las `Persona` con ese celular normalizado (puede haber mas de una, DEC-008) y junta las unidades candidatas de todas ellas en un dict por `unidad_electoral.id` -- esto es lo que dedupea el celular compartido entre conyuges a una sola unidad y separa las dos unidades de un jefe consagrado con doble rol (DEC-014). Cada unidad candidata se evalua de forma independiente: si `estado != HABILITADA`, no disponible con `motivo_no_disponible` igual al estado (y, si es `BLOQUEADA_POR_INCIDENCIA`, las incidencias CRITICA asociadas -- misma condicion de bloqueo que ya usa el importador en DEC-016: incidencia sobre algun integrante del matrimonio o sobre el grupo, para `MATRIMONIO_CONSAGRADO`; incidencia sobre el grupo, para `BLOQUE_NO_CONSAGRADO`); si esta `HABILITADA`, se chequea si ya existe un `Voto` para `(votacion_id, unidad_electoral_id)` de la votacion abierta -- si existe, no disponible con motivo `YA_VOTADO`; si no, disponible.
- `backend/app/schemas/habilitacion.py`: `HabilitacionConsultaRequest` (`celular: str`), `HabilitacionConsultaResponse` (`celular_normalizado`, `habilitado`, `personas` -- solo `persona_id`/`nombres`/`apellidos`, sin celular ni documento --, `unidades`), `UnidadElectoralDisponible` (`tipo`, `descripcion`, `estado`, `disponible`, `motivo_no_disponible`, `incidencias`) e `IncidenciaRespuesta` (`tipo`, `severidad`, `descripcion`).
- `POST /api/v1/habilitaciones/consultar` (`backend/app/api/v1/endpoints/habilitaciones.py`, registrado en `app/api/v1/api.py`): `200` con la respuesta de habilitacion (disponible o no, con motivo), `409` si no hay ninguna `Votacion` `ABIERTA`.
- `backend/tests/test_habilitacion.py`: 7 pruebas contra el servicio con datos armados directo con los modelos SQLAlchemy sobre un SQLite migrado por prueba (`db_session` de `conftest.py`) -- celular inexistente, celular con formato invalido, unidad `BLOQUEADA_POR_INCIDENCIA` (con la incidencia CRITICA en la respuesta), unidad con voto ya registrado, jefe consagrado con doble rol (una unidad disponible y la otra ya votada, evaluadas por separado), celular compartido entre conyuges (una sola unidad, DEC-008) y ausencia de votacion `ABIERTA` (`NoHayVotacionAbiertaError`). `backend/tests/test_habilitacion_endpoint.py`: 2 pruebas del endpoint HTTP (200 con unidad disponible, 409 sin votacion abierta) con `TestClient`, reusando los helpers de armado de datos del primer archivo.

Decision nueva: DEC-018 (la consulta resuelve siempre contra la unica votacion `ABIERTA`, sin `votacion_id` en la ruta; revisar si la Mision 07 llega a permitir mas de una simultanea).

Criterios de aceptacion:

- Cumplido: celular inexistente responde no habilitado (`test_celular_inexistente_no_habilitado`).
- Cumplido: unidad bloqueada por incidencia critica responde la incidencia y no ofrece voto (`test_unidad_bloqueada_por_incidencia_responde_la_incidencia_y_no_ofrece_voto`); esto cubre tanto `CELULAR_DUPLICADO` como cualquier otra incidencia CRITICA que deje la unidad `BLOQUEADA_POR_INCIDENCIA`, ya que la consulta lee el estado ya calculado por el importador (DEC-016), no vuelve a evaluar duplicados de celular por su cuenta.
- Cumplido: matrimonio (o bloque no consagrado) ya votado no vuelve a habilitarse (`test_unidad_con_voto_registrado_no_se_vuelve_a_ofrecer`, y el caso del bloque dentro de `test_jefe_consagrado_con_doble_rol_ve_dos_unidades_evaluadas_por_separado`).
- Cumplido: persona con dos roles ve dos opciones separadas, cada una evaluada de forma independiente (`test_jefe_consagrado_con_doble_rol_ve_dos_unidades_evaluadas_por_separado`).

Fuera de alcance a proposito, es la Mision 06: registrar el voto (`POST /api/v1/votaciones/{id}/votos`). Esta mision solo consulta.

## Mision 06 - Registro De Voto Y Auditoria

Estado: completada (2026-08-31)

Objetivo: registrar votos de forma idempotente y trazable, apoyandose en el motor de habilitacion de la Mision 05 sin reimplementarlo.

Entregables reales:

- `backend/app/services/voto.py`: `registrar_voto(db, *, votacion_id, celular_consultado, unidad_electoral_id, opcion_id, emitido_por_persona_id, canal=None)`. Valida en orden, cada paso con su propia excepcion: la `Votacion` del path existe y esta `ABIERTA` (`VotacionNoDisponibleError`, 409, mismo patron que DEC-015); la `UnidadElectoral` existe (`UnidadElectoralNoEncontradaError`, 404) y su estado es `HABILITADA` (`UnidadElectoralNoDisponibleError`, 409, con el estado real -- `BLOQUEADA_POR_INCIDENCIA`, `PENDIENTE_DEFINICION_POSTULANTES` o `PENDIENTE_DEFINICION_BAJA`); la `OpcionVoto` existe y pertenece a esa votacion (`OpcionInvalidaError`, 400); el `celular_consultado` normalizado (`normalizar_celular`, reusada de la Mision 04) efectivamente resuelve a `unidad_electoral_id` (`CelularNoResuelveUnidadError`, 400); `emitido_por_persona_id` es uno de los integrantes del matrimonio (`MATRIMONIO_CONSAGRADO`) o un jefe de ese circulo especifico (`BLOQUE_NO_CONSAGRADO`) (`PersonaNoAutorizadaError`, 400); y no existe ya un `Voto` para `(votacion_id, unidad_electoral_id)` (`VotoDuplicadoError`, 409, chequeado antes de insertar y de nuevo via `try/except IntegrityError` alrededor del commit, para la carrera de dos requests simultaneas que pasan el chequeo previo a la vez).
- `backend/app/services/habilitacion.py`: `_unidades_candidatas` paso a llamarse `unidades_candidatas` (publica, sin guion bajo) para que la Mision 06 la reuse tal cual en vez de duplicar la resolucion de que unidades corresponden a un celular; sin cambio de conducta.
- `backend/app/schemas/voto.py`: `VotoRequest` (`celular_consultado`, `unidad_electoral_id`, `opcion_id`, `emitido_por_persona_id` -- obligatorio en el schema aunque la columna del modelo sea nullable, para que la trazabilidad real siempre venga completa --, `canal` opcional) y `VotoResponse` (`id`, `votacion_id`, `unidad_electoral_id`, `opcion_id`, `emitido_por_persona_id`, `celular_consultado`, `fecha_emision`, `canal` -- sin ningun conteo ni dato agregado por opcion, `REGLAS_NEGOCIO.md` prohibe exponer resultados antes del cierre).
- `POST /api/v1/votaciones/{votacion_id}/votos` (`backend/app/api/v1/endpoints/votos.py`, registrado en `app/api/v1/api.py`): `201` con el `Voto` creado; `404` si la unidad electoral no existe; `409` si la votacion no existe/no esta abierta, si la unidad no esta `HABILITADA` o si ya hay un voto para esa unidad; `400` si la opcion no es de esa votacion, si el celular no resuelve a la unidad, o si la persona emisora no esta autorizada.
- `backend/tests/test_voto.py`: 15 pruebas contra el servicio, datos armados con los modelos SQLAlchemy (reusa los helpers de `test_habilitacion.py`) -- voto exitoso con todos los campos de auditoria, segundo intento sobre la misma unidad (409, sin segunda fila), carrera de dos inserts simultaneos resuelta por la restriccion unica de base y mapeada a 409 (bypaseando el chequeo previo con `monkeypatch` para forzar el camino del `IntegrityError`), votacion en `BORRADOR`/`CERRADA`/inexistente (409), unidad en cada estado no disponible citando el estado real (409) y unidad inexistente (404), opcion de otra votacion (400), celular que no resuelve a la unidad (400), persona no autorizada -- ajena al matrimonio, o integrante del circulo pero no jefe (400) --, y jefe consagrado con doble rol emitiendo dos votos independientes y exitosos. `backend/tests/test_voto_endpoint.py`: 3 pruebas del endpoint HTTP (201, 409 por doble voto, 409 sin votacion abierta).

Decision nueva: DEC-020 (el doble rol de jefe consagrado, DEC-014, se permite sin restriccion adicional -- dos requests, dos votos independientes -- hasta que el negocio resuelva esa decision pendiente; y el endpoint no tiene ningun control de acceso todavia, queda como pendiente explicito por ser una zona sensible segun `AGENTS.md`).

Criterios de aceptacion:

- Cumplido: una unidad electoral no puede votar dos veces en la misma votacion, tanto por el chequeo previo (`VotoDuplicadoError` antes de insertar) como por la restriccion unica de base como ultima linea de defensa ante una carrera (`test_segundo_intento_sobre_misma_unidad_da_409_y_no_crea_segunda_fila`, `test_carrera_de_dos_inserts_simultaneos_se_resuelve_como_409_no_500`).
- Cumplido: no se puede votar si la votacion esta en `BORRADOR`, `CERRADA` o no existe (`test_votacion_no_abierta_da_409`, `test_votacion_inexistente_da_409`).
- Cumplido: no se puede votar con una unidad electoral bloqueada por incidencia ni con ninguna otra que no este `HABILITADA` (`test_unidad_no_habilitada_da_409_citando_estado_real`).
- Cumplido: cada voto conserva `fecha_emision`, `celular_consultado` y `emitido_por_persona_id` para auditoria (`test_voto_exitoso_se_persiste_con_datos_de_auditoria`).

Pendiente para el negocio, no bloquea la Mision 07: doble rol de jefes consagrados (DEC-014, ver DEC-020) y control de acceso sobre este endpoint (tambien DEC-020, distinto del panel administrativo que cubrira la Mision 07).

## Mision 07 - Administracion De Votacion

Estado: completada (2026-08-31)

Objetivo: permitir crear una votacion con sus opciones, abrirla, cerrarla y consultar su estado operativo, cerrando dos gaps que quedaban abiertos: no existia ningun endpoint para crear una `Votacion`/`OpcionVoto` (todo se armaba por ORM en tests), y el modelo no registraba quien abrio o cerro la votacion.

Entregables reales:

- `backend/app/models/votacion.py`: columnas nuevas `abierta_por`/`cerrada_por` (`String(255)` nullable, texto libre -- no hay sistema de identidad todavia, DEC-021) mas `uq_votacion_estado_abierta`, un indice unico parcial sobre `estado` (valido solo mientras `estado = 'ABIERTA'`, via `sqlite_where`/`postgresql_where`) que refuerza en base la invariante de DEC-018 ("una sola votacion ABIERTA a la vez"), mismo patron de defensa en profundidad que el UNIQUE de `votos` (Mision 06).
- `backend/alembic/versions/6d2b5dd756ef_administracion_de_votacion.py`: migracion que agrega esas dos columnas y ese indice sobre la migracion previa (`b02555d5ef5b`).
- `backend/app/core/config.py` + `backend/.env.example`: `ADMIN_API_KEY` (default vacio). `backend/app/api/deps.py`: `require_admin`, dependencia de FastAPI que compara el header `X-Admin-Token` contra ese valor; si `ADMIN_API_KEY` esta vacio rechaza con `403` (falla cerrado), con token ausente o incorrecto responde `401` (DEC-021).
- `backend/app/services/votacion.py`: `crear_votacion`, `agregar_opcion` (exige `estado == BORRADOR`, `VotacionNoEsBorradorError` si no), `listar_opciones`, `abrir_votacion` (exige `BORRADOR`, al menos una `OpcionVoto` y ninguna otra `Votacion` `ABIERTA` -- cada validacion con su propia excepcion; comit envuelto en `try/except IntegrityError` por el indice unico parcial, igual patron que `registrar_voto` de la Mision 06), `cerrar_votacion` (exige `ABIERTA`) y `obtener_estado_operativo` (conteo de `unidades_electorales` por los cuatro estados de `EstadoUnidadElectoral`, votos emitidos de esa votacion, pendientes = habilitadas - emitidos; nunca nada agrupado por `opcion_id`).
- `backend/app/schemas/votacion.py` + `backend/app/api/v1/endpoints/votaciones.py` (registrado en `app/api/v1/api.py`), router completo protegido por `require_admin` a nivel de router: `POST /api/v1/votaciones` (201, BORRADOR), `POST` y `GET /api/v1/votaciones/{id}/opciones` (opciones se cargan en un endpoint separado del de creacion; 409 si la votacion ya salio de BORRADOR), `POST /api/v1/votaciones/{id}/abrir` (requiere `usuario` en el body; 404/409 segun corresponda), `POST /api/v1/votaciones/{id}/cerrar` (requiere `usuario`; 404/409), `GET /api/v1/votaciones/{id}/estado` (estado operativo, sin nada por opcion). `POST /api/v1/habilitaciones/consultar` y `POST /api/v1/votaciones/{id}/votos` quedan sin este control a proposito (DEC-020, DEC-021).
- `backend/tests/test_votacion.py` (22 pruebas contra el servicio) y `backend/tests/test_votacion_endpoint.py` (7 pruebas HTTP): creacion en BORRADOR, opcion rechazada fuera de BORRADOR, abrir sin opciones (409), abrir con opciones y sin otra abierta (200, `abierta_por`/`fecha_apertura` seteados), abrir con otra ya ABIERTA (409, chequeo de servicio) mas la carrera de dos aperturas simultaneas resuelta por el indice unico de base (`monkeypatch` bypasea el chequeo previo, inserta una segunda `ABIERTA` por fuera, confirma 409 no 500), cerrar una ABIERTA (200, `cerrada_por`/`fecha_cierre`), cerrar BORRADOR/CERRADA (409), estado operativo con conteos correctos y una prueba explicita de que la respuesta no expone ninguna clave relacionada a `opcion`, control de acceso (403 sin `ADMIN_API_KEY` configurado, 401 sin token o con token incorrecto, 201 con el correcto), y una prueba dedicada que confirma que `/habilitaciones/consultar` y `/votaciones/{id}/votos` siguen respondiendo sin token (no quedaron protegidos por accidente al conectar el router nuevo). Se ajusto ademas `test_voto.py::test_opcion_de_otra_votacion_da_400` (Mision 06), que armaba dos `Votacion` `ABIERTA` a la vez para un caso que no lo necesitaba: paso a violar el indice unico parcial nuevo.

Decision nueva: DEC-021 (mecanismo administrativo inicial via `ADMIN_API_KEY`, explicitamente no un sistema de usuarios; alcance exacto de que protege y que no).

Criterios de aceptacion:

- Cumplido: solo una votacion `ABIERTA` a la vez, reforzado tanto en servicio (`_confirmar_sin_otra_abierta`) como en base (`uq_votacion_estado_abierta`).
- Cumplido: el cierre registra fecha (`fecha_cierre`), hora (mismo campo, `DateTime`) y usuario (`cerrada_por`).
- Cumplido: antes del cierre -- de hecho, en cualquier momento -- `GET /votaciones/{id}/estado` no devuelve nada agrupado por `opcion_id`.

Fuera de alcance a proposito, es la Mision 08 completa: revelacion de resultados y cualquier conteo por opcion.

## Mision 08 - Resultados

Estado: completada (2026-08-31)

Objetivo: revelar resultados solo despues del cierre y con trazabilidad, cerrando el ultimo tramo del ciclo de vida de `Votacion` (el cuarto estado, `RESULTADOS_REVELADOS`, y `resultados_revelados_at`, presentes desde la Mision 03 pero sin usar).

Ambiguedad resuelta (DEC-022): `REGLAS_NEGOCIO.md` sugiere que revelar es una accion deliberada separada de consultar; el criterio de aceptacion de esta mision dice literalmente "con votacion cerrada, los resultados se muestran". Se resolvio que `GET /resultados` funciona con `estado` en `CERRADA` **o** `RESULTADOS_REVELADOS` (no hace falta revelar primero para consultar administrativamente), y que `POST /revelar` es un hito formal aparte, valido solo desde `CERRADA`, para que la Mision 10 pueda distinguir "cerrada pero no comunicada" de "ya anunciada".

Entregables reales:

- `backend/app/services/votacion.py`: `revelar_resultados` (exige `CERRADA`; `VotacionNoCerradaError` si no, `ResultadosYaReveladosError` explicito -- con la fecha de revelacion anterior -- si ya estaba en `RESULTADOS_REVELADOS`) y `obtener_resultados` (exige `CERRADA` o `RESULTADOS_REVELADOS`; `ResultadosBloqueadosError` en `BORRADOR`/`ABIERTA`, sin calcular nada). Los tres desgloses -- por opcion, por tipo de unidad electoral y por grupo (circulo) -- y el total general se calculan siempre a partir de las filas de `Voto` de esa votacion, nunca de `UnidadElectoral.estado` (ese campo es de elegibilidad, no de resultados). Deliberadamente **no** se cruza grupo x opcion: muchos circulos tienen una sola unidad electoral, y ese cruce equivaldria a revelar el voto individual de esa unidad (DEC-022).
- `backend/app/schemas/votacion.py`: `VotacionResultadosResponse` (`total_votos`, `totales_por_opcion`, `totales_por_tipo_unidad` con `unidades_habilitadas`/`participacion` por tipo, `totales_por_grupo` con lo mismo por circulo) y `VotacionResponse` gana `resultados_revelados_at`.
- `POST /api/v1/votaciones/{id}/revelar` y `GET /api/v1/votaciones/{id}/resultados` (`backend/app/api/v1/endpoints/votaciones.py`), ambos en el mismo router protegido por `require_admin` (DEC-021) que el resto de la administracion de votacion: `/resultados` lo consume el panel administrativo (Mision 10), no el frontend de votacion (Mision 09), que `REGLAS_NEGOCIO.md` prohibe que muestre resultados.
- Exportacion basica: `GET /resultados?formato=csv` sobre el mismo endpoint (no uno aparte, para no duplicar el calculo), devuelve las tres secciones mas el total general como texto `text/csv` (`_resultados_a_csv`, en el endpoint, separado del calculo de resultados en el servicio).
- `backend/tests/test_resultados.py` (10 pruebas de servicio) y `backend/tests/test_resultados_endpoint.py` (6 pruebas HTTP): resultados bloqueados en `BORRADOR`/`ABIERTA`, 404 sin la votacion, resultados en `CERRADA` con los tres desgloses, mismo contenido en `RESULTADOS_REVELADOS`, revelar desde `CERRADA` (200, `resultados_revelados_at` seteado), revelar desde `BORRADOR`/`ABIERTA` (409) y revelar dos veces (409 explicito), un caso con dos opciones y los dos tipos de unidad electoral verificando que los tres desgloses suman exactamente el total de votos insertados, control de acceso administrativo sobre los dos endpoints nuevos, y el formato `csv`.

Decision nueva: DEC-022 (interpretacion de la ambiguedad CERRADA/revelar, y la decision de no cruzar grupo x opcion). De paso se corrigio un error de redaccion en DEC-021 ("cinco endpoints" listaba seis).

Criterios de aceptacion:

- Cumplido: con votacion `BORRADOR` o `ABIERTA`, `GET /resultados` responde `409` sin filtrar ningun numero.
- Cumplido: con votacion `CERRADA` (o `RESULTADOS_REVELADOS`), los resultados se muestran de forma consistente: `totales_por_opcion`, `totales_por_tipo_unidad` y `totales_por_grupo` suman exactamente el mismo total general.
- Cumplido: los conteos coinciden con las filas de `Voto` de esa votacion, no con estimaciones ni con `UnidadElectoral.estado`.

Con esto se cierra el backend "core" del sistema (Misiones 00-08). Las Misiones 09-11 restantes son frontend y preparacion operativa. El control de acceso sobre `POST /api/v1/votaciones/{id}/votos` y `POST /api/v1/habilitaciones/consultar` sigue pendiente a proposito (DEC-020): no es parte de ninguna mision de backend "core".

## Mision 09 - Frontend De Votacion

Estado: completada (2026-09-01)

Objetivo: crear la experiencia de consulta por celular y emision de voto, conectada a la API real (sin mockear), sin tocar nada del panel administrativo (eso es la Mision 10 completa).

Gap de backend cerrado primero (DEC-023): el frontend de votacion necesita la papeleta (que votacion esta abierta y sus opciones) para poder votar, pero `GET /votaciones/{id}/opciones` (Mision 07) esta protegido por `require_admin` -- el votante no tiene ese token. Se agrego `GET /api/v1/votaciones/abierta`, publico, que devuelve `{votacion_id, nombre, opciones: [{id, nombre, orden}]}` de la unica `Votacion` `ABIERTA`, o 404 si no hay ninguna. La busqueda de "la unica votacion ABIERTA" (antes `_votacion_abierta`, privada de `app/services/habilitacion.py`, DEC-018) se factorizo a `obtener_votacion_abierta` en `app/services/votacion.py`, reusada por ambos en vez de escribirla una tercera vez; `habilitacion.py` re-exporta `NoHayVotacionAbiertaError` desde ahi para no romper imports existentes. `backend/tests/test_votacion_abierta_endpoint.py` (3 pruebas) cubre papeleta con opciones, 404 sin votacion abierta y que la respuesta no expone nada mas alla de `votacion_id`/`nombre`/`opciones`. 102 pruebas de backend siguen pasando.

Entregables reales (frontend):

- `frontend/src/api/client.ts`: gana `apiPost` (antes solo existia `apiGet`), y ambos comparten un `ejecutar` interno que distingue una falla HTTP real (`ApiError.status` con codigo) de una falla de red (`ApiError.status === undefined`, `fetch` nunca respondio) -- asi el resto del codigo puede armar el mensaje de "sin conexion" sin duplicar el `try/catch` de red en cada pantalla. `ApiError` ahora tambien lleva `detail`, el texto que FastAPI manda en `{"detail": "..."}"`, usado para distinguir `PersonaNoAutorizadaError` (400) del resto de los 400 posibles sin adivinar por el codigo de estado solo.
- `frontend/src/api/habilitacion.ts` y `frontend/src/api/votacion.ts`: clientes tipados contra `POST /habilitaciones/consultar`, `GET /votaciones/abierta` y `POST /votaciones/{id}/votos`, con los tipos de respuesta calcados de los schemas Pydantic reales (verificado en el navegador contra la API real, no solo contra los tipos).
- `frontend/src/lib/motivos.ts`: traduce `motivo_no_disponible` (`BLOQUEADA_POR_INCIDENCIA`, `YA_VOTADO`, `PENDIENTE_DEFINICION_POSTULANTES`/`_BAJA`) a lenguaje claro, y etiqueta cada unidad electoral segun su tipo ("Votar por tu matrimonio consagrado" / "Votar por el bloque de tu círculo") -- nunca el codigo tecnico crudo en pantalla. `frontend/src/lib/celular.ts`: validacion basica de celular en el cliente (9 o 10 digitos, no todo ceros) antes de llamar a la API; el backend (`normalizar_celular`) sigue siendo la fuente de verdad. `frontend/src/lib/errores.ts`: mensaje generico por tipo de `ApiError` (sin conexion, sin votacion abierta, error generico), sin exponer detalle tecnico del backend en las pantallas que no lo necesitan.
- `frontend/src/components/ConsultaCelularForm.tsx`: input + submit contra `POST /habilitaciones/consultar`, con sus tres estados (cargando, celular invalido -- validado antes de llamar a la API --, sin conexion).
- `frontend/src/components/ResultadoConsulta.tsx`: interpreta `HabilitacionConsultaResponse` -- celular inexistente (`unidades: []`) muestra "este celular no está en el padrón"; cada unidad no disponible muestra su motivo traducido; el doble rol de jefe consagrado se muestra como dos botones separados y claramente etiquetados, nunca combinados (criterio de aceptacion explicito de esta mision, cubierto por test).
- `frontend/src/components/PapeletaVoto.tsx`: si `personas.length > 1` (celular compartido entre conyuges, DEC-008) pide confirmar cual de las personas listadas esta votando antes de mostrar la papeleta; si el backend rechaza esa persona (`PersonaNoAutorizadaError`, 400, detectado por el texto "autorizada" en `ApiError.detail`) muestra un error claro y vuelve a la lista para elegir otra, sin adivinar de antemano quien es el jefe o el integrante correcto. Trae la papeleta de `GET /votaciones/abierta`, deja elegir una opcion y hace `POST /votaciones/{id}/votos`. El boton de confirmar se deshabilita apenas se envia (`enviando`, evita doble submit por doble click) y desaparece del todo al pasar a la siguiente pantalla (evita el reintento). Un 409 de "ya votado" (doble pestaña) se delega al padre como mensaje amigable, nunca como error generico.
- `frontend/src/components/ConfirmacionVoto.tsx`: pantalla final con la fecha/hora del voto (`fecha_emision`, formateada localmente), sin ningun boton -- ni de reenvio ni de navegacion -- para que no exista ningun camino de volver a emitir el mismo voto desde ahi.
- `frontend/src/routes/VotacionPage.tsx`: orquesta las cinco pantallas (`consulta` -> `resultado` -> `papeleta` -> `confirmado` / `ya-votado`) con estado local, sin routing adicional. `App.tsx` la monta en `/`; la pantalla de estado tecnico de la Mision 01 (`HomePage`) se movio a `/estado`.
- Regla dura verificada: ningun componente de esta mision llama a `GET /resultados` ni a `POST /revelar` -- `frontend/src/test/no-resultados.test.ts` escanea todo `frontend/src/` (excluyendo la carpeta `test/`) buscando esas dos rutas como texto literal y falla si aparecen; complementado con `grep -rn "/resultados|/revelar" frontend/src` a mano, que solo encuentra el propio test.
- Testing: se agrego `vitest` + `@testing-library/react` (+ `@testing-library/user-event`, `@testing-library/jest-dom`, `jsdom`) al scaffold, que no tenia ningun framework de testing de frontend (`frontend/vite.config.ts`, seccion `test`; `frontend/src/test/setup.ts`; script `npm test` en `package.json`). 28 pruebas de componente en 8 archivos, todas mockeando la capa de API (`vi.mock`, sin depender del backend real corriendo): celular invalido (sin llamar a la API), estado de carga, sin conexion, celular no encontrado, unidad bloqueada mostrando el motivo traducido sin el codigo crudo, doble rol mostrando dos botones separados, celular compartido pidiendo confirmar la persona, persona rechazada dejando elegir otra, voto exitoso deshabilitando el boton de reintento, 409 de voto duplicado mostrado como "tu voto ya fue registrado", y dos pruebas de integracion end-to-end sobre `VotacionPage` (flujo completo exitoso, y el 409 llegando hasta la pantalla final).
- Verificacion manual en navegador real (no solo mockeada): se corrieron `alembic upgrade head` + `seed_dev.py` sobre un SQLite local, se abrio una `Votacion` con dos opciones via los endpoints administrativos, se levantaron `uvicorn` y `npm run dev`, y se manejo un Chrome real con Playwright contra ambos servidores -- flujo completo de celular compartido (pide confirmar persona, vota, pantalla de confirmacion sin ningun boton), celular inexistente ("no está en el padrón") y jefe de bloque no consagrado (opcion unica, voto directo). Sin errores de consola mas alla de un 404 de `/favicon.ico` (preexistente del scaffold de la Mision 01, no de esta mision).

Criterios de aceptacion:

- Cumplido: el usuario entiende cuando no esta habilitado -- celular inexistente, o cada unidad con su motivo traducido.
- Cumplido: el usuario con dos roles (doble rol de jefe consagrado) puede elegir claramente que voto emitir -- dos botones separados y etiquetados, nunca combinados.
- Cumplido: la interfaz no muestra resultados -- verificado por busqueda automatizada (`no-resultados.test.ts`) y manual.
- Cumplido: el flujo impide reintentos ambiguos despues de votar -- boton deshabilitado durante el envio, pantalla de confirmacion sin ningun boton, y el 409 de voto duplicado se muestra como mensaje amigable en vez de reintento.

**Fix post-commit original (mismo dia): DEC-024** -- `PapeletaVoto.tsx` trataba cualquier `409` de `POST /votos` como voto duplicado, pero ese endpoint devuelve `409` para tres errores distintos (`VotoDuplicadoError`, `VotacionNoDisponibleError`, `UnidadElectoralNoDisponibleError`); en los ultimos dos el voto nunca se registro y la pantalla afirmaba lo contrario. Corregido clasificando por el texto de `detail` (`clasificarConflicto`, sin tocar el backend); solo el duplicado real dispara `onYaVotado()`, los otros dos muestran un mensaje que invita a reintentar. Dos pruebas nuevas en `PapeletaVoto.test.tsx` verifican que esos dos casos no llaman a `onYaVotado`.

Fuera de alcance a proposito, es la Mision 10 completa: dashboard, incidencias, importaciones, apertura/cierre y resultados finales.

## Mision 10 - Frontend Administrativo

Estado: completada (2026-09-01)

Objetivo: crear el panel administrativo (React, mismo stack que la Mision 09) para operar la votacion de punta a punta: importar el padron, revisar incidencias, gestionar el ciclo de vida de una votacion (crear/cargar opciones/abrir/cerrar) y ver resultados solo cuando corresponde. Nada de esto toca `frontend/` (Mision 09).

Gaps de backend cerrados primero (DEC-025), encontrados al revisar que endpoints existian realmente para esta mision: `POST /padron/importaciones` (Mision 04) no tenia `require_admin` a pesar de poder reimportar/recrear todo el padron -- un olvido, no una decision, corregido aca. No existia ningun `GET /votaciones` que listara todas las votaciones -- sin el, el panel no tenia forma de descubrir que `votacion_id` administrar salvo `GET /votaciones/abierta` (que solo sirve mientras hay una ABIERTA). Se agregan cuatro endpoints, los cuatro admin-protegidos: `GET /votaciones` (reusa `VotacionResponse`), `GET /padron/importaciones` (reusa `ImportacionPadronResponse`), y `GET /padron/incidencias` + `POST /padron/incidencias/{id}/resolver` (schema nuevo `IncidenciaPadronResponse`, servicio nuevo `app/services/padron/administracion.py`). `resolver_incidencia` es deliberadamente solo trazabilidad administrativa (`resuelto_por`/`resuelto_at`): nunca recalcula `UnidadElectoral.estado`, porque hacerlo exigiria resolver antes DEC-012/013/014 (bajas, circulos de postulantes, doble rol), todavia pendientes de negocio. 111 pruebas de backend (101 antes de esta mision + 10 nuevas: `test_padron_administracion_endpoint.py` completo, mas los casos agregados a `test_padron_endpoint.py` y `test_votacion_endpoint.py`).

Entregables reales (frontend, `frontend-admin/`, proyecto nuevo separado de `frontend/`):

- `src/api/adminToken.ts` + `src/context/AuthContext.tsx`: el `ADMIN_API_KEY` pegado en el login se guarda en `sessionStorage` (nunca `localStorage` ni hardcodeado) y se manda como header `X-Admin-Token` en cada request (`src/api/client.ts`). Cualquier `401`/`403` real de un endpoint administrativo dispara `notificarNoAutorizado()`, que `AuthContext` escucha para limpiar el token y volver a `/login` -- sin que quede un token invalido reintentando en loop. `src/routes/LoginPage.tsx` valida el token contra `GET /votaciones` antes de entrar, para no parpadear el dashboard y rebotar.
- `src/routes/DashboardPage.tsx`: lista de votaciones (`GET /votaciones`) con su estado; `src/routes/VotacionDetailPage.tsx` muestra el estado operativo (`GET /votaciones/{id}/estado`) y el resumen de la ultima importacion (el JSON que ya guarda `ImportacionPadron.resumen`, sin recalcular nada) -- nunca un desglose por opcion mientras la votacion no esta CERRADA o RESULTADOS_REVELADOS.
- `src/routes/IncidenciasPage.tsx`: tabla desde `GET /padron/incidencias`, filtrable por severidad/tipo/resuelta, con "marcar como revisada" (`POST .../resolver`) y una nota visible de que esto no rehabilita ninguna unidad.
- `src/routes/ImportacionesPage.tsx`: historial (`GET /padron/importaciones`) mas un boton de nueva importacion que exige un segundo paso explicito de confirmacion antes de ejecutar `POST /padron/importaciones` (operacion pesada, nunca a un solo click).
- `src/routes/VotacionDetailPage.tsx` + `src/routes/CrearVotacionPage.tsx`: crear votacion, cargar opciones en BORRADOR, abrir/cerrar, con los errores del backend (`OtraVotacionAbiertaError`, `VotacionSinOpcionesError`, etc.) traducidos por substring de `detail` en `src/lib/erroresVotacion.ts` -- mismo patron que `clasificarConflicto` de `PapeletaVoto.tsx` (Mision 09, DEC-024).
- `src/components/ResultadosView.tsx`: el unico punto que llama a `GET /resultados` y `POST /revelar`. `VotacionDetailPage` solo la monta -- nunca oculta en el DOM -- cuando `votacion.estado` es `CERRADA` o `RESULTADOS_REVELADOS` (el tipo de su prop `estado` ya excluye `BORRADOR`/`ABIERTA` en tiempo de compilacion); "revelar" solo se ofrece desde `CERRADA`.
- Testing (`vitest` + `@testing-library/react`, mismo scaffold que la Mision 09): 24 pruebas en 4 archivos. `src/test/no-resultados-prematuros.test.tsx` es la version invertida del test de la Mision 09 -- como este panel si necesita llamar a `/resultados`/`/revelar`, en vez de un grep estatico verifica en tiempo de ejecucion que esas dos llamadas nunca ocurren con `BORRADOR`/`ABIERTA` (y que si ocurren con `CERRADA`/`RESULTADOS_REVELADOS`). `src/test/sesion-401.test.tsx` y `src/api/client.test.ts` verifican que un `401`/`403` real limpia el token y redirige a `/login`. `src/lib/erroresVotacion.test.ts` cubre la traduccion de cada error del backend.
- Verificacion: `tsc --noEmit` y `vite build` sin errores, 24/24 pruebas de vitest y 111/111 de pytest en verde. No se hizo una pasada manual con navegador real (Playwright) como en la Mision 09 -- queda pendiente antes de operar una votacion real (razonable cubrirlo en la Mision 11).

Criterios de aceptacion:

- Cumplido: el administrador puede monitorear (dashboard, estado operativo, resumen de importacion) sin ver resultados prematuros -- verificado por `no-resultados-prematuros.test.tsx`.
- Cumplido: las incidencias del padron son visibles (`GET /padron/incidencias`, filtrable) y accionables (`POST .../resolver`), con la aclaracion de que resolver es solo trazabilidad.
- Cumplido: los resultados solo aparecen con la votacion CERRADA o RESULTADOS_REVELADOS, nunca antes.

## Mision 11 - Prueba General Y Preparacion Operativa

Estado: en curso (2026-09-01)

Objetivo: validar el sistema completo antes de usarlo en una votacion real.

Resolucion de las tres decisiones de negocio pendientes desde la Mision 02,
autorizada explicitamente por Sebad para que el orquestador las resuelva con
el razonamiento mas logico disponible -- a diferencia de DEC-017, **no** son
una confirmacion del dueño real del Excel:

- **DEC-014 (doble rol de jefe consagrado)**: resuelta sin ningun cambio de
  codigo. `docs/REGLAS_NEGOCIO.md` ya decia textualmente que la persona con
  doble rol debe ver "opciones separadas" y registrar "cada voto con su
  unidad electoral" -- exactamente lo implementado desde la Mision 06
  (DEC-020). Documentado en DEC-026.
- **DEC-012 (bajas de personas)**: resuelta hacia "no vota". Las 8 unidades
  en `PENDIENTE_DEFINICION_BAJA` (verificado de nuevo contra el Excel real:
  siguen siendo exactamente 8 de 314) son, por definicion de la regla de
  DEC-016, unidades sin un solo integrante activo. Quedan bloqueadas de
  forma **permanente** para esta eleccion, reutilizando el estado que ya
  existia -- sin cambio de esquema ni de importador. Documentado en DEC-027.
- **DEC-013 (circulos de postulantes)**: resuelta hacia "no votan este
  ciclo". Las 25 unidades en `PENDIENTE_DEFINICION_POSTULANTES` (verificado
  de nuevo contra el Excel real) quedan bloqueadas de forma **permanente**,
  mismo criterio y mismo estado reutilizado. Documentado en DEC-028.
- Unico cambio de codigo asociado: `frontend/src/lib/motivos.ts` deja de
  decir "Todavía no está habilitada para votar." (ya no es preciso una vez
  que la decision es definitiva) y pasa a decir "Esta unidad no tiene voto
  habilitado en esta elección.", con su prueba actualizada. No hizo falta
  ningun cambio en `frontend-admin` -- no tiene un mensaje equivalente
  orientado al votante.
- Impacto en los numeros: de 314 unidades electorales, 265 `HABILITADA`
  (sin cambio) + 16 `BLOQUEADA_POR_INCIDENCIA` (sin cambio) + 33 (25 + 8)
  bloqueadas de forma permanente por estas dos decisiones. El total votable
  de esta eleccion sigue siendo 265, igual que lo que ya se contaba como
  habilitado antes de esta mision.

Endurecimiento para operacion 24/7 (DEC-029): `POST /habilitaciones/consultar`
y `POST /votaciones/{id}/votos` siguen sin control de acceso a proposito
(DEC-020) -- restringir por red no aplica a un sistema expuesto en internet
por dias o semanas, y una contrasena compartida no aporta trazabilidad real.
Se agrego rate limiting por IP (`slowapi`, `backend/app/core/rate_limit.py`):
`RATE_LIMIT_POR_MINUTO` (default 20/minuto), `429` al superarlo, resuelto
contra la IP real del cliente (`get_client_ip`, con soporte de
`X-Forwarded-For` para no rate-limitar a todos los votantes juntos detras de
un proxy). No reemplaza autenticacion real por votante -- eso sigue fuera de
alcance, igual que ya quedo documentado en DEC-020.

Dataset de prueba y casos criticos: `backend/tests/test_mision11_casos_criticos.py`
(12 pruebas nuevas), un circulo mixto sintetico que ejercita de punta a
punta -- habilitacion y registro de voto real, servicios de las Misiones
05/06 -- cada caso pedido: matrimonio consagrado votando, bloque no
consagrado votando, circulo mixto (los dos tipos de unidad en el mismo
circulo, votando de forma independiente), doble rol de jefe consagrado (dos
votos independientes), doble voto sobre la misma unidad (bloqueado,
`VotoDuplicadoError`, sin segunda fila), celular duplicado entre matrimonios
distintos (las dos unidades candidatas bloqueadas por su propia incidencia
CRITICA), celular inexistente (no habilitado), y una unidad en cada uno de
los cuatro estados posibles -- incluidas las dos resoluciones nuevas de esta
mision -- confirmando el `motivo_no_disponible` exacto que devuelve cada
una. Ademas, `backend/tests/test_rate_limit.py` (3 pruebas: `429` al superar
el limite en cada uno de los dos endpoints, y aislamiento por IP via
`X-Forwarded-For`). **126 pruebas de backend en verde** (111 previas + 3 +
12), y las **30 pruebas de `frontend/`** (28 previas + 2 de la Mision 09
sin cambio) siguen en verde con el mensaje nuevo.

Verificado contra el Excel real (reimportado de nuevo para esta mision, no
solo contra los fixtures sinteticos de los tests): personas, matrimonios,
grupos, unidades electorales e incidencias coinciden exactamente con los
numeros ya documentados en la Mision 04/DEC-019 -- 314 unidades, 265/16/8/25
por estado.

Checklist operativo, plan de backup y guia operativa (documentos, no
codigo): `docs/CHECKLIST_OPERATIVO.md` (que revisar antes de abrir, durante
la votacion y en el cierre -- `ADMIN_API_KEY`, `RATE_LIMIT_POR_MINUTO`,
ultima importacion correcta, incidencias criticas revisadas),
`docs/PLAN_BACKUP.md` (cubre los dos escenarios posibles de la base real de
DigitalOcean -- Managed Database con backup automatico, o Postgres sin
backup administrado con rutina de `pg_dump` manual -- **pendiente confirmar
con Sebad cual de los dos aplica**), y `docs/GUIA_OPERACION_VOTACION.md`
(paso a paso: importar padron, crear votacion y opciones, abrir, monitorear,
cerrar, revelar resultados, con el llamado HTTP y el paso equivalente en el
panel para cada uno).

Pendiente para cerrar esta mision:

- **Validacion contra PostgreSQL real**: corrida completa (migraciones,
  importar padron, abrir votacion, votar casos de prueba, cerrar, revelar,
  resultados) contra la base v18 real de DigitalOcean. Necesita el
  `DATABASE_URL` real, que Sebad va a pasar mas adelante -- por ahora, todo
  lo de esta mision corrio solo contra SQLite (igual que el resto de la
  suite de pruebas desde la Mision 03).
- **Pasada manual con navegador real sobre `frontend-admin`**: pendiente
  desde el cierre de la Mision 10. Para esta mision se levanto el backend
  real (SQLite local con el padron real ya importado, sin ninguna votacion
  creada todavia) mas `frontend-admin` en `npm run dev`, y Sebad la esta
  probando el mismo a mano desde el navegador (login, dashboard, incidencias,
  importaciones, crear/abrir/cerrar votacion, resultados) -- no hay
  herramienta de navegador/Playwright conectada en esta sesion para hacerlo
  de forma automatizada.

Entregables:

- Dataset de prueba.
- Pruebas de casos criticos.
- Checklist operativo.
- Plan de backup.
- Guia de apertura, monitoreo, cierre y resultados.

Criterios de aceptacion:

- Cumplido: los casos de matrimonio consagrado, bloque no consagrado y
  grupo mixto funcionan (`test_mision11_casos_criticos.py`).
- Cumplido: los intentos de doble voto quedan bloqueados (mismo archivo, y
  ya cubierto desde la Mision 06).
- Cumplido: los resultados no se revelan antes del cierre (ya cubierto
  desde la Mision 08, DEC-022; sin cambios en esta mision).
- Cumplido: existe una guia clara para operar durante todo el periodo de
  votacion, no solo "el dia" (`docs/GUIA_OPERACION_VOTACION.md`).
- Pendiente: el ciclo completo corriendo sin diferencias contra PostgreSQL
  real, y la confirmacion de Sebad sobre la pasada manual de
  `frontend-admin` -- ver "Pendiente para cerrar esta mision" arriba.

## Proxima Mision Recomendada

No queda ninguna mision nueva planificada: la Mision 11 es la ultima de
`BACKLOG_INICIAL.md`. Lo que resta no es una mision nueva, sino cerrar los
dos pendientes explicitos de la Mision 11 (validacion contra PostgreSQL real
y confirmacion de la pasada manual de `frontend-admin`, ver arriba) antes de
operar una votacion real.

El control de acceso sobre `POST /api/v1/votaciones/{id}/votos` y `POST /api/v1/habilitaciones/consultar` sigue pendiente a proposito (DEC-020, DEC-021): ni la Mision 09 ni la Mision 10 le agregaron ninguno, tal como estaba documentado. Conviene resolverlo antes de operar una votacion real (Mision 11).
