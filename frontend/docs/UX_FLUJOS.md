# Flujos UX

## Consulta Por Celular

1. Usuario ingresa celular.
2. Frontend llama a la API de habilitacion.
3. Si no hay habilitacion, muestra estado no habilitado.
4. Si hay una unidad electoral disponible, continua al voto.
5. Si hay varias, solicita elegir rol o unidad electoral.
6. Si hay incidencia, informa que requiere revision administrativa.

## Caso Jefe Consagrado

Cuando una persona es jefe de grupo y tambien pertenece a un matrimonio consagrado:

- Mostrar dos acciones separadas si ambas estan habilitadas.
- Identificar una como voto del matrimonio consagrado.
- Identificar otra como voto del bloque no consagrado del grupo.
- Registrar cada voto contra una unidad electoral distinta.

## Panel Administrativo

Vistas esperadas:

- Resumen del padron.
- Incidencias.
- Conteo operativo de votos.
- Apertura y cierre de votacion.
- Resultados finales solo despues del cierre.
