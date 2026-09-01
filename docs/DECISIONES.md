# Decisiones Del Proyecto

## Formato

Cada decision debe registrar:

- Fecha.
- Contexto.
- Decision.
- Consecuencias.

## DEC-001 - Separacion Backend Y Frontend

Fecha: 2026-08-29

Contexto: El proyecto debe seguir el estilo utilizado en el sistema TRAMOS, con una carpeta principal y aplicaciones separadas.

Decision: Mantener `backend` y `frontend` como carpetas independientes dentro de la carpeta principal.

Consecuencias: Cada aplicacion podra tener dependencias, documentacion, variables de entorno y pruebas propias.

## DEC-002 - Celular Como Consulta, No Como Confianza Absoluta

Fecha: 2026-08-29

Contexto: El requerimiento define el celular como numero unico de referencia para consultar habilitacion.

Decision: Usar celular como identificador principal de consulta, pero validar duplicados e inconsistencias durante la importacion del padron.

Consecuencias: Si aparecen duplicados, la aplicacion debera tratarlos como incidencia y no permitir voto automatico hasta resolverlos.

## DEC-003 - Unidad Electoral Separada De Persona

Fecha: 2026-08-29

Contexto: Una persona puede votar por su matrimonio consagrado, por un grupo no consagrado si es jefe, o por ambos roles.

Decision: Modelar el derecho a voto como `unidad_electoral`, separada de la persona.

Consecuencias: Se facilita controlar un voto por matrimonio, un voto por bloque no consagrado y casos mixtos.

## DEC-004 - Health Check Versionado Para Integracion Inicial

Fecha: 2026-08-29

Contexto: La Mision 01 requiere validar que frontend y backend pueden conectarse sin adelantar reglas de padron, habilitacion, voto ni resultados.

Decision: Crear `GET /api/v1/health` como contrato tecnico minimo y consumirlo desde la pantalla base del frontend mediante `VITE_API_BASE_URL`.

Consecuencias: Se puede verificar conectividad local entre aplicaciones manteniendo backend y frontend separados, sin exponer informacion electoral ni resultados.

## DEC-005 - El Valor 0 En Celular Es Ausencia De Dato, No Un Numero

Fecha: 2026-08-31

Contexto: El analisis del Excel (Mision 02) encontro dos filas de persona con el literal `0` en la columna `CELULAR ` (filas 593 y 939), y una con el literal `EL` en una fila que resulto ser un rotulo decorativo. El relevamiento preliminar los habia contado como un duplicado de celular, porque el mismo `0` aparece dos veces.

Decision: Normalizar el celular a 10 digitos con cero inicial (`09XXXXXXXX`) y tratar como ausencia de dato todo valor que, tras quitar los caracteres no numericos, quede compuesto solo por ceros. Estos casos generan la incidencia `CELULAR_PLACEHOLDER` con severidad ALTA y **no** cuentan como duplicado.

Consecuencias: El conteo de duplicados reales de celular no queda contaminado por marcadores de "no tiene telefono". Estas personas quedan sin celular y por lo tanto sin capacidad de consultar habilitacion por si mismas; si pertenecen a un matrimonio consagrado, el conyuge puede votar por la unidad. La misma regla se aplica a la columna `E-MAIL `, donde 126 celdas traen `0`.

## DEC-006 - Las Filas De Resumen Se Descartan Por Deteccion Estructural

Fecha: 2026-08-31

Contexto: La columna `Consagrados` parecia corrupta por contener valores como `496` y `0.4546...` junto a las marcas `1`. El analisis mostro que esos valores no estan mezclados con los datos: viven exclusivamente en las dos ultimas filas del Excel (1190 y 1191), que son un pie de totales y porcentajes agregado a mano por el operador del padron.

Decision: No aplicar reglas de limpieza sobre los valores de las columnas de marca. En cambio, clasificar cada fila estructuralmente antes de interpretarla: fila de persona, fila separadora de circulo, fila de resumen, fila vacia o fila rotulo. Toda celda no vacia en `Consagrados`, `sin consagracion`, `Jefes`, `ML`, `Viudos` y `No ML` se interpreta como marca booleana verdadera; las celdas con solo espacios se tratan como vacias.

Consecuencias: El importador no depende de numeros de fila fijos y sigue funcionando si el operador agrega o quita filas al pie. Las 1190 filas crudas se reducen a 1113 personas, 73 filas separadoras de circulo, 2 filas de resumen, 1 vacia y 1 rotulo. Las columnas de marca quedan libres de valores anomalos sin necesidad de umbrales arbitrarios.

## DEC-007 - Los Matrimonios Se Agrupan Por Etiqueta Mas Contiguidad De Filas

Fecha: 2026-08-31

Contexto: La columna `MATRIMONIO` no es un identificador sino texto libre con apellidos combinados. Siete etiquetas se repiten en circulos distintos (`PEREIRA FERNANDEZ`, `GONZALEZ RODRIGUEZ`, `MALDONADO CACERES`, `RODRIGUEZ CARDOZO`, `Reyes` y dos mas), de modo que agrupar solo por etiqueta uniria personas de matrimonios ajenos.

Decision: Agrupar por etiqueta normalizada (sin tildes, mayusculas, espacios colapsados) **mas** contiguidad de filas **mas** un tope de dos integrantes por grupo. No usar heuristica de apellidos.

Consecuencias: Se obtienen 571 matrimonios (542 de dos integrantes y 29 de uno), ninguno con mas de dos personas ni partido en filas no contiguas. La etiqueta original se conserva como `codigo_externo` para trazabilidad contra el Excel, nunca como clave. La regla depende de que los conyuges esten en filas consecutivas, lo cual se verifico para las 1113 filas de persona: si una carga futura rompe esa premisa, el script lo expone como matrimonio incompleto.

