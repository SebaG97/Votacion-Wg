# Importacion Del Excel

## Objetivo

Convertir el padron recibido en un modelo normalizado para votar con control y auditoria.

## Flujo Propuesto

1. Cargar archivo Excel.
2. Listar hojas y columnas.
3. Detectar columnas candidatas para persona, celular, matrimonio, consagracion, grupo y jefe.
4. Generar vista previa de datos.
5. Validar duplicados e inconsistencias.
6. Crear personas, matrimonios, grupos y unidades electorales.
7. Emitir informe de importacion.

## Validaciones Minimas

- Celular vacio.
- Celular duplicado.
- Matrimonio consagrado sin ambos integrantes.
- Persona asignada a mas de un matrimonio activo.
- Grupo sin jefe.
- Jefe con celular inexistente.
- Grupo mixto sin clasificacion clara de consagrados y no consagrados.

## Salida Esperada

- Registros importados.
- Registros omitidos.
- Incidencias abiertas.
- Total maximo de votos por tipo de unidad electoral.
