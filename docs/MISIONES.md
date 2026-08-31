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
- `backend/tests/test_importador_padron.py`: 15 pruebas rapidas contra un `.xlsx` sintetico de 14 filas (`_construir_excel_fixture`) que reproduce a proposito un matrimonio de un solo integrante sin viudez, dos etiquetas `MATRIMONIO` repetidas en circulos distintos, un celular compartido entre conyuges, una fila de resumen al pie, una celda combinada, un jefe que solo existe en `LISTADO JEFES` (con y sin correspondencia), un matrimonio consagrado sin ningun celular valido en ninguno de sus dos integrantes (DEC-017, bloquea la unidad) y un matrimonio donde solo uno de los dos tiene celular propio (no bloquea, aunque el otro dependa de la reconciliacion de `LISTADO JEFES` para completar el suyo). Mas 1 prueba `@pytest.mark.slow` que corre contra el Excel real y verifica los totales exactos de `PADRON_ANALISIS.md`. `backend/tests/test_padron_endpoint.py`: 3 pruebas del endpoint HTTP (201, 404, 409) con `TestClient` y un SQLite migrado por prueba.
- `openpyxl` se movio de `requirements-dev.txt` a `requirements.txt`/`dependencies` (ya no es solo una herramienta de analisis: el importador la usa en runtime).

Resultado de correr el importador contra el Excel real (`python -m app.services.padron.importar`), verificado contra `PADRON_ANALISIS.md`:

- 1113 personas, 571 matrimonios (260 consagrados, 292 no consagrados, 19 sin definir), 93 grupos -- coinciden exactamente con el analisis de la Mision 02.
- 690 incidencias (72 CRITICA, 43 ALTA, 168 MEDIA, 407 BAJA). Los 682/64 originales de la Mision 02 coinciden salvo por las 8 incidencias `MATRIMONIO_SIN_CELULAR_DISPONIBLE` (CRITICA) agregadas por DEC-017: 7 matrimonios (8 personas -- seis de un solo integrante, uno de dos) donde ningun integrante tiene un celular que normalice a un numero valido.
- Reconciliacion de `LISTADO JEFES`: 110 por nombre+celular, 29 por celular, 4 por nombre (celular discrepante, no completado automaticamente), 3 sin correspondencia -- coincide con DEC-009. Se verifico ademas, contra el Excel real, que ninguno de los 7 circulos con bloque no consagrado y jefe resuelto queda sin un celular valido tras esta reconciliacion (0 casos sobre 54 circulos), asi que `BLOQUE_SIN_CELULAR_JEFE_DISPONIBLE` no se agrego a la taxonomia -- no hay ningun caso real que lo justifique (DEC-017).
- 314 unidades electorales (260 `MATRIMONIO_CONSAGRADO` + 54 `BLOQUE_NO_CONSAGRADO`): 216 `HABILITADA`, 70 `BLOQUEADA_POR_INCIDENCIA`, 22 `PENDIENTE_DEFINICION_POSTULANTES`, 6 `PENDIENTE_DEFINICION_BAJA`. Votos maximos habilitables hoy: 203 `MATRIMONIO_CONSAGRADO` + 13 `BLOQUE_NO_CONSAGRADO` = 216 (baja de 224 tras aplicar DEC-017; tres de los siete matrimonios sin celular tambien tenian todos sus integrantes de baja y antes contaban como `PENDIENTE_DEFINICION_BAJA`, asi que `BLOQUEADA_POR_INCIDENCIA` sube en 11, no en 8).

Decisiones nuevas: DEC-015 (rechazo de reimportacion con votacion abierta/cerrada; reemplazo transaccional mientras este en borrador), DEC-016 (prioridad de estados de unidad electoral: incidencia critica > postulantes pendiente > baja pendiente > habilitada) y DEC-017 (matrimonio sin ningun celular valido, a partir de la aclaracion textual del dueño del padron sobre DEC-005).

Criterios de aceptacion:

- Cumplido: el importador no deja habilitada ninguna unidad electoral con una incidencia CRITICA asociada (`BLOQUEADA_POR_INCIDENCIA`).
- Cumplido: los duplicados de celular entre matrimonios distintos (`CELULAR_DUPLICADO`, `CELULAR_DUPLICADO_EN_LISTADO_JEFES`, `CELULAR_DISCREPANTE_ENTRE_HOJAS`) son CRITICA y bloquean la unidad electoral asociada; el celular compartido entre conyuges (`CELULAR_COMPARTIDO_CONYUGES`, DEC-008) no bloquea.
- Cumplido: un matrimonio donde ningun integrante tiene celular valido (`MATRIMONIO_SIN_CELULAR_DISPONIBLE`, DEC-017) bloquea su unidad electoral; un matrimonio donde al menos uno de los dos si tiene celular valido no se ve afectado, aunque el otro dependa de `LISTADO JEFES` para completar el suyo.
- Cumplido: cada matrimonio consagrado (incluidos los 22 viudos, DEC-011) genera una unidad `MATRIMONIO_CONSAGRADO`.
- Cumplido: cada circulo con al menos un matrimonio no consagrado genera una unidad `BLOQUE_NO_CONSAGRADO` (54, DEC-010), independientemente de si el jefe se resuelve por la hoja principal o por `LISTADO JEFES`.