## DEC-008 - El Celular Compartido Entre Conyuges No Bloquea El Voto

Fecha: 2026-08-31

Contexto: DEC-002 establecio que los duplicados de celular deben tratarse como incidencia y bloquear el voto automatico. El analisis del Excel encontro 4 casos de celular repetido en la hoja principal, y los cuatro son los dos integrantes del mismo matrimonio compartiendo telefono. No hay ningun caso de dos personas de matrimonios distintos con el mismo numero.

Decision: Distinguir dos tipos de duplicado. `CELULAR_COMPARTIDO_CONYUGES` (ambas personas en el mismo matrimonio) es severidad ALTA y **no bloquea**, porque el matrimonio consume un unico voto y el numero resuelve a una sola unidad electoral. `CELULAR_DUPLICADO` (personas de matrimonios distintos) es severidad CRITICA y bloquea, segun DEC-002. Excepcion: si uno de los conyuges es ademas jefe con bloque no consagrado propio, el numero resuelve a dos unidades y debe presentarse la eleccion explicita prevista en las reglas de negocio.

Consecuencias: No se bloquean 8 personas por una situacion domestica normal. La regla de DEC-002 sigue vigente para el caso que realmente compromete la trazabilidad. Los duplicados criticos que si existen estan en `LISTADO JEFES` (2 pares) y entre hojas (3 discrepancias), y esos si bloquean.

## DEC-009 - Fuente De Verdad Del Padron Y Reconciliacion De Las Dos Hojas

Fecha: 2026-08-31

Contexto: El Excel tiene dos hojas con personas. `Copia de Jefes ML 2026. betty(1` trae 1113 personas con celular, CI, email y marcas de consagracion. `LISTADO JEFES` trae 146 personas, solo jefes y educadores, con una nomenclatura de circulo distinta. Habia que determinar si la segunda es redundante, complementaria o desactualizada.

Decision: La hoja `Copia de Jefes ML 2026. betty(1` es la **fuente de verdad** para personas, matrimonios, circulos y consagracion. `LISTADO JEFES` es **complementaria** y se usa exclusivamente para completar la jefatura: aporta el telefono de los 4 matrimonios educadores de POSTULANTES 2026 que en la hoja principal solo figuran como etiqueta en la fila separadora, el numero de orden de grupo y observaciones operativas de estado del circulo. `Hoja1` es una tabla dinamica y se excluye de la importacion.

La reconciliacion se hace por persona en cascada, nunca por circulo (41 etiquetas de circulo del listado no existen en la hoja principal y 58 de la principal no existen en el listado):

1. Nombre normalizado + celular normalizado: 110 de 146 filas.
2. Solo celular: 29 filas mas; se acepta y se registra `NOMBRE_DISCREPANTE_ENTRE_HOJAS` (BAJA).
3. Solo nombre, con celular distinto: 4 filas; **no se acepta automaticamente**, genera `CELULAR_DISCREPANTE_ENTRE_HOJAS` (CRITICA) y exige confirmacion humana.
4. Sin correspondencia: 3 filas, resolucion manual.

Consecuencias: 139 de 146 filas (95%) se reconcilian sin intervencion. Los 4 circulos POSTULANTES 2026 solo obtienen jefe habilitable si se ejecuta esta reconciliacion; sin ella quedan sin representante. Las 3 discrepancias de celular afectan a jefes, por lo que un numero equivocado deja un bloque completo sin poder votar: deben resolverse antes de abrir la votacion.

## DEC-010 - Solo Se Exige Jefe Donde Existe Bloque No Consagrado

Fecha: 2026-08-31

Contexto: 22 de los 93 circulos no tienen ningun integrante con la marca `Jefes`. Marcarlos a todos como incidencia critica producia falsos positivos: varios de esos circulos (`C° CONSAGRADOS`, `CIRCULO 33`, entre otros) estan integrados exclusivamente por matrimonios consagrados, que votan matrimonio por matrimonio y no necesitan representante.

Decision: La incidencia `CIRCULO_SIN_JEFE` se emite unicamente cuando el circulo tiene al menos un matrimonio no consagrado y ningun integrante marcado como jefe. Un circulo integramente consagrado sin jefe no es una incidencia.

Consecuencias: Las incidencias criticas por falta de jefe bajan de 22 a 11, y esas 11 si representan un voto de bloque que hoy no tendria quien lo emita. La generacion de unidades electorales `BLOQUE_NO_CONSAGRADO` se hace por circulo con bloque no consagrado (54 circulos), no por circulo existente (93).

## DEC-011 - Los Viudos Consagrados Conservan El Voto De Matrimonio

Fecha: 2026-08-31

Contexto: 29 de los 571 matrimonios tienen un solo integrante activo. De esos, 22 estan marcados como consagrados y quedaron viudos: el conyuge que sigue en el padron llevo el voto del matrimonio antes de enviudar, y la marca `Consagrados` del Excel se mantuvo sobre la persona sobreviviente (`PADRON_ANALISIS.md`, secciones 3.3 y 7, punto 1).

Decision: Un matrimonio de un solo integrante marcado como consagrado conserva su derecho a un voto de `MATRIMONIO_CONSAGRADO`, emitido por la persona sobreviviente. No se exige un segundo integrante activo para generar la unidad electoral.

Consecuencias: El total estimado de unidades `MATRIMONIO_CONSAGRADO` queda en 260 (238 de dos integrantes + 22 viudos), no en 238. El modelo de datos soporta esto de forma nativa: `matrimonios.integrante_2_id` es nullable (Mision 03), asi que un matrimonio viudo consagrado no requiere ningun tratamiento especial para generar su unidad electoral. Los 7 matrimonios restantes de un solo integrante que no estan marcados como consagrados siguen abiertos como incidencia `MATRIMONIO_INCOMPLETO` y no generan unidad electoral hasta que se resuelvan.

