# Frontend Administrativo

Panel administrativo del sistema VOTACION WG (Mision 10). Proyecto separado de `frontend/` (Mision 09, votante): no comparte codigo ni build.

## Stack

- React
- TypeScript
- Vite
- React Router
- Cliente HTTP tipado contra `VITE_API_BASE_URL`, con header `X-Admin-Token` en cada request

## Pantallas

- Login: pega el `ADMIN_API_KEY` (guardado en `sessionStorage`, nunca `localStorage` ni hardcodeado) y lo valida contra la API.
- Dashboard: lista de votaciones (`GET /votaciones`).
- Detalle de votacion: estado operativo, resumen de la ultima importacion, opciones (BORRADOR), abrir/cerrar, y resultados finales solo con la votacion CERRADA o RESULTADOS_REVELADOS.
- Incidencias: listado filtrable por severidad/tipo/resuelta, con "marcar como revisada" (trazabilidad, no rehabilita nada).
- Importaciones: historial mas una nueva importacion con confirmacion explicita antes de ejecutarla.

## Principios

- Nunca un desglose por opcion/candidato antes del cierre formal de la votacion (`REGLAS_NEGOCIO.md`).
- Un `401`/`403` real de cualquier endpoint administrativo vuelve al login y limpia el token guardado.
- Ninguna operacion que reescriba datos (reimportar el padron) se dispara con un solo click.

## Instalacion Local

```powershell
cd frontend-admin
npm install
```

## Ejecutar

```powershell
cd frontend-admin
npm run dev
```

Por defecto Vite levanta en `http://localhost:5174` (distinto del `5173` de `frontend/`, para poder correr los dos a la vez contra el mismo backend). Agregar `http://localhost:5174` a `CORS_ORIGINS` del backend si no esta ya.

## Validacion

```powershell
cd frontend-admin
npm run build
```

## Tests

```powershell
cd frontend-admin
npm test
```

`vitest` + `@testing-library/react`, mockeando la capa de API (`vi.mock`). Incluye `src/test/no-resultados-prematuros.test.tsx`: verifica en tiempo de ejecucion que `GET /resultados` y `POST /revelar` nunca se llaman mientras la votacion no esta CERRADA o RESULTADOS_REVELADOS.
