import type { EstadoVotacion } from "../api/votaciones";

const ETIQUETAS: Record<EstadoVotacion, string> = {
  BORRADOR: "Borrador",
  ABIERTA: "Abierta",
  CERRADA: "Cerrada",
  RESULTADOS_REVELADOS: "Resultados revelados",
};

export function EstadoBadge({ estado }: { estado: EstadoVotacion }) {
  return <span className={`badge ${estado.toLowerCase()}`}>{ETIQUETAS[estado]}</span>;
}