## DEC-012 - Bajas De Personas (No ML U Observacion): Pendiente De Negocio

Fecha: 2026-08-31

Contexto: 118 personas tienen la marca estructurada `No ML` y 33 tienen una observacion textual libre de baja (`salieron`, `fallecio`, `ya no siguen`, entre otras). Ambos grupos siguen contados hoy en los matrimonios consagrados y no consagrados del padron (`PADRON_ANALISIS.md`, seccion 5.2 y seccion 7, punto 2). Falta que el negocio defina si estas personas -y, por extension, los matrimonios o bloques que dependen de ellas- quedan excluidos del padron votante.

Decision: Pendiente. No se implementa ninguna exclusion automatica todavia.

Consecuencias: El modelo ya distingue los dos motivos de baja en `personas.estado` (`ACTIVA` / `BAJA_NO_ML` / `BAJA_OBSERVACION`, Mision 03) mas el detalle textual en `personas.observacion_baja`, de modo que cuando el negocio resuelva esta decision, aplicarla es un filtro sobre datos ya modelados y no requiere una migracion adicional ni volver a importar el padron.

## DEC-013 - Circulos De Postulantes: Pendiente De Negocio

Fecha: 2026-08-31

Contexto: 45 de los 93 circulos son de postulantes (matrimonios no consagrados en formacion). Falta que el negocio confirme si corresponde un voto de bloque `BLOQUE_NO_CONSAGRADO` por cada circulo de postulantes o si estos circulos no votan en esta eleccion (`PADRON_ANALISIS.md`, seccion 7, punto 3).

Decision: Pendiente. La Mision 03 no genera ni excluye unidades electorales para circulos de postulantes; eso es trabajo del importador (Mision 04) una vez resuelta esta decision.

Consecuencias: El modelo no necesita ningun campo ni migracion adicional para soportar cualquiera de los dos desenlaces: `unidades_electorales` ya admite crear o no crear una fila `BLOQUE_NO_CONSAGRADO` por circulo segun corresponda, controlado enteramente por la logica del importador de la Mision 04.

## DEC-014 - Doble Rol De Jefes Consagrados: Pendiente De Negocio

Fecha: 2026-08-31

Contexto: 43 de los 74 matrimonios jefe son ademas consagrados: la persona tiene, en principio, dos unidades electorales disponibles (su propio matrimonio consagrado y el bloque no consagrado que lidera). El requerimiento contempla el caso pero falta confirmar si en esta votacion la persona emite los dos votos o debe elegir uno (`PADRON_ANALISIS.md`, seccion 7, punto 5; `REGLAS_NEGOCIO.md`, seccion "Habilitacion Por Celular").

Decision: Pendiente. No se implementa restriccion alguna todavia; el motor de habilitacion (Mision 05) es quien debe aplicar la regla que el negocio confirme.

Consecuencias: El modelo ya separa el derecho a voto de la persona mediante `unidades_electorales` (DEC-003), por lo que ambos desenlaces -emitir dos votos o forzar una eleccion entre las dos unidades- se resuelven en la logica de habilitacion y registro de voto (Misiones 05 y 06) sin cambios al esquema de base de datos.

## DEC-015 - El Importador Rechaza Reimportar Si Ya Hay Una Votacion Abierta O Posterior

Fecha: 2026-08-31

Contexto: El importador de la Mision 04 puede correrse mas de una vez (para corregir datos del padron antes de una votacion real). Si ya existen votos emitidos, reemplazar personas/matrimonios/unidades electorales rompería la trazabilidad de esos votos y podria dejar votos huerfanos apuntando a una unidad electoral que ya no existe.

Decision: Antes de importar, el importador verifica si existe alguna `Votacion` con `estado` distinto de `BORRADOR` (es decir, `ABIERTA`, `CERRADA` o `RESULTADOS_REVELADOS`). Si existe, la corrida se rechaza por completo (`ImportacionRechazadaError`, HTTP 409 en el endpoint) sin tocar la base. Si no existe ninguna votacion mas alla de `BORRADOR` (incluido el caso de que todavia no exista ninguna votacion), el importador reemplaza por completo lo generado por la corrida anterior -personas, matrimonios, grupos, unidades electorales e incidencias- dentro de una unica transaccion, y vuelve a generarlo desde cero a partir del Excel. Cada corrida (exitosa o fallida) queda registrada como una fila en `importaciones_padron`, con su `resumen` o su `error`.

Consecuencias: El padron se puede corregir y reimportar tantas veces como haga falta mientras la votacion siga en preparacion, sin acumular duplicados ni dejar registros a medio borrar si la corrida falla a mitad de camino (el reemplazo y la generacion ocurren en la misma transaccion; si algo falla, se revierte todo y la importacion anterior sigue vigente). Una vez que una votacion se abre, el padron queda congelado: para corregirlo hace falta cerrar o descartar esa votacion primero. Esto responde al pendiente de la Mision 03 sobre que pasa si se reimporta el padron.

## DEC-016 - Unidades Electorales Con Decision De Negocio Pendiente Se Crean Igual, Con Un Estado Que Las Distingue

Fecha: 2026-08-31

Contexto: Al momento de implementar el importador (Mision 04), DEC-012 (bajas de personas), DEC-013 (circulos de postulantes) y DEC-014 (doble rol de jefes consagrados) seguian sin resolucion del negocio. Bloquear la importacion hasta tener esas tres respuestas hubiera dejado el padron entero sin poder cargarse. El requerimiento pide lo contrario: importar todo y generar las unidades electorales igual, marcandolas de forma que se puedan habilitar despues sin reimportar.

Decision: `unidades_electorales.estado` (columna libre desde la Mision 03) toma uno de cuatro valores segun esta prioridad, evaluada en orden:

