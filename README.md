# VOTACION WG

Sistema de votacion basado en padron de personas, matrimonios consagrados y grupos de matrimonios no consagrados.

## Objetivo

Construir una plataforma interna para habilitar votos usando el numero de celular como referencia unica de consulta, controlar la emision de votos segun reglas del padron y revelar resultados solo al concluir la votacion.

## Tecnologia Base

- Backend: Python, FastAPI, SQLAlchemy, Alembic.
- Frontend: React, TypeScript, Vite.
- Base de datos inicial: importacion desde Excel provisto por el usuario.
- Base persistente sugerida: PostgreSQL para produccion y SQLite/PostgreSQL local segun entorno.

## Estructura

```text
VOTACION-WG/
  backend/
    README.md
    docs/
  frontend/
    README.md
    docs/
  frontend-admin/
    README.md
  docs/
  .vscode/
  AGENTS.md
```

## Regla Central

El sistema no cuenta votos por persona de forma directa. El voto se habilita segun la unidad electoral correspondiente:

- Matrimonio consagrado: un voto por matrimonio. Si vota cualquiera de los dos integrantes, el matrimonio queda marcado como votado.
- Grupo de matrimonios no consagrados: un voto por grupo, habilitado por el numero de celular del jefe.
- Grupo mixto: deben convivir los votos de matrimonios consagrados y el voto del jefe por los no consagrados.

## Estado Inicial

La Mision 01 dejo el scaffolding tecnico inicial:

- Backend FastAPI con `GET /api/v1/health`.
- Frontend React + TypeScript + Vite con pantalla de estado de conexion.
- Configuracion por variables de entorno.
- Pruebas iniciales del endpoint de salud.

## Ejecucion Local

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

URLs:

```text
API: http://127.0.0.1:8000/api/v1/health
Web: http://localhost:5173
```

El siguiente hito es analizar el Excel base, normalizar el padron y definir el modelo de datos final.
