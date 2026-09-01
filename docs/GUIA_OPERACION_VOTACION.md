# Guia De Apertura, Monitoreo, Cierre Y Resultados

Guia paso a paso para operar una votacion real de punta a punta con el panel
administrativo (`frontend-admin/`, Mision 10) y, como referencia, el llamado
HTTP equivalente de cada paso contra el backend real. Antes de arrancar,
completar `docs/CHECKLIST_OPERATIVO.md`.

Todos los endpoints administrativos requieren el header `X-Admin-Token` con
el valor de `ADMIN_API_KEY` (DEC-021); el panel lo pide una sola vez en
`/login` y lo guarda en `sessionStorage` del navegador (se pierde al cerrar
la pestana, a proposito).

## 0. Importar El Padron (Si Hace Falta)

Solo si el Excel cambio desde la ultima importacion, o si es la primera vez.
Rechaza la corrida si ya hay una votacion `ABIERTA` o `CERRADA` (DEC-015):
hacer esto **antes** de crear/abrir la votacion.

- Panel: pagina **Importaciones** -> "Nueva importacion" -> confirmar (pide
  confirmacion explicita antes de ejecutar, es una operacion pesada).
- HTTP: `POST /api/v1/padron/importaciones` con header `X-Admin-Token`, body
  `{"usuario": "nombre del operador"}`.
- Verificar el resumen devuelto contra los numeros esperados (ver
  `CHECKLIST_OPERATIVO.md`): 265 `HABILITADA`, 16 `BLOQUEADA_POR_INCIDENCIA`,
  8 `PENDIENTE_DEFINICION_BAJA`, 25 `PENDIENTE_DEFINICION_POSTULANTES`.

## 1. Crear La Votacion Y Sus Opciones

- Panel: **Dashboard** -> "Nueva votacion" -> nombre -> cargar cada opcion
  (nombre y, opcionalmente, orden).
- HTTP:
  - `POST /api/v1/votaciones` `{"nombre": "..."}` -> devuelve `id` en
    `BORRADOR`.
  - `POST /api/v1/votaciones/{id}/opciones` `{"nombre": "...", "orden": N}`
    una vez por opcion.
- La votacion queda en `BORRADOR`: no acepta votos todavia, y el padron
  sigue pudiendo reimportarse mientras siga en este estado.

## 2. Apertura

- Panel: pagina de detalle de la votacion -> "Abrir" -> confirmar usuario
  (texto libre, queda registrado en `abierta_por`).
- HTTP: `POST /api/v1/votaciones/{id}/abrir` `{"usuario": "..."}`.
- Falla con `409` si: la votacion no esta en `BORRADOR`, no tiene ninguna
  opcion cargada, o ya existe otra `Votacion` `ABIERTA` (reforzado en base
  por un indice unico parcial, no solo en el servicio).
- Desde este momento, `GET /api/v1/votaciones/abierta` (publico, sin token)
  empieza a devolver la papeleta, y el frontend de votantes (`frontend/`)
  puede recibir consultas y votos reales. **A partir de aca, el padron ya no
  se puede reimportar** hasta cerrar esta votacion (DEC-015).
- Verificar de inmediato: entrar a `frontend/` (el sitio publico) y
  confirmar que la papeleta carga con las opciones correctas.

## 3. Monitoreo (Mientras Esta Abierta, Dias O Semanas)

Lo unico permitido ver mientras esta `ABIERTA` es participacion agregada,
nunca nada por opcion (DEC-022):

- Panel: pagina de detalle de la votacion muestra el estado operativo
  (`GET /votaciones/{id}/estado`): unidades `HABILITADA`,
  `BLOQUEADA_POR_INCIDENCIA`, `PENDIENTE_DEFINICION_BAJA`,
  `PENDIENTE_DEFINICION_POSTULANTES`, votos emitidos y pendientes.
- Panel: pagina de **Incidencias**, filtrable por severidad/tipo/resuelta,
  para revisar si aparece algo nuevo y marcarlo como revisado (esto es solo
  trazabilidad administrativa, no cambia ninguna habilitacion -- DEC-025).
- Rate limiting activo (DEC-029): si alguien reporta que no puede consultar
  o votar, antes de asumir un bug revisar si esta recibiendo `429` -- el
  limite default es de `RATE_LIMIT_POR_MINUTO` (20) requests por minuto por
  IP a `POST /habilitaciones/consultar` y `POST /votaciones/{id}/votos`. Un
  votante real haciendo una consulta ocasional no deberia notarlo nunca.
- Backups periodicos segun `PLAN_BACKUP.md` durante toda la ventana abierta.
- No hay ningun endpoint ni pantalla que muestre resultados por opcion en
  este estado -- `GET /resultados` y `POST /revelar` devuelven `409` si se
  intentan (`ResultadosBloqueadosError`), y el panel ni siquiera monta
  `ResultadosView` mientras el estado no es `CERRADA`/`RESULTADOS_REVELADOS`.

## 4. Cierre

- Confirmar primero con quien tiene la autoridad de negocio (ver
  `CHECKLIST_OPERATIVO.md`) -- no hay forma de reabrir desde la API.
- Panel: pagina de detalle -> "Cerrar" -> confirmar usuario (queda en
  `cerrada_por`).
- HTTP: `POST /api/v1/votaciones/{id}/cerrar` `{"usuario": "..."}`. `409` si
  no estaba `ABIERTA`.
- Backup inmediato despues del cierre (`PLAN_BACKUP.md`).
- A partir de este momento `GET /resultados` ya responde (no hace falta
  revelar primero para consultarlo administrativamente, DEC-022), pero
  sigue protegido por `require_admin`: el frontend de votantes nunca lo
  llama (verificado por `frontend/src/test/no-resultados.test.ts`).

## 5. Revelar Resultados

- Panel: pagina de detalle, seccion de resultados -> "Revelar" (solo
  disponible con la votacion `CERRADA`).
- HTTP: `POST /api/v1/votaciones/{id}/revelar`. `409` si no esta `CERRADA`,
  o si ya se revelo antes (cita la fecha de la revelacion anterior).
- Es un hito deliberado y separado del cierre (DEC-022): sirve para
  distinguir "cerrada pero todavia no comunicada" de "ya anunciada".
- Exportar el CSV para archivo: `GET /votaciones/{id}/resultados?formato=csv`
  (mismo header `X-Admin-Token`).
- Los tres desgloses (`totales_por_opcion`, `totales_por_tipo_unidad`,
  `totales_por_grupo`) suman siempre el mismo `total_votos` -- si al mirar
  el CSV o el panel algo no cuadra, es una senal de bug, no una
  particularidad esperada del calculo.

## Referencia Rapida De Estados De `Votacion`

```
BORRADOR -> ABIERTA -> CERRADA -> RESULTADOS_REVELADOS
```

Cada flecha es una accion administrativa explicita (crear ya deja en
BORRADOR; abrir, cerrar y revelar son los tres pasos de arriba). No hay
transicion hacia atras expuesta por la API.
