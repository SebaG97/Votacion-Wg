"""Logica de lectura, normalizacion e importacion del padron (Mision 04).

Extraido de `backend/scripts/explorar_padron.py` (Mision 02) para que tanto el
script exploratorio como el importador real (`app.services.padron.importador`)
usen las mismas reglas validadas: clasificacion estructural de filas,
normalizacion de celular/CI, agrupamiento de matrimonios y deteccion de
incidencias. Ver `docs/PADRON_ANALISIS.md` y `docs/DECISIONES.md` (DEC-005 a
DEC-011) para el detalle de cada regla.
"""
