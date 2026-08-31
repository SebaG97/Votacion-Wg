# Modelo De Datos Inicial

Este modelo es preliminar y debe ajustarse despues de analizar el Excel base.

## Tablas Sugeridas

### personas

- id
- nombres
- apellidos
- celular
- documento
- estado
- grupo_id
- matrimonio_id
- es_jefe_grupo
- created_at
- updated_at

### matrimonios

- id
- codigo_externo
- integrante_1_id
- integrante_2_id
- es_consagrado
- grupo_id
- estado
- created_at
- updated_at

### grupos

- id
- nombre
- circulo
- jefe_persona_id
- tipo
- estado
- created_at
- updated_at

### unidades_electorales

- id
- tipo
- referencia_id
- grupo_id
- descripcion
- cantidad_personas_control
- estado
- created_at
- updated_at

Tipos iniciales:

- `MATRIMONIO_CONSAGRADO`
- `BLOQUE_NO_CONSAGRADO`

### votaciones

- id
- nombre
- estado
- fecha_apertura
- fecha_cierre
- resultados_revelados_at
- created_at
- updated_at

Estados iniciales:

- `BORRADOR`
- `ABIERTA`
- `CERRADA`
- `RESULTADOS_REVELADOS`

### votos

- id
- votacion_id
- unidad_electoral_id
- opcion_id
- emitido_por_persona_id
- celular_consultado
- fecha_emision
- canal
- metadata

Restriccion clave:

- `votacion_id` + `unidad_electoral_id` debe ser unico.

### opciones_voto

- id
- votacion_id
- nombre
- orden
- estado

### incidencias_padron

- id
- tipo
- descripcion
- persona_id
- grupo_id
- estado
- resuelto_por
- resuelto_at
- created_at

## Pendientes De Confirmacion

- Si el celular sera obligatorio para todas las personas.
- Si puede haber matrimonios con mas datos historicos que dos integrantes activos.
- Si un jefe puede representar mas de un grupo.
- Como se define formalmente un matrimonio no consagrado en el Excel.
