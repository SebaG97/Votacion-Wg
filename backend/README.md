# Backend

API y capa de negocio del sistema VOTACION WG.

## Stack

- Python 3.11+
- FastAPI
- Pydantic Settings
- Pytest
- SQLAlchemy 2.0 y Alembic (SQLite en local, PostgreSQL en produccion via `DATABASE_URL`).

## Estructura

```text
app/
  api/
  core/
  db/
  models/
  schemas/
  services/
  tests/
alembic/
```

## Variables De Entorno

Ver `.env.example`.

## Instalacion Local

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

## Ejecutar API

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Endpoint inicial:

```text
GET http://127.0.0.1:8000/api/v1/health
```

## Scripts

### Explorador Del Padron

Analiza `docs/Padron de ML con Jefes 2026.xlsx` sin modificarlo y regenera los
informes de la Mision 02.

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python scripts/explorar_padron.py
```

Salidas: `docs/padron_incidencias.csv` y `docs/padron_estructura.json`.
Lectura del informe: `docs/PADRON_ANALISIS.md`.

Acepta `--excel` y `--salida` para apuntar a otro archivo o directorio.

### Seed De Desarrollo

Inserta un puñado de filas de ejemplo (no datos reales del padron) para
probar el modelo: un matrimonio consagrado de dos integrantes, un viudo
consagrado, un matrimonio sin marca de consagracion y un bloque no
consagrado con jefe. Requiere que las migraciones ya hayan corrido.

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python scripts/seed_dev.py
```

## Base De Datos Y Migraciones

`DATABASE_URL` (ver `.env.example`) resuelve SQLite en local o PostgreSQL en
produccion; los mismos modelos y migraciones corren sobre los dos motores.

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head          # aplica todas las migraciones
alembic downgrade base        # revierte todo (solo desarrollo)
alembic revision -m "mensaje" # nueva migracion en blanco
```

## Pruebas

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest
```
