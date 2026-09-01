# Plan De Backup

La votacion queda abierta en internet por dias o semanas, no un evento de un
dia (ver DEC-029 en `docs/DECISIONES.md`). Este documento cubre como se
respalda la base PostgreSQL real de DigitalOcean durante ese periodo y como
restaurarla si hace falta.

## Punto Pendiente De Confirmar Con Sebad

Este plan cubre los dos escenarios posibles porque, al momento de escribirlo,
no esta confirmado cual de los dos aplica al despliegue real:

- **Si la base es un DigitalOcean Managed Database (Postgres administrado)**:
  ya incluye backups automaticos diarios con un periodo de retencion fijo
  (tipicamente 7 dias en el plan basico) y point-in-time recovery dentro de
  ese periodo, gestionados por DigitalOcean sin configuracion adicional.
- **Si la base corre en un Droplet propio** (Postgres instalado a mano, sin
  el servicio administrado): no hay ningun backup automatico salvo que se
  configure explicitamente -- corresponde la rutina de `pg_dump` manual de
  este documento.

Accion pendiente: confirmar con Sebad cual de los dos escenarios es el real
antes de la votacion, y tachar la seccion que no aplica.

## Escenario A - DigitalOcean Managed Database

Si la base es un cluster administrado:

1. Confirmar en el panel de DigitalOcean (seccion **Backups** del cluster)
   la hora del backup diario automatico y la ventana de retencion.
2. Antes de abrir la votacion y antes de revelar resultados, ademas del
   automatico, tomar un backup **manual bajo demanda** desde el mismo panel
   (DigitalOcean permite forzar uno fuera del horario programado) -- son los
   dos momentos de mayor costo si algo sale mal.
3. Restauracion: DigitalOcean permite crear un cluster nuevo a partir de un
   backup (o de un punto en el tiempo dentro de la ventana de retencion) sin
   sobrescribir el original. Restaurar sobre un cluster nuevo primero,
   verificar los datos, y recien despues decidir si el backend debe apuntar
   ahi (cambiando `DATABASE_URL`) -- nunca restaurar directo sobre la base en
   uso mientras la votacion sigue activa.

## Escenario B - Postgres Sin Backup Administrado (`pg_dump` Manual)

Si no hay backup automatico del proveedor:

### Rutina Periodica

```powershell
# Requiere pg_dump del mismo major version que el servidor (v18) instalado localmente,
# o correrlo desde una maquina con acceso a la red de la base.
$fecha = Get-Date -Format "yyyyMMdd-HHmmss"
pg_dump --format=custom --file="votacion_wg_$fecha.dump" "$env:DATABASE_URL"
```

- Frecuencia recomendada mientras la votacion esta **abierta**: al menos una
  vez por dia; si el volumen de votos lo justifica, cada varias horas.
- Momentos obligatorios independientes de la frecuencia periodica: **antes de
  abrir**, **inmediatamente despues de cerrar** y **antes de revelar**
  resultados -- son los tres puntos donde perder el estado seria mas grave.
- Guardar cada dump fuera de la maquina que corre el backend (otro disco,
  almacenamiento en la nube, o al menos otro directorio con su propio
  control de acceso) -- un backup en el mismo disco que falla no sirve de
  nada.
- Retener todos los dumps generados durante la ventana de votacion (no
  rotarlos hasta que la votacion termine y los resultados esten comunicados
  y archivados).

### Restauracion

```powershell
# Contra una base nueva y vacia, nunca sobre la base en uso:
pg_restore --dbname="$env:DATABASE_URL_NUEVA" --clean --if-exists "votacion_wg_20260901-120000.dump"
```

1. Restaurar siempre sobre una base **nueva**, nunca sobre la que esta en
   produccion mientras algo todavia depende de ella.
2. Verificar los conteos clave antes de decidir el corte: `SELECT count(*)
   FROM votos;`, `SELECT estado, count(*) FROM votaciones GROUP BY estado;`,
   y comparar contra `GET /votaciones/{id}/estado` del backend que seguia
   corriendo (si sigue disponible) o contra el ultimo estado conocido.
3. Solo despues de verificar, decidir si el backend real pasa a apuntar a la
   base restaurada (cambiar `DATABASE_URL` y reiniciar el proceso).

## Que Se Respalda

Un solo `pg_dump`/backup de cluster cubre todo lo necesario: el esquema
completo (`personas`, `matrimonios`, `grupos`, `unidades_electorales`,
`votaciones`, `opciones_voto`, `votos`, `incidencias_padron`,
`importaciones_padron`) vive en la misma base, no hay almacenamiento
separado que respaldar aparte. El Excel original del padron
(`docs/Padron de ML con Jefes 2026.xlsx`) vive en el repositorio git, no en
la base, y ya tiene su propio historial de versiones ahi.

## Que No Cubre Este Plan

- Rotacion de `ADMIN_API_KEY` comprometida: eso es un procedimiento de
  seguridad, no de backup (rotar la variable de entorno y reiniciar el
  backend).
- Recuperacion ante perdida del dominio o del hosting del frontend (fuera de
  alcance: los frontends son estaticos y se pueden re-desplegar desde el
  repositorio git en cualquier momento, no dependen de estado propio).
