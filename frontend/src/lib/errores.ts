import { ApiError } from "../api/client";

/**
 * Mensaje generico para un error de API, sin exponer el detalle tecnico del
 * backend. `status === undefined` significa que `fetch` nunca llego a
 * responder (sin conexion); un status HTTP real llega con codigo.
 */
export function mensajeDeError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === undefined) {
      return "Sin conexión. Verificá tu internet e intentá de nuevo.";
    }
    if (err.status === 409) {
      return "No hay ninguna votación abierta en este momento.";
    }
    return "No se pudo completar la operación. Intentá de nuevo.";
  }
  return "Ocurrió un error inesperado.";
}
