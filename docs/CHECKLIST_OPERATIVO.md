# Checklist Operativo

Lista de verificacion para quien opera el sistema en una votacion real. Cubre
lo que hace falta revisar antes de abrir, durante la votacion y en el cierre.
No repite el detalle de cada paso -- eso esta en `GUIA_OPERACION_VOTACION.md`
-- ni el procedimiento de backup completo, que esta en `PLAN_BACKUP.md`.

## Antes De Abrir La Votacion

Configuracion del backend real (no del entorno local de desarrollo):

- [ ] `DATABASE_URL` apunta a la base PostgreSQL real de produccion, no a un
      SQLite local ni a una base de pruebas.
- [ ] `ADMIN_API_KEY` esta configurado con un valor no trivial (no vacio, no
      el placeholder de `.env.example`). Sin esto, `require_admin` rechaza
      *todo* el panel administrativo con `403` (DEC-021) -- es la primera
      cosa a revisar si el panel no responde.
- [ ] `RATE_LIMIT_POR_MINUTO` esta configurado (default 20/minuto si se deja
      sin definir) sobre `POST /habilitaciones/consultar` y
      `POST /votaciones/{id}/votos` (DEC-029). Confirmar que responde `429`
      al superarlo (ver `GUIA_OPERACION_VOTACION.md`, seccion de monitoreo).
- [ ] `CORS_ORIGINS` incluye los dominios reales de `frontend/` y
      `frontend-admin/` en produccion -- no solo `localhost`.
- [ ] El dominio publico sirve por HTTPS (los celulares consultados y los
      votos no deben viajar en texto plano).
- [ ] Migraciones aplicadas contra la base real: `alembic upgrade head`
      corrido y sin errores (`backend/README.md`, seccion "Base De Datos Y
      Migraciones").

Padron:

- [ ] La ultima importacion (`GET /api/v1/padron/importaciones`, o la pagina
      de Importaciones del panel) es la que corresponde a esta votacion:
      revisar la fecha, el `usuario` que la corrio y que
      `estado == COMPLETADA`.
- [ ] El resumen de esa importacion (`resumen` en la respuesta, o la vista
      del panel) coincide con lo esperado: sobre el padron actual, 314
      unidades electorales, 265 `HABILITADA` (votos maximos), 16
      `BLOQUEADA_POR_INCIDENCIA`, 8 `PENDIENTE_DEFINICION_BAJA` (DEC-027) y
      25 `PENDIENTE_DEFINICION_POSTULANTES` (DEC-028). Si estos numeros
      cambiaron respecto de la ultima corrida documentada, investigar por
      que antes de abrir -- puede significar que el Excel cambio.
- [ ] Las incidencias `CRITICA` sin resolver (`GET /padron/incidencias?severidad=CRITICA&resuelta=false`,
      o la pagina de Incidencias) fueron revisadas por una persona, aunque
      ya esten bloqueando su unidad automaticamente -- "resolver" es solo
      trazabilidad (DEC-025), no cambia la habilitacion.
- [ ] Si el Excel del padron cambio desde la ultima importacion, se
      reimporto **antes** de abrir la votacion: una vez `ABIERTA`, el
      importador rechaza cualquier corrida nueva (DEC-015) hasta que esa
      votacion se cierre.

Votacion:

- [ ] La `Votacion` a abrir existe en `BORRADOR` con al menos una
      `OpcionVoto` cargada (`abrir_votacion` rechaza sin opciones,
      `VotacionSinOpcionesError`).
- [ ] No hay otra `Votacion` en estado `ABIERTA` al mismo tiempo (reforzado
      en base por `uq_votacion_estado_abierta`, pero confirmar en el
      dashboard antes de intentar abrir para no toparse con el 409).
- [ ] Los dos frontends (`frontend/` para votantes, `frontend-admin/` para
      el panel) apuntan al backend real via `VITE_API_BASE_URL` de
      produccion, no a `localhost`.

Backup:

- [ ] Se tomo un backup manual justo antes de abrir, ademas de cualquier
      backup automatico que ya exista (`PLAN_BACKUP.md`).

## Durante La Votacion (Puede Durar Dias O Semanas)

- [ ] Revisar periodicamente `GET /votaciones/{id}/estado` (o la pagina de
      detalle del panel): unidades habilitadas, votos emitidos, pendientes.
      Nunca expone nada agrupado por opcion mientras la votacion sigue
      `ABIERTA` (DEC-022).
- [ ] Revisar si aparecen incidencias nuevas (por ejemplo, si se corrigio
      algo del padron manualmente en la base -- fuera de flujo normal, pero
      posible) y marcarlas como revisadas cuando corresponda.
- [ ] Verificar de tanto en tanto que el rate limiting sigue activo (una
      request de mas al limite configurado deberia devolver `429`, no
      colgarse ni caer en `500`).
- [ ] No consultar `GET /votaciones/{id}/resultados` ni `POST /revelar`
      mientras la votacion sigue abierta -- estan protegidos por
      `require_admin` y devuelven `409` en `BORRADOR`/`ABIERTA` (DEC-022),
      pero igual no corresponde intentarlo antes del cierre planificado.

## Cierre

- [ ] Confirmar con quien tiene la autoridad de negocio que corresponde
      cerrar antes de ejecutar `POST /votaciones/{id}/cerrar` -- el cierre
      es el limite formal que habilita `GET /resultados` (DEC-022) y no es
      reversible desde la API (no existe un "reabrir").
- [ ] Backup inmediatamente despues del cierre, antes de revelar
      (`PLAN_BACKUP.md`).
- [ ] Verificar el estado operativo final: votos emitidos vs. unidades
      habilitadas, para detectar participacion anormalmente baja o alta
      antes de comunicar nada.

## Revelar Resultados

- [ ] `POST /votaciones/{id}/revelar` solo despues de que quien tiene la
      autoridad de negocio confirme que corresponde comunicar el resultado
      -- es un hito deliberado y separado del cierre (DEC-022), y un
      segundo `POST /revelar` da `409` explicito.
- [ ] Exportar el CSV (`GET /resultados?formato=csv`) para archivo, ademas
      de lo que se muestre en el panel.
