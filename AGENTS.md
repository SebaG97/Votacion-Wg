# Instrucciones Para Codex

## Rol

Actuar como orquestador tecnico del proyecto VOTACION WG. Antes de implementar, leer la documentacion en `docs/`, `backend/docs/` y `frontend/docs/`.

## Principios

- Mantener backend y frontend separados.
- Documentar cada decision funcional relevante.
- No modificar reglas de votacion sin dejar una decision registrada en `docs/DECISIONES.md`.
- Tratar el numero de celular como identificador de consulta, pero no asumir que es unico hasta validar el Excel.
- Proteger los resultados: no deben exponerse antes del cierre formal de la votacion.

## Flujo De Trabajo

1. Leer requerimiento y reglas vigentes.
2. Revisar el impacto en padron, habilitacion, auditoria y resultados.
3. Implementar cambios chicos y verificables.
4. Actualizar documentacion cuando cambie el comportamiento.
5. Ejecutar pruebas del modulo afectado.

## Tecnologia Esperada

- Backend: Python/FastAPI, SQLAlchemy, Alembic, Pydantic.
- Frontend: React, TypeScript, Vite.
- Estilo de API: REST versionada bajo `/api/v1`.

## Zonas Sensibles

- Duplicidad de numeros de celular.
- Jefes de grupo que tambien son integrantes de matrimonios consagrados.
- Matrimonios incompletos o mal cargados en el padron.
- Grupos mixtos.
- Momento exacto de cierre y revelacion de resultados.
- Trazabilidad de quien habilito o emitio cada voto.
