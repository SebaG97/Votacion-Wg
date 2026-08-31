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

Estado: pendiente

Objetivo: convertir el Excel validado en personas, matrimonios, grupos, jefes y unidades electorales.

Entregables:

- Endpoint o comando de importacion.
- Servicio de normalizacion.
- Registro de importacion.
- Generacion de incidencias.
- Resumen de votos maximos por tipo y grupo.

Criterios de aceptacion:

- El importador no habilita registros con incidencias criticas.
- Los duplicados de celular quedan bloqueados para voto automatico.
- Los matrimonios consagrados generan una unidad electoral por matrimonio.
- Los bloques no consagrados generan una unidad electoral por jefe/grupo.

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

La siguiente mision recomendada es la Mision 04: Importador Y Normalizador Del Padron, siguiendo el orden recomendado en `docs/PADRON_ANALISIS.md` seccion 6.3 sobre el modelo y las migraciones ya implementados en la Mision 03.
