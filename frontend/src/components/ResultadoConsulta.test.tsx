import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { HabilitacionConsultaResponse } from "../api/habilitacion";
import { ResultadoConsulta } from "./ResultadoConsulta";

function consultaBase(overrides: Partial<HabilitacionConsultaResponse>): HabilitacionConsultaResponse {
  return {
    celular_normalizado: "0981000001",
    habilitado: false,
    personas: [],
    unidades: [],
    ...overrides,
  };
}

describe("ResultadoConsulta", () => {
  it("muestra que el celular no esta en el padron cuando no hay ninguna unidad", () => {
    render(
      <ResultadoConsulta consulta={consultaBase({ unidades: [] })} onElegirUnidad={vi.fn()} />,
    );

    expect(screen.getByText(/este celular no está en el padrón/i)).toBeInTheDocument();
  });

  it("muestra el motivo traducido de una unidad bloqueada, sin el codigo tecnico crudo", () => {
    const consulta = consultaBase({
      unidades: [
        {
          unidad_electoral_id: 1,
          tipo: "MATRIMONIO_CONSAGRADO",
          descripcion: null,
          estado: "BLOQUEADA_POR_INCIDENCIA",
          disponible: false,
          motivo_no_disponible: "BLOQUEADA_POR_INCIDENCIA",
          incidencias: [],
        },
      ],
    });

    render(<ResultadoConsulta consulta={consulta} onElegirUnidad={vi.fn()} />);

    expect(
      screen.getByText(/hay un problema con tus datos, contactá al administrador/i),
    ).toBeInTheDocument();
    expect(screen.queryByText("BLOQUEADA_POR_INCIDENCIA")).not.toBeInTheDocument();
  });

  it("muestra dos opciones separadas para el doble rol de jefe consagrado", async () => {
    const user = userEvent.setup();
    const onElegirUnidad = vi.fn();
    const consulta = consultaBase({
      habilitado: true,
      unidades: [
        {
          unidad_electoral_id: 1,
          tipo: "MATRIMONIO_CONSAGRADO",
          descripcion: null,
          estado: "HABILITADA",
          disponible: true,
          motivo_no_disponible: null,
          incidencias: [],
        },
        {
          unidad_electoral_id: 2,
          tipo: "BLOQUE_NO_CONSAGRADO",
          descripcion: null,
          estado: "HABILITADA",
          disponible: true,
          motivo_no_disponible: null,
          incidencias: [],
        },
      ],
    });

    render(<ResultadoConsulta consulta={consulta} onElegirUnidad={onElegirUnidad} />);

    const matrimonio = screen.getByRole("button", { name: /votar por tu matrimonio consagrado/i });
    const bloque = screen.getByRole("button", { name: /votar por el bloque de tu círculo/i });
    expect(matrimonio).toBeInTheDocument();
    expect(bloque).toBeInTheDocument();

    await user.click(bloque);
    expect(onElegirUnidad).toHaveBeenCalledTimes(1);
    expect(onElegirUnidad).toHaveBeenCalledWith(consulta.unidades[1]);
  });
});
