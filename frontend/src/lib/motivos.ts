import type { TipoUnidadElectoral } from "../api/habilitacion";

/**
 * Traduce el `motivo_no_disponible` crudo de `HabilitacionConsultaResponse`
 * a lenguaje claro. Nunca se muestra el codigo tecnico (`BLOQUEADA_POR_INCIDENCIA`,
 * etc.) directamente en pantalla.
 */
export function traducirMotivoNoDisponible(motivo: string | null): string {
  switch (motivo) {
    case "BLOQUEADA_POR_INCIDENCIA":
      return "Hay un problema con tus datos, contactá al administrador.";
    case "YA_VOTADO":
      return "Esta unidad ya emitió su voto.";
    case "PENDIENTE_DEFINICION_POSTULANTES":
    case "PENDIENTE_DEFINICION_BAJA":
      return "Esta unidad no tiene voto habilitado en esta elección.";
    default:
      return "No está disponible para votar en este momento.";
  }
}

/**
 * Etiqueta del voto por tipo de unidad electoral (criterio de aceptacion de
 * la Mision 09): el doble rol de jefe consagrado se muestra como dos
 * acciones separadas y claramente identificadas, nunca combinadas.
 */
export function etiquetaUnidad(tipo: TipoUnidadElectoral): string {
  return tipo === "MATRIMONIO_CONSAGRADO"
    ? "Votar por tu matrimonio consagrado"
    : "Votar por el bloque de tu círculo";
}
