# Frontend

Interfaz del sistema VOTACION WG.

## Stack

- React
- TypeScript
- Vite
- React Router
- Cliente HTTP tipado contra `VITE_API_BASE_URL`

## Pantallas

Implementadas (Mision 09, `/`):

- Consulta por celular.
- Resultado de la consulta / seleccion de unidad electoral (incluido el doble rol de jefe consagrado, mostrado como dos opciones separadas).
- Confirmacion de persona cuando el celular es compartido entre conyuges (DEC-008).
- Emision de voto (papeleta de la votacion abierta).
- Confirmacion de voto registrado, sin ningun camino para reenviar el mismo voto.

Pendientes (Mision 10, panel administrativo):

- Panel administrativo.
- Incidencias del padron.
- Estado de votacion.
- Resultados finales.

## Principios De UX

- El flujo de votacion debe ser simple y sin distracciones.
- Si una persona tiene mas de un rol, el sistema debe mostrar opciones separadas.
- Los errores de padron deben explicarse sin exponer datos innecesarios.
- Los resultados no deben aparecer antes del cierre.

## Instalacion Local

```powershell
cd frontend
npm install
```

## Ejecutar Frontend

```powershell
cd frontend
npm run dev
```

Por defecto Vite levanta en:

```text
http://localhost:5173
```

La aplicacion consulta:

```text
VITE_API_BASE_URL=http://localhost:8000/api/v1
GET /health
```

## Validacion

```powershell
cd frontend
npm run build
```

## Tests

```powershell
cd frontend
npm test
```

`vitest` + `@testing-library/react`, mockeando la capa de API (`vi.mock`): no depende del backend real corriendo.