Pendiente para el negocio, no bloquea la Mision 05: bajas de personas (DEC-012), circulos de postulantes (DEC-013) y doble rol de jefes consagrados (DEC-014). Aplicar cualquiera de las tres es un `UPDATE` sobre `unidades_electorales`/`incidencias_padron`, no una reimportacion (DEC-016).

## Mision 05 - Motor De Habilitacion Por Celular

Estado: pendiente

Objetivo: resolver que puede votar una persona a partir de su celular.

Entregables:

- Servicio de consulta de habilitacion.
- Endpoint `POST /api/v1/habilitaciones/consultar`.
- Respuesta con persona, unidades disponibles e incidencias.
- Manejo explicito del jefe consagrado con dos unidades posibles.

Criterios de aceptacion:

- Celular inexistente responde no habilitado.
- Celular duplicado responde incidencia bloqueante.
- Matrimonio ya votado no vuelve a habilitarse.
- Jefe con bloque no consagrado ya votado no vuelve a habilitarse.
- Persona con dos roles ve dos opciones separadas.

## Mision 06 - Registro De Voto Y Auditoria

Estado: pendiente

Objetivo: registrar votos de forma idempotente y trazable.

Entregables:

- Endpoint `POST /api/v1/votaciones/{id}/votos`.
- Validacion de votacion abierta.
- Validacion de unidad electoral disponible.
- Registro de voto con fecha, celular consultado y persona emisora.
- Pruebas de doble voto.

Criterios de aceptacion:

- Una unidad electoral no puede votar dos veces en la misma votacion.
- No se puede votar si la votacion esta cerrada.
- No se puede votar con una unidad electoral bloqueada por incidencia.
- Cada voto conserva datos suficientes para auditoria.

## Mision 07 - Administracion De Votacion

Estado: pendiente

Objetivo: permitir administrar apertura, monitoreo operativo, cierre y revelacion.

Entregables:

- Endpoints de abrir y cerrar votacion.
- Estado operativo de votacion.
- Conteos de habilitados, emitidos y pendientes.
- Control de acceso administrativo inicial.

Criterios de aceptacion:

- Solo una votacion abierta puede recibir votos.
- El cierre registra fecha, hora y usuario.
- Antes del cierre no se devuelven resultados por opcion.

## Mision 08 - Resultados

Estado: pendiente

Objetivo: revelar resultados solo despues del cierre y con trazabilidad.

Entregables:

- Endpoint de resultados.
- Validacion de estado cerrado o revelado.
- Totales por opcion.
- Totales por grupo y tipo de unidad electoral.
- Exportacion basica si aplica.

Criterios de aceptacion:

- Con votacion abierta, el endpoint de resultados responde bloqueado.
- Con votacion cerrada, los resultados se muestran de forma consistente.
- Los conteos coinciden con los votos registrados.

## Mision 09 - Frontend De Votacion

Estado: pendiente

Objetivo: crear la experiencia de consulta por celular y emision de voto.

Entregables:

- Pantalla de consulta por celular.
- Pantalla de seleccion de unidad electoral.
- Pantalla de voto.
- Pantalla de confirmacion.
- Estados de error e incidencia.

Criterios de aceptacion:

- El usuario entiende cuando no esta habilitado.
- El usuario con dos roles puede elegir claramente que voto emitir.
- La interfaz no muestra resultados.
- El flujo impide reintentos ambiguos despues de votar.

## Mision 10 - Frontend Administrativo

Estado: pendiente

Objetivo: crear vistas administrativas para padron, incidencias, estado y resultados.

Entregables:

- Dashboard operativo.
- Vista de incidencias.
- Vista de importaciones.
- Controles de apertura y cierre.
- Vista de resultados finales.

Criterios de aceptacion:

- El administrador puede monitorear sin ver resultados prematuros.
- Las incidencias del padron son visibles y accionables.
- Los resultados solo aparecen cuando corresponde.

## Mision 11 - Prueba General Y Preparacion Operativa

Estado: pendiente

Objetivo: validar el sistema completo antes de usarlo en una votacion real.

Entregables:

- Dataset de prueba.
- Pruebas de casos criticos.
- Checklist operativo.
- Plan de backup.
- Guia de apertura, monitoreo, cierre y resultados.

Criterios de aceptacion:

- Los casos de matrimonio consagrado, bloque no consagrado y grupo mixto funcionan.
- Los intentos de doble voto quedan bloqueados.
- Los resultados no se revelan antes del cierre.
- Existe una guia clara para operar el dia de la votacion.

## Proxima Mision Recomendada

La siguiente mision recomendada es la Mision 05: Motor De Habilitacion Por Celular, sobre el padron real ya importado (personas, matrimonios, grupos, unidades electorales e incidencias) en la Mision 04.
