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
