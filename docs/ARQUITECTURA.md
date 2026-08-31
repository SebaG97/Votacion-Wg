# Arquitectura Inicial

## Vista General

El sistema se divide en dos aplicaciones principales:

- `backend`: API, reglas de habilitacion, importacion del padron, auditoria y persistencia.
- `frontend`: interfaz de consulta, emision de voto, administracion y resultados.

## Backend

Responsabilidades:

- Importar y normalizar el Excel del padron.
- Detectar inconsistencias antes de abrir una votacion.
- Resolver habilitaciones a partir del celular.
- Registrar votos con idempotencia por unidad electoral.
- Bloquear resultados hasta el cierre.
- Exponer reportes operativos y resultados finales.

## Frontend

Responsabilidades:

- Pantalla de consulta por celular.
- Seleccion clara de rol cuando una persona puede votar por mas de una unidad electoral.
- Flujo de voto simple y verificable.
- Panel administrativo para padron, incidencias, estado de votacion y resultados.

## API Inicial

Rutas candidatas:

- `POST /api/v1/padron/importaciones`
- `GET /api/v1/padron/incidencias`
- `POST /api/v1/habilitaciones/consultar`
- `POST /api/v1/votaciones/{id}/votos`
- `POST /api/v1/votaciones/{id}/abrir`
- `POST /api/v1/votaciones/{id}/cerrar`
- `GET /api/v1/votaciones/{id}/estado`
- `GET /api/v1/votaciones/{id}/resultados`

## Seguridad Y Auditoria

- No exponer resultados si la votacion no esta cerrada.
- Registrar usuario administrativo en acciones sensibles.
- Registrar fecha y hora de cada voto.
- Evitar guardar informacion innecesaria en logs.
- Validar duplicados de celular antes de habilitar votos.
