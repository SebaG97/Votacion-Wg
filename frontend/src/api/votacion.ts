import { apiGet, apiPost } from "./client";

export type OpcionAbierta = {
  id: number;
  nombre: string;
  orden: number | null;
};

export type VotacionAbierta = {
  votacion_id: number;
  nombre: string;
  opciones: OpcionAbierta[];
};

/**
 * Papeleta de la unica votacion ABIERTA (`GET /votaciones/abierta`, DEC-023).
 * Publico, sin token administrativo: es lo que este frontend de votacion
 * necesita para saber contra que opciones puede votar el usuario.
 */
export function getVotacionAbierta(): Promise<VotacionAbierta> {
  return apiGet<VotacionAbierta>("/votaciones/abierta");
}

export type VotoRequest = {
  celular_consultado: string;
  unidad_electoral_id: number;
  opcion_id: number;
  emitido_por_persona_id: number;
  canal?: string;
};

export type VotoResponse = {
  id: number;
  votacion_id: number;
  unidad_electoral_id: number;
  opcion_id: number;
  emitido_por_persona_id: number | null;
  celular_consultado: string | null;
  fecha_emision: string;
  canal: string | null;
};

export function registrarVoto(votacionId: number, body: VotoRequest): Promise<VotoResponse> {
  return apiPost<VotoResponse, VotoRequest>(`/votaciones/${votacionId}/votos`, body);
}
