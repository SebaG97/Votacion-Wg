# Requerimiento Inicial

## Objetivo

Sistema de votacion en base a un padron de personas.

## Identificador De Consulta

El numero unico de referencia para consultar y habilitar una votacion sera el celular.

## Reglas De Votacion

### Matrimonios Consagrados

- Corresponde un voto por matrimonio consagrado.
- Puede votar uno de los dos integrantes.
- Cuando vota uno de ellos, el matrimonio completo queda marcado como votado.
- El sistema debe impedir un segundo voto del mismo matrimonio.

### Agrupaciones De Matrimonios No Consagrados

- Corresponde un voto por grupo o agrupacion de matrimonios no consagrados.
- La habilitacion se realiza por el numero de celular del jefe del grupo.
- El voto del jefe representa a la agrupacion no consagrada.

### Grupos Mixtos

- Pueden votar los matrimonios consagrados individualmente, segun la regla de un voto por matrimonio.
- Tambien puede existir el voto del jefe por los matrimonios no consagrados del grupo.
- Si el jefe tambien pertenece a un matrimonio consagrado, el sistema debe resolver y auditar si actua como:
  - votante de su matrimonio consagrado;
  - jefe habilitado para el bloque no consagrado;
  - ambos, cuando corresponda y este permitido.

## Resultados

- Los resultados solo se revelan despues de concluida la votacion.
- Antes del cierre, el sistema puede mostrar estado operativo, cantidad de habilitados, cantidad de votos emitidos y pendientes, pero no resultados por opcion.

## Insumo Inicial

El padron base sera importado desde un archivo Excel de aproximadamente 15 MB que sera entregado en una etapa posterior.
