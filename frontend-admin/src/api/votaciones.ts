import { apiGet, apiPost } from "./client";

export type EstadoVotacion = "BORRADOR" | "ABIERTA" | "CERRADA" | "RESULTADOS_REVELADOS";

export type Votacion = {
  id: number;
  nombre: string;
  estado: EstadoVotacion;
  fecha_apertura: string | null;
  fecha_cierre: string | null;
  abierta_por: string | null;
  cerrada_por: string | null;
  resultados_revelados_at: string | null;
};

export type Opcion = {
  id: number;
  votacion_id: number;
  nombre: string;
  orden: number | null;
};

export type ConteoUnidadesPorEstado = {
  habilitada: number;
  bloqueada_por_incidencia: number;
  pendiente_definicion_postulantes: number;
  pendiente_definicion_baja: number;
};

export type VotacionEstado = {
  votacion_id: number;
  estado: EstadoVotacion;
  unidades_por_estado: ConteoUnidadesPorEstado;
  votos_emitidos: number;
  pendientes: number;
};

export type ResultadoOpcion = {
  opcion_id: number;
  nombre: string;
  votos: number;
  porcentaje: number;
};

export type ResultadoTipoUnidad = {
  tipo: "MATRIMONIO_CONSAGRADO" | "BLOQUE_NO_CONSAGRADO";
  votos_emitidos: number;
  unidades_habilitadas: number;
  participacion: number | null;
};

export type ResultadoGrupo = {
  grupo_id: number;
  nombre: string;
  votos_emitidos: number;
  unidades_habilitadas: number;
  participacion: number | null;
};

export type VotacionResultados = {
  votacion_id: number;
  estado: EstadoVotacion;
  total_votos: number;
  totales_por_opcion: ResultadoOpcion[];
  totales_por_tipo_unidad: ResultadoTipoUnidad[];
  totales_por_grupo: ResultadoGrupo[];
};

/** `GET /votaciones` (Mision 10, DEC-025): unico punto de entrada del panel
 * para descubrir que votaciones existen. */
export function listarVotaciones(): Promise<Votacion[]> {
  return apiGet<Votacion[]>("/votaciones");
}

export function crearVotacion(nombre: string): Promise<Votacion> {
  return apiPost<Votacion, { nombre: string }>("/votaciones", { nombre });
}

export function listarOpciones(votacionId: number): Promise<Opcion[]> {
  return apiGet<Opcion[]>(`/votaciones/${votacionId}/opciones`);
}

export function agregarOpcion(
  votacionId: number,
  body: { nombre: string; orden?: number | null },
): Promise<Opcion> {
  return apiPost<Opcion, typeof body>(`/votaciones/${votacionId}/opciones`, body);
}

export function abrirVotacion(votacionId: number, usuario: string): Promise<Votacion> {
  return apiPost<Votacion, { usuario: string }>(`/votaciones/${votacionId}/abrir`, { usuario });
}

export function cerrarVotacion(votacionId: number, usuario: string): Promise<Votacion> {
  return apiPost<Votacion, { usuario: string }>(`/votaciones/${votacionId}/cerrar`, { usuario });
}

export function obtenerEstadoOperativo(votacionId: number): Promise<VotacionEstado> {
  return apiGet<VotacionEstado>(`/votaciones/${votacionId}/estado`);
}

/**
 * `POST /votaciones/{id}/revelar` solo tiene sentido llamarlo desde estado
 * CERRADA (REGLAS_NEGOCIO.md, DEC-022) -- quien llama a esta funcion (los
 * controles de la votacion) es responsable de esa condicion; esta funcion no
 * la repite para no duplicar la logica de habilitacion del boton.
 */
export function revelarResultados(votacionId: number): Promise<Votacion> {
  return apiPost<Votacion>(`/votaciones/${votacionId}/revelar`);
}

/**
 * `GET /votaciones/{id}/resultados` esta bloqueado por el backend
 * (`ResultadosBloqueadosError`, DEC-022) salvo en CERRADA o
 * RESULTADOS_REVELADOS. Igual que `revelarResultados`, quien llama a esta
 * funcion debe respetar esa condicion antes de invocarla: `ResultadosView`
 * (`components/ResultadosView.tsx`) es el unico punto que la llama, y solo se
 * monta cuando la votacion ya esta en uno de esos dos estados.
 */
export function obtenerResultados(votacionId: number): Promise<VotacionResultados> {
  return apiGet<VotacionResultados>(`/votaciones/${votacionId}/resultados`);
}