1. `BLOQUEADA_POR_INCIDENCIA`: la unidad (el matrimonio, o algun matrimonio del bloque) tiene asociada al menos una incidencia de severidad CRITICA (por ejemplo `CONSAGRACION_INCONSISTENTE`, `CIRCULO_SIN_JEFE`, `CELULAR_DISCREPANTE_ENTRE_HOJAS`). Esta condicion tiene prioridad sobre las dos siguientes: un dato con integridad dudosa se congela primero, independientemente de si ademas es un circulo de postulantes o tiene bajas.
2. `PENDIENTE_DEFINICION_POSTULANTES`: solo aplica a `BLOQUE_NO_CONSAGRADO` cuyo circulo contiene la palabra "POSTULANTE" en su nombre (DEC-013). Un matrimonio consagrado que este dentro de un circulo de postulantes no queda pendiente por esta regla: solo el bloque del circulo lo esta.
3. `PENDIENTE_DEFINICION_BAJA`: todas las personas que componen la unidad (los integrantes del matrimonio, o todas las personas de los matrimonios no consagrados del bloque) estan en estado `BAJA_NO_ML` o `BAJA_OBSERVACION` (DEC-012). Si al menos una persona sigue `ACTIVA`, la unidad no se marca pendiente por este motivo.
4. `HABILITADA`: ninguna de las anteriores aplica.

El doble rol de jefes consagrados (DEC-014) no necesita un estado especial: el modelo ya permite que una persona tenga dos unidades electorales (su matrimonio y el bloque que lidera) sin relacion directa entre ambas filas, asi que cada una se evalua de forma independiente con las mismas cuatro reglas.

Consecuencias: Cuando el negocio resuelva DEC-012, DEC-013 o DEC-014, aplicar la decision es un `UPDATE` sobre `unidades_electorales.estado` (o sobre las incidencias que las bloquean), no una reimportacion del padron. El resumen de la importacion (`ImportacionPadron.resumen`) reporta `votos_maximos` contando unicamente las unidades en `HABILITADA`, para no sobreestimar cuantos votos puede recibir la votacion mientras estas decisiones sigan abiertas.

## DEC-017 - Un Matrimonio Sin Ningun Celular Valido No Puede Consultar Su Habilitacion

Fecha: 2026-08-31

Contexto: DEC-002 y DEC-005 tratan el celular como el canal de consulta de habilitacion, pero hasta la Mision 04 el importador solo generaba `CELULAR_FALTANTE` **por persona** (severidad ALTA, no bloqueante): un matrimonio donde un conyuge no tenia celular pero el otro si seguia quedando `HABILITADA`, correctamente, porque ese conyuge podia consultar por los dos. El dueño del padron aclaro por escrito, revisando el resultado de la Mision 04, que el caso que faltaba cubrir es distinto: si **ningun** integrante del matrimonio tiene un celular valido, no existe ningun numero por el cual esa unidad electoral pueda ser consultada, y el matrimonio queda de hecho inhabilitado para votar aunque el resto de sus datos (consagracion, CI, etc.) este correcto.

Decision: Se agrega `MATRIMONIO_SIN_CELULAR_DISPONIBLE` a `TipoIncidenciaPadron`, severidad CRITICA. El importador la genera por matrimonio (para cada integrante) cuando, usando el celular tal como viene en la hoja principal -sin aplicar todavia la reconciliacion con `LISTADO JEFES` de DEC-009-, ninguno de los uno o dos integrantes tiene un celular que normalice a un numero valido (se excluyen por igual el celular ausente, el placeholder `0` y los formatos no interpretables: los tres casos ya resuelven a `PersonaExcel.celular = None`). Al ser CRITICA, DEC-016 ya la deja `BLOQUEADA_POR_INCIDENCIA` sin necesidad de tocar la logica de precedencia de estados.

Se evaluo el caso analogo del lado del bloque: un `BLOQUE_NO_CONSAGRADO` cuyo jefe, **despues** de la reconciliacion de DEC-009 (que puede completar un celular faltante desde `LISTADO JEFES`), sigue sin ningun celular valido. Se corrio esa verificacion contra el Excel real sobre los 54 circulos con bloque no consagrado: en los 54, todo circulo con al menos un jefe resuelto (por la hoja principal o por `LISTADO JEFES`) termina con un celular valido en alguno de sus jefes. No aparecio ningun caso real, asi que **no** se agrega `BLOQUE_SIN_CELULAR_JEFE_DISPONIBLE` a la taxonomia: agregar una incidencia sin un solo caso que la ejercite en datos reales seria codigo especulativo, no una regla validada. Si una carga futura del padron produce ese caso, corresponde agregarlo entonces, con el mismo criterio con que se agrego cada tipo de incidencia existente (validado contra datos reales, nunca supuesto).

Consecuencias: Sobre el Excel real, 7 matrimonios (8 personas: seis matrimonios de un solo integrante y uno de dos) quedan con `MATRIMONIO_SIN_CELULAR_DISPONIBLE`; las unidades `MATRIMONIO_CONSAGRADO`/`BLOQUE_NO_CONSAGRADO` habilitadas bajan de 224 a 216 (tres de esos siete tambien tenian todos sus integrantes de baja y hubieran caido en `PENDIENTE_DEFINICION_BAJA`; con esta regla caen directamente en `BLOQUEADA_POR_INCIDENCIA`, que tiene prioridad segun DEC-016). El chequeo se hace con el celular crudo de la hoja principal, no con el resuelto por `LISTADO JEFES`: se verifico contra el Excel real que ningun matrimonio sin celular queda luego completado por la reconciliacion (los 7 matrimonios sin celular valido de la hoja principal no coinciden con ninguna de las filas que la cascada de DEC-009 resuelve), asi que el orden de estas dos comprobaciones no cambia el resultado hoy, pero si una carga futura lo hace, el criterio documentado aca (celular crudo de la hoja principal) es el que rige hasta que se decida lo contrario.

