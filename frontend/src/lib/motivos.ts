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
    case "CELULAR_DUPLICADO":
      return "Este celular figura en más de un matrimonio del padrón. Contactá al administrador para revisarlo.";
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
 * acciones separadas y claramente identificadas, nunca combinadas. Desde
 * DEC-042 un educador puede votar varios bloques, asi que el del bloque
 * nombra al circulo cuando la descripcion lo trae.
 */
export function etiquetaUnidad(tipo: TipoUnidadElectoral, descripcion?: string | null): string {
  if (tipo === "MATRIMONIO_CONSAGRADO") {
    return "Votar por tu matrimonio consagrado";
  }
  const circulo = descripcion?.match(/^Bloque no consagrado de (.+)$/)?.[1]?.trim();
  return circulo ? `Votar por el bloque de ${circulo}` : "Votar por el bloque de tu círculo";
}
