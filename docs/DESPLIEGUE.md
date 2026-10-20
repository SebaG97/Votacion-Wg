# Despliegue En DigitalOcean App Platform

Este documento es la Parte A de la Mision 14: deja el repositorio listo para
desplegarse. La Parte B -- crear la app en el dashboard de DigitalOcean, dar
de alta los tres componentes, conectar la base de datos administrada, cargar
los secretos y disparar el primer despliegue -- la hace Sebad a mano
siguiendo la checklist de abajo; no es parte de esta mision ni se puede
automatizar desde el repositorio.

## Configuracion Real En Produccion (2026-10-20, DEC-037)

Lo que quedo andando en la Parte B, que manda sobre lo planificado mas abajo
donde difieren:

- Una sola app: `https://votacion-app-bildv.ondigitalocean.app`, con la base
  `segir-db-1` adjunta.
- Rutas (Settings -> cada componente -> HTTP Request Routes):
  - `/api` -> backend, **Preserve Full Path**.
  - `/` -> `frontend`, Trim Prefix.
  - `/admin` -> `frontend-admin`, Trim Prefix.
- Run Command del backend (sin Pre-Deploy Job):
  `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- `VITE_API_BASE_URL=/api/v1` (relativa, Build Time) en los dos frontends.
- `CORS_ORIGINS=https://votacion-app-bildv.ondigitalocean.app` (todo es mismo
  origen, no hace falta mas).
- `DATABASE_URL` con prefijo `postgresql+psycopg://` y `?sslmode=require`.
- Catchall document `index.html` en los dos Static Site (Settings ->
  componente -> Custom Pages).
- `frontend-admin` se construye con `base: "/admin/"` (`vite.config.ts`).

La app tiene tres componentes dentro de un mismo proyecto de App Platform:

| Componente       | Tipo        | Carpeta           |
| ----------------- | ----------- | ------------------ |
| Backend            | Web Service | `backend/`          |
| `frontend`          | Static Site | `frontend/`          |
| `frontend-admin`    | Static Site | `frontend-admin/`    |

La base de datos administrada de PostgreSQL ya existe y ya esta en uso; esta
mision no la crea ni la toca. `DATABASE_URL` (ver Requerimiento del
Backend abajo) es lo que conecta el Web Service a esa base.

## Backend (Web Service)

### Build Command

App Platform detecta Python y corre `pip install -r requirements.txt`
automaticamente. No hace falta un Build Command custom.

### Run Command

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Puntos clave:

- Sin `--reload`: esa flag es solo para desarrollo local (recarga en cada
  cambio de archivo, mas lenta y no pensada para produccion). El comando de
  desarrollo (`backend/README.md`) usa `--host 127.0.0.1 --port 8000` fijo;
  produccion usa `--host 0.0.0.0` (escucha en todas las interfaces, no solo
  loopback) y `$PORT`, la variable que App Platform inyecta con el puerto
  real asignado al contenedor -- nunca asumir el 8000 fijo de desarrollo.
- Directorio de trabajo: la raiz del componente Backend debe estar apuntando
  a `backend/` (Source Directory en el dashboard), para que `app.main:app`
  resuelva igual que en local.

### Pre-Deploy Job

```text
alembic upgrade head
```

Se configura como "Pre-Deploy Job" del componente Web Service, no como parte
del Run Command. App Platform corre este comando antes de cada despliegue
nuevo y solo deja pasar trafico a la version nueva si el job termina en
exito -- asi el esquema de la base queda al dia antes de que el codigo nuevo
reciba una sola request. Mismo Source Directory que el Run Command
(`backend/`), para que `alembic.ini` y `alembic/` se encuentren igual que en
local (`backend/README.md`, seccion "Base De Datos Y Migraciones").

### Variables De Entorno

Checklist para cargar en el dashboard, componente Backend. Todas estan hoy
documentadas con valores de ejemplo en `backend/.env.example`; el valor real
de produccion es el que aparece en la columna "Valor en produccion".

| Variable                 | Valor en produccion                                                                 | Notas |
| ------------------------- | ------------------------------------------------------------------------------------ | ----- |
| `DATABASE_URL`             | Connection string de la base administrada de DigitalOcean (formato `postgresql+psycopg://...`) | La toma directamente de la base ya conectada; App Platform puede inyectarla automaticamente si la base esta vinculada como recurso del componente. |
| `SECRET_KEY`               | Un valor unico y secreto generado para produccion, distinto del `change-me` de `.env.example` | |
| `ADMIN_API_KEY`            | Token administrativo unico de produccion                                              | Protege todos los endpoints admin (`require_admin`). |
| `ADMIN_USERNAME`           | Usuario del login admin de produccion                                                 | Usado por `POST /api/v1/auth/login` (Mision 12). |
| `ADMIN_PASSWORD`           | Contraseña del login admin de produccion                                              | Idem. Si falta junto con `ADMIN_API_KEY`, el login falla cerrado (403). |
| `CORS_ORIGINS`             | URLs reales de produccion de `frontend/` y `frontend-admin/`, separadas por coma       | **No** dejar los `localhost` de `.env.example`. Ejemplo de forma: `https://frontend-real.ondigitalocean.app,https://frontend-admin-real.ondigitalocean.app`. Completar con las URLs que DigitalOcean asigna a cada Static Site (o el dominio propio si se configura uno). |
| `RATE_LIMIT_POR_MINUTO`    | `20` (o el valor que Sebad decida para produccion)                                    | Limite general por IP (`slowapi`, Mision 11). |
| `APP_NAME`                 | `VOTACION WG API` (opcional, tiene default)                                           | |
| `APP_ENV`                  | `production` (opcional, tiene default `local`)                                        | Informativo; no cambia comportamiento del backend hoy. |
| `API_V1_PREFIX`             | `/api/v1` (opcional, tiene default)                                                   | Dejar el default salvo que haya una razon para cambiarlo. |

