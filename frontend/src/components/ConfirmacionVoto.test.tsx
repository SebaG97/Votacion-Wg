import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { VotoResponse } from "../api/votacion";
import { ConfirmacionVoto } from "./ConfirmacionVoto";

describe("ConfirmacionVoto", () => {
  it("muestra la fecha del voto y ningun boton para reenviar", () => {
    const voto: VotoResponse = {
      id: 1,
      votacion_id: 1,
      unidad_electoral_id: 7,
      opcion_id: 10,
      emitido_por_persona_id: 1,
      celular_consultado: "0981000001",
      fecha_emision: "2026-09-01T12:00:00",
      canal: null,
    };

    render(<ConfirmacionVoto voto={voto} />);

    expect(screen.getByText(/tu voto se registró correctamente/i)).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
