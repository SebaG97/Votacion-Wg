import { ApiError } from "../api/client";
import { mensajeDeError } from "./errores";

/**
 * Traduce los `409`/`404` de la administracion de votacion e incidencias a
 * lenguaje claro, mismo patron que `clasificarConflicto` de
 * `PapeletaVoto.tsx` (Mision 09, DEC-024): cada excepcion del backend arma un
 * mensaje de `detail` con texto distinto (`app/services/votacion.py`,
 * `app/services/padron/administracion.py`), asi que se clasifica por
 * substring en vez de asumir que todo `409` significa lo mismo. Los checks
 * mas especificos van primero para no matchear por accidente con uno mas
 * generico.
 */
export function traducirErrorVotacion(err: unknown): string {
  if (!(err instanceof ApiError) || err.status === undefined) {
    return mensajeDeError(err);
  }

  const detalle = err.detail?.toLowerCase() ?? "";

  if (detalle.includes("no se puede reimportar el padron")) {
    return "No se puede reimportar: hay una votación abierta o cerrada. Cerrá o esperá a que vuelva a BORRADOR.";
  }
  if (detalle.includes("ya existe otra votacion abierta")) {
    return "Ya hay otra votación ABIERTA. Cerrala antes de abrir esta.";
  }
  if (detalle.includes("no tiene ninguna opcion cargada")) {
    return "Cargá al menos una opción antes de abrir la votación.";
  }
  if (detalle.includes("no esta en borrador")) {
    return "La votación ya salió de BORRADOR: no se pueden agregar ni editar opciones, ni volver a abrirla.";
  }
  if (detalle.includes("no esta abierta")) {
    return "La votación no está ABIERTA: no se puede cerrar.";
  }
  if (detalle.includes("no esta cerrada")) {
    return "La votación no está CERRADA: no se pueden revelar los resultados.";
  }
  if (detalle.includes("ya fueron revelados")) {
    return "Los resultados de esta votación ya fueron revelados.";
  }
  if (detalle.includes("resultados bloqueados")) {
    return "Los resultados están bloqueados hasta el cierre de la votación.";
  }
  if (detalle.includes("ya fue resuelta")) {
    return "Esta incidencia ya había sido marcada como revisada.";
  }
  if (detalle.includes("no existe")) {
    return "No se encontró lo que buscás: puede haber sido eliminado o el id es incorrecto.";
  }

  return mensajeDeError(err);
}
