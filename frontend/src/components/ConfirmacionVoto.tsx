import { CheckCircle2 } from "lucide-react";

import type { VotoResponse } from "../api/votacion";

type ConfirmacionVotoProps = {
  voto: VotoResponse;
};

/**
 * Pantalla final del flujo: deliberadamente no ofrece ningun boton para
 * volver a votar la misma unidad. Una vez acá, el unico camino es recargar
 * la aplicacion, que arranca de cero desde la consulta por celular.
 */
export function ConfirmacionVoto({ voto }: ConfirmacionVotoProps) {
  const fecha = new Date(voto.fecha_emision);
  const fechaFormateada = Number.isNaN(fecha.getTime())
    ? voto.fecha_emision
    : fecha.toLocaleString("es-PY", { dateStyle: "long", timeStyle: "short" });

  return (
    <section className="panel confirmacion-panel">
      <span className="icon-success">
        <CheckCircle2 size={44} />
      </span>
      <p className="eyebrow">Voto registrado</p>
      <h1>Tu voto se registró correctamente</h1>
      <p>{fechaFormateada}</p>
    </section>
  );
}
