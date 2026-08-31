# Reglas De Negocio

## Entidades Conceptuales

- Persona: integrante del padron.
- Matrimonio: unidad formada por dos personas.
- Matrimonio consagrado: matrimonio con derecho a un voto propio.
- Grupo o circulo: agrupacion de matrimonios y personas bajo control operativo.
- Jefe de grupo: persona autorizada para votar por el bloque no consagrado del grupo.
- Votacion: evento electoral con apertura, cierre y revelacion.
- Voto: registro emitido contra una unidad electoral habilitada.

## Unidad Electoral

La unidad electoral es la entidad que consume el derecho a voto.

- Para matrimonios consagrados, la unidad electoral es el matrimonio.
- Para no consagrados agrupados, la unidad electoral es el grupo o subgrupo representado por el jefe.

## Habilitacion Por Celular

El sistema consulta por celular y devuelve las unidades electorales disponibles para esa persona.

Casos esperados:

- Persona pertenece a un matrimonio consagrado no votado: puede votar por su matrimonio.
- Persona es jefe de grupo con bloque no consagrado no votado: puede votar por ese bloque.
- Persona cumple ambos roles: el sistema debe presentar opciones separadas y registrar cada voto con su unidad electoral.
- Celular duplicado: el sistema debe bloquear la emision directa y enviar a resolucion administrativa.
- Celular inexistente: no habilitado.

## Control De Cantidad

El total de votos maximos debe calcularse desde el padron normalizado:

- Total de matrimonios consagrados habilitados.
- Total de unidades no consagradas representadas por jefe.
- Total de unidades mixtas separadas por tipo.

Los reportes deben comparar votos emitidos contra votos maximos por grupo, circulo y total general.

## Revelacion De Resultados

Mientras la votacion este abierta:

- Permitido: cantidad de votos emitidos, pendientes, incidencias, estado de mesas o dispositivos.
- No permitido: resultados por candidato, opcion o lista.

Despues del cierre:

- Los resultados pueden revelarse si la votacion tiene estado `CERRADA`.
- La auditoria debe conservar fecha, hora y usuario que ejecuto el cierre.
