import { apiPost } from "./client";

export type PersonaConsultada = {
  persona_id: number;
  nombres: string;
  apellidos: string;
};

export type IncidenciaRespuesta = {
  tipo: string;
  severidad: string;
  descripcion: string | null;
};

export type TipoUnidadElectoral = "MATRIMONIO_CONSAGRADO" | "BLOQUE_NO_CONSAGRADO";

export type UnidadElectoralDisponible = {
  unidad_electoral_id: number;
  tipo: TipoUnidadElectoral;
  descripcion: string | null;
  estado: string;
  disponible: boolean;
  motivo_no_disponible: string | null;
  incidencias: IncidenciaRespuesta[];
};

export type HabilitacionConsultaResponse = {
  celular_normalizado: string | null;
  habilitado: boolean;
  personas: PersonaConsultada[];
  unidades: UnidadElectoralDisponible[];
};

export function consultarHabilitacion(celular: string): Promise<HabilitacionConsultaResponse> {
  return apiPost<HabilitacionConsultaResponse, { celular: string }>(
    "/habilitaciones/consultar",
    { celular },
  );
}
