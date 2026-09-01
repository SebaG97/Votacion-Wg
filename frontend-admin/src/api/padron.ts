import { apiGet, apiPost } from "./client";

export type EstadoImportacion = "EN_PROCESO" | "COMPLETADA" | "FALLIDA";

export type ImportacionPadron = {
  id: number;
  fecha: string;
  archivo_origen: string;
  usuario: string | null;
  estado: EstadoImportacion;
  resumen: Record<string, unknown> | null;
  error: string | null;
};

export type SeveridadIncidencia = "CRITICA" | "ALTA" | "MEDIA" | "BAJA";

export type IncidenciaPadron = {
  id: number;
  tipo: string;
  severidad: SeveridadIncidencia;
  descripcion: string | null;
  persona_id: number | null;
  grupo_id: number | null;
  importacion_id: number | null;
  resuelto_por: string | null;
  resuelto_at: string | null;
  created_at: string;
};

export type FiltrosIncidencias = {
  severidad?: SeveridadIncidencia;
  tipo?: string;
  resuelta?: boolean;
};

/** `GET /padron/importaciones` (Mision 10, DEC-025): historial, mas nueva
 * primero. */
export function listarImportaciones(): Promise<ImportacionPadron[]> {
  return apiGet<ImportacionPadron[]>("/padron/importaciones");
}

/** Operacion pesada: reescribe todo el padron (personas, matrimonios,
 * unidades electorales e incidencias). Quien llama a esto debe pedir
 * confirmacion explicita antes -- `ImportacionesPage` lo hace con un panel de
 * confirmacion, nunca dispara esto con un solo click. */
export function ejecutarImportacion(body: {
  excel_path?: string;
  usuario?: string;
}): Promise<ImportacionPadron> {
  return apiPost<ImportacionPadron, typeof body>("/padron/importaciones", body);
}

function construirQuery(filtros: FiltrosIncidencias): string {
  const params = new URLSearchParams();
  if (filtros.severidad) params.set("severidad", filtros.severidad);
  if (filtros.tipo) params.set("tipo", filtros.tipo);
  if (filtros.resuelta !== undefined) params.set("resuelta", String(filtros.resuelta));
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function listarIncidencias(filtros: FiltrosIncidencias = {}): Promise<IncidenciaPadron[]> {
  return apiGet<IncidenciaPadron[]>(`/padron/incidencias${construirQuery(filtros)}`);
}

/**
 * Marca una incidencia como revisada (`resuelto_por`/`resuelto_at`).
 * Trazabilidad administrativa pura (DEC-025): NO rehabilita ninguna unidad
 * electoral. `IncidenciasPage` muestra esa aclaracion junto al boton para que
 * el operador no confunda "revisado" con "vuelto a habilitar".
 */
export function resolverIncidencia(
  incidenciaId: number,
  usuario: string,
): Promise<IncidenciaPadron> {
  return apiPost<IncidenciaPadron, { usuario: string }>(
    `/padron/incidencias/${incidenciaId}/resolver`,
    { usuario },
  );
}