## DEC-018 - La Consulta De Habilitacion Resuelve Siempre Contra La Unica Votacion ABIERTA

Fecha: 2026-08-31

Contexto: La Mision 05 agrega `POST /api/v1/habilitaciones/consultar`, que necesita saber contra que `Votacion` evaluar si una unidad electoral ya tiene voto registrado. A diferencia de `POST /api/v1/votaciones/{id}/votos` (Mision 06), el requerimiento de esta consulta no trae `votacion_id` en la ruta: el operador solo tiene el celular. La Mision 07 (apertura/cierre de votacion) todavia no existe, asi que no hay endpoint que fije cual es "la" votacion vigente ni una regla escrita sobre cuantas pueden estar `ABIERTA` a la vez.

Decision: El endpoint no recibe `votacion_id`. Resuelve siempre contra la unica `Votacion` en estado `ABIERTA` (`app/services/habilitacion.py`, `_votacion_abierta`): se asume que existe como maximo una en ese estado al mismo tiempo. Si no existe ninguna, el servicio levanta `NoHayVotacionAbiertaError` y el endpoint responde `409 Conflict` con un detalle explicito -- nunca un `200` con una respuesta vacia ni una excepcion sin manejar. Para las pruebas de esta mision, la `Votacion` en estado `ABIERTA` se crea directo por ORM/fixture (`tests/test_habilitacion.py`, `_votacion_abierta`), sin depender de un endpoint de apertura que todavia no existe.

Consecuencias: Mientras no exista la Mision 07, "abrir una votacion" es un `INSERT`/`UPDATE` manual sobre `votaciones.estado`, y esta consulta ya sabe operar sobre ese estado. Si la Mision 07 llega a permitir mas de una `Votacion` `ABIERTA` en simultaneo (por ejemplo, para pruebas paralelas a la votacion real), esta decision debe revisarse: `_votacion_abierta` tendria que recibir un criterio de seleccion explicito en vez de asumir unicidad. Hasta entonces, dos filas `ABIERTA` a la vez es un estado invalido que el sistema no produce por si mismo (nada en el codigo actual permite abrir una segunda votacion) y que, si ocurriera por una carga manual incorrecta, esta consulta no intenta resolver en silencio: `Session.query(...).one_or_none()` levanta `MultipleResultsFound`, que llega como error 500 sin manejar especial -- una senal de bug, no un camino normal a cubrir con manejo dedicado todavia.

## DEC-019 - El Bloqueo Por Incidencia Critica De Una Unidad Electoral No Se Contagia A Otra Del Mismo Circulo

Fecha: 2026-08-31

Contexto: Al revisar la Mision 05 se detecto que `_crear_unidades_electorales` (Mision 04, DEC-016) calculaba `grupos_con_critica` como "cualquier circulo con al menos una incidencia CRITICA de cualquier persona, sobre cualquier tema", y usaba ese set tanto para decidir si un `MATRIMONIO_CONSAGRADO` quedaba `BLOQUEADA_POR_INCIDENCIA` (`matrimonio.grupo_id in grupos_con_critica`, ademas de la condicion correcta sobre sus propios integrantes) como para un `BLOQUE_NO_CONSAGRADO` (`grupo.id in grupos_con_critica`, sin ninguna otra condicion). Como casi toda incidencia de la hoja principal lleva el circulo de la persona afectada (`IncidenciaPadron.grupo_id` se resuelve por `circulo`, no solo por pertenencia real al problema), un matrimonio o bloque sin ningun problema propio quedaba bloqueado solo por compartir circulo con otro que si lo tenia. Verificado contra el Excel real: circulos como "CIRCULO 1 - LUQUE" (16 incidencias `CONSAGRACION_SIN_DEFINIR` de otros matrimonios bloqueaban 3-4 matrimonios consagrados bien cargados) o "GENERACION DEL CENTENARIO" (una incidencia de un matrimonio bloqueaba a los otros 3 del circulo) mostraban el patron con claridad. La Mision 05 (`app/services/habilitacion.py`) heredaba el mismo alcance incorrecto al explicarle al operador por que una unidad estaba bloqueada, mostrando incidencias que no eran la causa real.

Decision: El bloqueo por incidencia CRITICA se acota a lo que realmente compromete a cada unidad electoral, nunca a lo que le pasa a otra unidad del mismo circulo:

- `MATRIMONIO_CONSAGRADO`: se bloquea unicamente si hay una incidencia CRITICA con `persona_id` en alguno de sus propios integrantes (`integrantes_ids & personas_con_critica`). Se elimina por completo la condicion sobre `grupo_id`.
- `BLOQUE_NO_CONSAGRADO`: se bloquea unicamente si hay una incidencia CRITICA con `grupo_id` de ese circulo y, ademas, `persona_id IS NULL` (incidencias genuinamente de circulo, como `CIRCULO_SIN_JEFE` o `JEFE_SIN_PERSONA_EN_PADRON`, que no tienen una persona puntual) o `persona_id` de alguien marcado `es_jefe_grupo=True` en ese mismo circulo. Una incidencia sobre un matrimonio consagrado puntual del circulo, cuya persona no es jefe, no cuenta.

Implementado en `backend/app/services/padron/importador.py`: se elimina `_grupos_con_incidencia_critica` y se agrega `_personas_jefe_por_grupo` (mapa `grupo_id -> {persona_id}` de jefes) y `_grupos_con_incidencia_de_jefe_o_circulo` (aplica la regla de arriba para bloques). `backend/app/services/habilitacion.py` se corrige en el mismo sentido (`_incidencias_criticas_matrimonio` ya no filtra por `grupo_id`; `_incidencias_criticas_grupo` agrega el filtro de jefe/circulo consultando `Persona.es_jefe_grupo`), para que las incidencias que la Mision 05 muestra como motivo de un bloqueo sean exactamente las que ahora lo causan.

