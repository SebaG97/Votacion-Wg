# Frontend

Interfaz del sistema VOTACION WG.

## Stack

- React
- TypeScript
- Vite
- React Router
- Cliente HTTP tipado contra `VITE_API_BASE_URL`

## Pantallas Iniciales

- Consulta por celular.
- Seleccion de unidad electoral cuando aplique.
- Emision de voto.
- Confirmacion de voto registrado.
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
