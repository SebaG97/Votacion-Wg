import { apiGet, apiPost } from "./client";

export type EstadoPersona = "ACTIVA" | "BAJA_NO_ML" | "BAJA_OBSERVACION";

export type TipoUnidadElectoral = "MATRIMONIO_CONSAGRADO" | "BLOQUE_NO_CONSAGRADO";

export type EstadoUnidadElectoral =
  | "HABILITADA"
  | "BLOQUEADA_POR_INCIDENCIA"
  | "PENDIENTE_DEFINICION_POSTULANTES"
  | "PENDIENTE_DEFINICION_BAJA";

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

export type PadronUnidadElectoral = {
  id: number;
  tipo: TipoUnidadElectoral;
  estado: string | null;
};

/**
 * Fila de `GET /padron/personas` (Mision 12, DEC-031): datos de padron
 * (persona, circulo, matrimonio, unidades electorales). Deliberadamente sin
 * ningun dato de `Voto` -- este visor es para consultar quien es quien y su
 * habilitacion, no para ver ni cruzar que voto cada unidad (DEC-020).
 */
export type PadronPersona = {
  id: number;
  nombres: string;
  apellidos: string;
  documento: string | null;
  celular: string | null;
  estado: EstadoPersona;
  grupo_id: number | null;
  circulo: string | null;
  es_jefe_grupo: boolean;
  matrimonio_id: number | null;
  matrimonio_estado: string | null;
  es_consagrado: boolean | null;
  unidades_electorales: PadronUnidadElectoral[];
};

export type PadronListado = {
  total: number;
  pagina: number;
  tamanio_pagina: number;
  items: PadronPersona[];
};

export type FiltrosPadron = {
  circulo?: string;
  grupo_id?: number;
  estado_persona?: EstadoPersona;
  estado_unidad_electoral?: EstadoUnidadElectoral;
  tipo_unidad_electoral?: TipoUnidadElectoral;
  nombre?: string;
  documento?: string;
  celular?: string;
  pagina?: number;
  tamanio_pagina?: number;
};

function construirQueryPadron(filtros: FiltrosPadron): string {
  const params = new URLSearchParams();
  if (filtros.circulo) params.set("circulo", filtros.circulo);
  if (filtros.grupo_id !== undefined) params.set("grupo_id", String(filtros.grupo_id));
  if (filtros.estado_persona) params.set("estado_persona", filtros.estado_persona);
  if (filtros.estado_unidad_electoral) {
    params.set("estado_unidad_electoral", filtros.estado_unidad_electoral);
  }
  if (filtros.tipo_unidad_electoral) {
    params.set("tipo_unidad_electoral", filtros.tipo_unidad_electoral);
  }
  if (filtros.nombre) params.set("nombre", filtros.nombre);
  if (filtros.documento) params.set("documento", filtros.documento);
  if (filtros.celular) params.set("celular", filtros.celular);
  if (filtros.pagina !== undefined) params.set("pagina", String(filtros.pagina));
  if (filtros.tamanio_pagina !== undefined) {
    params.set("tamanio_pagina", String(filtros.tamanio_pagina));
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function listarPadron(filtros: FiltrosPadron = {}): Promise<PadronListado> {
  return apiGet<PadronListado>(`/padron/personas${construirQueryPadron(filtros)}`);
}