Consecuencias: Sobre el Excel real (mismos 690 incidencias, 72 de ellas CRITICA -- el fix no cambia que incidencias existen, solo a cuantas unidades bloqueaban), las unidades electorales `HABILITADA` suben de 216 a 265 (+49) y `BLOQUEADA_POR_INCIDENCIA` baja de 70 a 16 (-54). La diferencia entre +49 y -54 no se pierde: 3 unidades que dejaron de estar bloqueadas por una incidencia ajena caen en `PENDIENTE_DEFINICION_POSTULANTES` (22 -> 25) y 2 en `PENDIENTE_DEFINICION_BAJA` (6 -> 8), porque al dejar de aplicar la regla 1 de precedencia de DEC-016 (incidencia critica) pasan a evaluarse contra las reglas 2 y 3, que en esos casos si aplican. Votos maximos habilitables hoy: 249 `MATRIMONIO_CONSAGRADO` + 16 `BLOQUE_NO_CONSAGRADO` = 265 (subio de 216). Pruebas de regresion agregadas en `backend/tests/test_importador_padron.py` (`_construir_excel_fixture_alcance_incidencias`, dos matrimonios consagrados en un mismo circulo donde solo uno tiene una incidencia propia, y un circulo mixto donde el bloque no consagrado esta sano pese a que un matrimonio consagrado del mismo circulo esta bloqueado).

## DEC-020 - Registro De Voto: Doble Rol Sin Restriccion Adicional Y Sin Control De Acceso

Fecha: 2026-08-31

Contexto: La Mision 06 (`POST /api/v1/votaciones/{id}/votos`) registra el voto de una unidad electoral ya resuelta por la Mision 05. Dos preguntas quedaban abiertas al implementarla: que hacer con el doble rol de jefe consagrado (DEC-014, todavia pendiente de negocio) al momento de votar, y que control de acceso protege este endpoint.

Decision: Sobre DEC-014, esta mision no impone ninguna restriccion de "elegi una unidad": si la misma persona tiene disponibles su matrimonio consagrado y el bloque no consagrado que lidera, cada unidad se vota con una request independiente y genera su propia fila en `votos`, sin relacion entre ambas. Inventar una regla de eleccion excluyente ahora seria adelantarse a una decision que todavia no esta tomada; cuando el negocio resuelva DEC-014, aplicarla en `app/services/voto.py` (`_confirmar_persona_autorizada` o una nueva validacion previa) es un cambio acotado que no requiere revisar el modelo de datos.

Sobre control de acceso: `POST /api/v1/votaciones/{id}/votos` no implementa ninguno. Hoy, cualquiera que le pegue al endpoint con `votacion_id`, `unidad_electoral_id`, `opcion_id` y `emitido_por_persona_id` validos puede registrar un voto sin acreditar que es esa persona ni que opera desde un dispositivo autorizado. La Mision 07 menciona control de acceso administrativo para el panel de administracion, pero no cubre este endpoint de emision. Esto queda como pendiente explicito, no como omision accidental: es una de las zonas sensibles listadas en `AGENTS.md` ("trazabilidad de quien habilito o emitio cada voto").

Consecuencias: Los tests de la Mision 06 (`backend/tests/test_voto.py`, `test_jefe_consagrado_con_doble_rol_permite_dos_votos_independientes`) verifican dos votos exitosos e independientes para el mismo doble rol, sin bloqueo cruzado. Ninguna migracion adicional hace falta si el negocio termina exigiendo "elegi una": el UNIQUE existente es por `(votacion_id, unidad_electoral_id)`, no por persona, asi que ya impide que la misma unidad reciba dos votos; falta unicamente la regla de negocio que decida si una persona con dos unidades puede consumir ambas. Antes de una votacion real, este endpoint necesita algun mecanismo de autenticacion/autorizacion (token de dispositivo, sesion de operador, o similar) definido por el negocio; hasta entonces no debe exponerse en una red no confiable.

## DEC-021 - Control De Acceso Administrativo Inicial Via ADMIN_API_KEY

Fecha: 2026-08-31

Contexto: La Mision 07 agrega los primeros endpoints administrativos reales: crear una `Votacion` y sus `OpcionVoto`, abrirla, cerrarla y consultar su estado operativo. No existe todavia ningun sistema de usuarios, sesiones ni roles en el proyecto (eso no esta planificado hasta, como muy pronto, las Misiones 09-10 de frontend), pero estos endpoints ya no pueden quedar abiertos como `POST /api/v1/votaciones/{id}/votos` (DEC-020): a diferencia de ese endpoint operativo, estos permiten alterar el ciclo de vida completo de la votacion (crear, abrir, cerrar).

Decision: Se agrega `ADMIN_API_KEY` a `Settings` (`backend/app/core/config.py`) y `backend/.env.example`, y una dependencia de FastAPI `require_admin` (`backend/app/api/deps.py`) que compara el header `X-Admin-Token` contra ese valor. Si `ADMIN_API_KEY` esta vacio (no configurado), `require_admin` rechaza toda accion administrativa con `403` -- falla cerrado, nunca abierto, para que un despliegue sin la variable configurada no quede con el panel administrativo accesible a cualquiera. Con un token incorrecto o ausente responde `401`. Esto es explicitamente un mecanismo **inicial**, no un sistema de usuarios: no hay identidad, sesion, expiracion, ni distincion entre distintos administradores mas alla de que cada uno declare su propio nombre en el campo `usuario` del body de `abrir`/`cerrar` (texto libre, sin relacion con el token). Reemplazarlo por autenticacion real es trabajo futuro, fuera del alcance de esta mision.