`RATE_LIMIT_LOGIN` (5/minute, Mision 12) esta fijo en el codigo, no es una
variable de entorno -- no hace falta cargarla.

## `frontend/` (Static Site)

### Build Command

```text
npm run build
```

Equivalente a `tsc --noEmit && vite build` (`frontend/package.json`).

### Output Directory

```text
dist
```

### Variables De Entorno

| Variable              | Valor en produccion                          | Notas |
| ----------------------- | ---------------------------------------------- | ----- |
| `VITE_API_BASE_URL`      | URL publica del Backend ya desplegado + `/api/v1` | Ejemplo de forma: `https://backend-real.ondigitalocean.app/api/v1`. Se usa en build time (Vite), asi que hay que cargarla **antes** de que corra el Build Command -- si se cambia despues hace falta un nuevo build. |

### Catchall Document

Activar en la configuracion del Static Site: **catchall document ->
`index.html`**.

`frontend/src/App.tsx` usa `BrowserRouter` (rutas del lado del cliente). Sin
el catchall, entrar directo a una URL que no sea la raiz devuelve 404 del
servidor de archivos estatico en vez de cargar `index.html` y dejar que
React Router resuelva la ruta.

## `frontend-admin/` (Static Site)

### Build Command

```text
npm run build
```

Equivalente a `tsc --noEmit && vite build` (`frontend-admin/package.json`).

### Output Directory

```text
dist
```

### Variables De Entorno

| Variable              | Valor en produccion                          | Notas |
| ----------------------- | ---------------------------------------------- | ----- |
| `VITE_API_BASE_URL`      | La misma URL del Backend que usa `frontend/` + `/api/v1` | Mismo backend para los dos frontends; no son URLs distintas. |

### Catchall Document

Activar en la configuracion del Static Site: **catchall document ->
`index.html`**.

`frontend-admin/src/App.tsx` tambien usa `BrowserRouter`. Sin el catchall,
entrar directo a una URL como `/votaciones/5` da 404 en vez de cargar la
app -- confirmado en `App.tsx`.

## Checklist Final Para Sebad (Parte B, Manual En El Dashboard)

- [ ] Crear la app en App Platform con los tres componentes (Backend,
      `frontend`, `frontend-admin`) apuntando cada uno a su carpeta
      (`backend/`, `frontend/`, `frontend-admin/`) del mismo repositorio.
- [ ] Vincular la base de datos administrada de PostgreSQL ya existente al
      componente Backend.
- [ ] Backend: configurar Run Command
      (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`).
- [ ] Backend: configurar Pre-Deploy Job (`alembic upgrade head`).
- [ ] Backend: cargar las variables de entorno de la tabla de arriba
      (`DATABASE_URL`, `SECRET_KEY`, `ADMIN_API_KEY`, `ADMIN_USERNAME`,
      `ADMIN_PASSWORD`, `CORS_ORIGINS`, `RATE_LIMIT_POR_MINUTO`, y las
      opcionales si aplica).
- [ ] Desplegar primero el Backend y anotar su URL publica.
- [ ] `frontend/`: configurar Build Command (`npm run build`), Output
      Directory (`dist`) y `VITE_API_BASE_URL` apuntando a la URL del
      Backend + `/api/v1`.
- [ ] `frontend/`: activar catchall document -> `index.html`.
- [ ] `frontend-admin/`: configurar Build Command (`npm run build`), Output
      Directory (`dist`) y `VITE_API_BASE_URL` apuntando a la misma URL del
      Backend + `/api/v1`.
- [ ] `frontend-admin/`: activar catchall document -> `index.html`.
- [ ] Una vez desplegados los dos Static Sites, volver a Backend y
      actualizar `CORS_ORIGINS` con las URLs reales que DigitalOcean asigno
      (no se conocen hasta que los Static Sites existen), y volver a
      desplegar el Backend para que tome el valor nuevo.
- [ ] Verificar `GET /api/v1/health` en la URL publica del Backend.
- [ ] Verificar que `frontend/` carga y consulta el backend real.
- [ ] Verificar el login de `frontend-admin/` y que entrar directo a una
      URL interna (por ejemplo `/votaciones`) no da 404.
