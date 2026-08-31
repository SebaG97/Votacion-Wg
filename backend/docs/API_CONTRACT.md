# Contrato API Inicial

## Consultar Habilitacion

`POST /api/v1/habilitaciones/consultar`

Request:

```json
{
  "celular": "0981123456"
}
```

Response:

```json
{
  "persona": {
    "id": "per_123",
    "nombre_completo": "Nombre Apellido",
    "celular": "0981123456"
  },
  "unidades_disponibles": [
    {
      "id": "ue_1",
      "tipo": "MATRIMONIO_CONSAGRADO",
      "descripcion": "Matrimonio consagrado",
      "ya_voto": false
    }
  ],
  "incidencias": []
}
```

## Emitir Voto

`POST /api/v1/votaciones/{votacion_id}/votos`

Request:

```json
{
  "unidad_electoral_id": "ue_1",
  "opcion_id": "op_1",
  "celular_consultado": "0981123456"
}
```

Regla: una unidad electoral no puede emitir mas de un voto por votacion.

## Estado De Votacion

`GET /api/v1/votaciones/{votacion_id}/estado`

Debe devolver estado general, conteos operativos y si los resultados estan disponibles.

## Resultados

`GET /api/v1/votaciones/{votacion_id}/resultados`

Debe responder error si la votacion no esta cerrada o si los resultados aun no fueron revelados.