Alcance exacto de lo que protege `require_admin` -- aplicado en `backend/app/api/v1/endpoints/votaciones.py` a nivel de router, a los seis endpoints administrativos: `POST /api/v1/votaciones`, `POST /api/v1/votaciones/{id}/opciones`, `GET /api/v1/votaciones/{id}/opciones`, `POST /api/v1/votaciones/{id}/abrir`, `POST /api/v1/votaciones/{id}/cerrar` y `GET /api/v1/votaciones/{id}/estado`. **No** se aplica a `POST /api/v1/habilitaciones/consultar` ni a `POST /api/v1/votaciones/{id}/votos`: esos dos son de uso operativo (por los que consultan o emiten un voto, no por administracion) y su falta de control de acceso ya quedo documentada como pendiente explicito en DEC-020 -- esta decision no la resuelve, a proposito, para no mezclar los dos problemas. `backend/tests/test_votacion_endpoint.py::test_votos_y_habilitaciones_consultar_siguen_sin_proteccion` confirma que conectar el router nuevo no los protegio por accidente.

Consecuencias: Antes de una votacion real, `ADMIN_API_KEY` debe configurarse con un valor no trivial y distribuirse solo a quien opera el panel administrativo; mientras no este configurado, la Mision 07 completa queda inutilizable (a proposito). Cuando el negocio defina un sistema de usuarios real, `require_admin` es el unico punto a reemplazar: los endpoints ya dependen de el via `Depends`, no de una verificacion propia repetida en cada uno. (Nota: el texto original de esta decision decia "cinco endpoints" pero listaba seis; corregido en la Mision 08 sin agregar una decision nueva, es un error de redaccion, no un cambio de alcance.)

## DEC-022 - Cerrada Habilita Consulta De Resultados; Revelar Es Un Hito Separado, Y No Se Cruza Grupo Por Opcion

Fecha: 2026-08-31

Contexto: La Mision 08 encontro una ambiguedad entre dos documentos. `REGLAS_NEGOCIO.md` ("Revelacion De Resultados") dice que los resultados "pueden revelarse si la votacion tiene estado `CERRADA`", lo cual sugiere una accion deliberada de "revelar" antes de poder verlos. El criterio de aceptacion de `MISIONES.md` para esta mision, en cambio, dice literalmente "con votacion cerrada, los resultados se muestran", sin mencionar ningun paso intermedio. Ademas, `Votacion.estado` ya tenia un cuarto valor, `RESULTADOS_REVELADOS`, y la columna `resultados_revelados_at`, ambos presentes desde la Mision 03 pero sin ningun endpoint que los usara.

Decision: Se toman dos decisiones relacionadas:

1. `GET /api/v1/votaciones/{id}/resultados` funciona con `estado` en `CERRADA` **o** `RESULTADOS_REVELADOS` -- no hace falta "revelar" primero para poder consultarlos administrativamente. Se agrega ademas `POST /api/v1/votaciones/{id}/revelar` (protegido por `require_admin`, mismo patron que abrir/cerrar de la Mision 07), valido unicamente desde `CERRADA` (409 si no), que setea `estado = RESULTADOS_REVELADOS` y `resultados_revelados_at = ahora`. Si la votacion ya esta en `RESULTADOS_REVELADOS`, un segundo `POST /revelar` da 409 explicito citando la fecha en la que ya se revelo, en vez de tratarlo como un caso mas de "no esta CERRADA". Hoy `revelar` no cambia lo que devuelve `/resultados` (ya funcionaba en `CERRADA`): es el hito formal que va a necesitar la Mision 10 (vista de resultados finales del panel administrativo) para distinguir "cerrada pero todavia no comunicada" de "ya anunciada".
2. `GET /resultados` desglosa por opcion, por tipo de unidad electoral (`MATRIMONIO_CONSAGRADO` / `BLOQUE_NO_CONSAGRADO`) y por grupo (circulo), pero **no** cruza grupo por opcion. Muchos circulos tienen una sola unidad electoral (un matrimonio, o un bloque representado por un jefe), asi que un desglose "circulo x opcion" equivaldria a revelar el voto individual de esa unidad. El sistema no es anonimo a nivel de auditoria (`AGENTS.md` pide trazabilidad de quien voto, DEC-020), pero ningun requerimiento pide ademas desglosar la eleccion por circulo, asi que no se agrega sin que se pida explicitamente.

Todos los conteos (`totales_por_opcion`, `totales_por_tipo_unidad`, `totales_por_grupo`) se calculan siempre a partir de las filas de `Voto` de esa votacion -- nunca de `UnidadElectoral.estado`, que sirve para elegibilidad, no para resultados. El "total general" (`total_votos`) es trivialmente verificable: coincide con la suma de `totales_por_opcion` y con la suma de `totales_por_tipo_unidad`, porque cada `Voto` tiene exactamente una opcion y su unidad electoral tiene exactamente un tipo.

`GET /resultados` esta protegido por `require_admin` (lo consume el panel administrativo, Mision 10): a diferencia de `POST /votaciones/{id}/votos` y `POST /habilitaciones/consultar` (DEC-020), este endpoint expone resultados por opcion, y `REGLAS_NEGOCIO.md` prohibe que el frontend de votacion (Mision 09) los muestre.

Exportacion: se agrega `?formato=csv` sobre el mismo `GET /resultados` (en vez de un endpoint aparte) porque la logica de calculo es identica y solo cambia la serializacion de salida; es una funcion de formateo separada en el endpoint (`_resultados_a_csv`), no en el servicio, para no mezclar calculo de resultados con presentacion.

