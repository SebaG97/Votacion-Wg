import { ArrowRight } from "lucide-react";

import type { HabilitacionConsultaResponse, UnidadElectoralDisponible } from "../api/habilitacion";
import { etiquetaUnidad, traducirMotivoNoDisponible } from "../lib/motivos";

type ResultadoConsultaProps = {
  consulta: HabilitacionConsultaResponse;
  onElegirUnidad: (unidad: UnidadElectoralDisponible) => void;
};

export function ResultadoConsulta({ consulta, onElegirUnidad }: ResultadoConsultaProps) {
  if (consulta.unidades.length === 0) {
    return (
      <section className="panel">
        <p className="eyebrow">Resultado de la consulta</p>
        <h1>Este celular no está en el padrón</h1>
        <p>Verificá el número o consultá con el administrador de tu círculo.</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <p className="eyebrow">Resultado de la consulta</p>
      <h1>Elegí qué voto emitir</h1>

      <ul className="unidad-list">
        {consulta.unidades.map((unidad) => (
          <li key={unidad.unidad_electoral_id}>
            {unidad.disponible ? (
              <button
                type="button"
                className="unidad-card disponible"
                onClick={() => onElegirUnidad(unidad)}
              >
                <span>{etiquetaUnidad(unidad.tipo)}</span>
                <ArrowRight size={18} />
              </button>
            ) : (
              <div className="unidad-card no-disponible">
                <span>{etiquetaUnidad(unidad.tipo)}</span>
                <p className="motivo">{traducirMotivoNoDisponible(unidad.motivo_no_disponible)}</p>
              </div>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
