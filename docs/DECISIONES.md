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