Consecuencias: `backend/app/services/votacion.py` gana `revelar_resultados` y `obtener_resultados`, con las excepciones `VotacionNoCerradaError`, `ResultadosYaReveladosError` y `ResultadosBloqueadosError`. Ningun modelo ni migracion nueva hace falta: `RESULTADOS_REVELADOS` y `resultados_revelados_at` ya existian desde la Mision 03 sin usarse. Pruebas en `backend/tests/test_resultados.py` (servicio) y `backend/tests/test_resultados_endpoint.py` (HTTP, incluida la proteccion `require_admin` de los dos endpoints nuevos y que `/votos` y `/habilitaciones/consultar` siguen sin ella).

## DEC-023 - Papeleta Publica: `GET /votaciones/abierta`, Sin `require_admin`

Fecha: 2026-09-01

Contexto: La Mision 09 (frontend de votacion) necesita saber contra que votacion y opciones puede votar el usuario, pero `GET /votaciones/{id}/opciones` (Mision 07) esta protegido por `require_admin` (DEC-021) -- correcto para el panel administrativo, pero el votante no tiene ese token. Es el mismo criterio que DEC-020 ya aplico a `POST /habilitaciones/consultar` y `POST /votaciones/{id}/votos`, aplicado ahora a un dato nuevo: la papeleta.

Decision: Se agrega `GET /api/v1/votaciones/abierta`, publico (sin `require_admin`), que devuelve `{votacion_id, nombre, opciones: [{id, nombre, orden}]}` de la unica `Votacion` en estado ABIERTA, o 404 si no hay ninguna. El nombre de las opciones no es un resultado -no revela ningun conteo- asi que exponerlo antes del cierre no viola `REGLAS_NEGOCIO.md`. La busqueda de "la unica votacion ABIERTA" (antes `_votacion_abierta` en `app/services/habilitacion.py`, DEC-018) se factoriza a `obtener_votacion_abierta` en `app/services/votacion.py`, reusada tanto por `habilitacion.py` como por este endpoint nuevo, en vez de escribirla una tercera vez.

Consecuencias: `app/services/habilitacion.py` re-exporta `NoHayVotacionAbiertaError` desde `app/services/votacion.py` para no romper el codigo y los tests que ya lo importaban desde ahi. `backend/app/api/v1/endpoints/votaciones.py` gana un segundo router (`public_router`) sin la dependencia `require_admin` a nivel de router, registrado junto al administrativo en `app/api/v1/api.py`. Pruebas en `backend/tests/test_votacion_abierta_endpoint.py`: papeleta con opciones, 404 sin votacion abierta, y que la respuesta no trae ningun campo mas alla de `votacion_id`/`nombre`/`opciones`.

## DEC-024 - El Frontend De Votacion Distingue Los Tres 409 De `POST /votos` Por El Texto De `detail`

Fecha: 2026-09-01

Contexto: Revision post-commit de la Mision 09. `POST /votaciones/{id}/votos` (`backend/app/services/voto.py`, Mision 06) devuelve `409` para tres errores con significado muy distinto: `VotoDuplicadoError` (la unidad ya tiene un voto registrado -- el caso real de "ya votado"), `VotacionNoDisponibleError` (la votacion se cerro en la ventana entre que el usuario cargo la papeleta con `GET /votaciones/abierta` y confirmo su eleccion) y `UnidadElectoralNoDisponibleError` (la unidad quedo bloqueada por una incidencia nueva en ese mismo lapso). `frontend/src/components/PapeletaVoto.tsx` (`handleConfirmar`) trataba cualquier `status === 409` como duplicado y disparaba `onYaVotado()`, mostrando "tu voto ya fue registrado" tambien en los otros dos casos -- donde el voto **nunca** se registro. Como la trazabilidad de quien voto es una zona sensible del proyecto (`AGENTS.md`), afirmarle a alguien que su voto quedo registrado cuando en realidad fallo es peor que un error generico: puede hacer que esa persona nunca vuelva a intentar votar.

Decision: No tocar el backend -- ya manda suficiente informacion en `detail` para diferenciar los tres casos sin ambigüedad, porque cada excepcion arma un mensaje con texto distinto (`voto.py`, lineas 41, 66, 136/172). `PapeletaVoto.tsx` agrega `clasificarConflicto(err)`, que solo actua sobre un `ApiError` con `status === 409` y clasifica por substring de `detail.toLowerCase()`: `"ya existe un voto"` -> `duplicado` (unico caso que llama a `onYaVotado()`), `"no existe o no esta en estado abierta"` -> `votacion-no-disponible`, `"no esta disponible para votar"` -> `unidad-no-disponible`. Los dos ultimos casos, y cualquier `409` que no matchee ninguno de los tres (`desconocido`, defensivo), muestran un `votoError` que invita a reintentar ("La votación ya no está disponible. Volvé a intentarlo." / "Esta unidad electoral ya no está disponible para votar. Volvé a intentarlo.") y nunca afirman que el voto se registro.

Consecuencias: `frontend/src/components/PapeletaVoto.test.tsx` gana dos pruebas (`test_...votacion...NO dispara 'ya votado'`, `test_...unidad...NO dispara 'ya votado'`) que verifican explicitamente que esos dos 409 no llaman a `onYaVotado` y si muestran un mensaje distinto al de duplicado. La clasificacion depende del texto exacto de `detail` que arma `backend/app/services/voto.py`: si ese texto cambia sin actualizar `clasificarConflicto`, el caso vuelve a caer en `desconocido` (mensaje generico, nunca en `duplicado` por accidente, porque el substring de duplicado es el mas especifico y no es prefijo de los otros dos) -- no hay forma de que este cambio futuro reintroduzca el bug original de "todo 409 es duplicado", pero si conviene revisar esta decision si `voto.py` cambia su redaccion.
