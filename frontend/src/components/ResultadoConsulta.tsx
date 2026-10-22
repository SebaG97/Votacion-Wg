import { ArrowRight } from "lucide-react";

import type { HabilitacionConsultaResponse, UnidadElectoralDisponible } from "../api/habilitacion";
import { etiquetaUnidad, traducirMotivoNoDisponible } from "../lib/motivos";

type ResultadoConsultaProps = {
  consulta: HabilitacionConsultaResponse;
  onElegirUnidad: (unidad: UnidadElectoralDisponible) => void;
};

export function ResultadoConsulta({ consulta, onElegirUnidad }: ResultadoConsultaProps) {
  if (consulta.unidades.length === 0 && consulta.personas.length > 0) {
    // La persona esta en el padron pero no tiene ningun voto a su cargo: en los
    // circulos no consagrados vota solo el jefe (o el educador), por el bloque.
    return (
      <section className="panel">
        <p className="eyebrow">Resultado de la consulta</p>
        <h1>No tenés un voto a tu cargo</h1>
        <p>
          Figurás en el padrón, pero tu voto lo emite otra persona: en los círculos no consagrados
          vota por todo el bloque el jefe de círculo o, en los de postulantes, el educador. Si creés
          que es un error, consultá con el administrador.
        </p>
      </section>
    );
  }

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
                <span>{etiquetaUnidad(unidad.tipo, unidad.descripcion)}</span>
                <ArrowRight size={18} />
              </button>
            ) : (
              <div className="unidad-card no-disponible">
                <span>{etiquetaUnidad(unidad.tipo, unidad.descripcion)}</span>
                <p className="motivo">{traducirMotivoNoDisponible(unidad.motivo_no_disponible)}</p>
              </div>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
