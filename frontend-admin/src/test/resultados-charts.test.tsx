import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import * as votacionesApi from "../api/votaciones";
import type { VotacionResultados } from "../api/votaciones";
import { ResultadosView } from "../components/ResultadosView";

vi.mock("../api/votaciones", async () => {
  const actual = await vi.importActual<typeof import("../api/votaciones")>("../api/votaciones");
  return { ...actual, obtenerResultados: vi.fn(), revelarResultados: vi.fn() };
});

function resultados(): VotacionResultados {
  return {
    votacion_id: 1,
    estado: "CERRADA",
    total_votos: 30,
    totales_por_opcion: [
      { opcion_id: 1, nombre: "Opción A", votos: 20, porcentaje: 66.67 },
      { opcion_id: 2, nombre: "Opción B", votos: 10, porcentaje: 33.33 },
    ],
    totales_por_tipo_unidad: [
      {
        tipo: "MATRIMONIO_CONSAGRADO",
        votos_emitidos: 25,
        unidades_habilitadas: 50,
        participacion: 0.5,
      },
      {
        tipo: "BLOQUE_NO_CONSAGRADO",
        votos_emitidos: 5,
        unidades_habilitadas: 10,
        participacion: null,
      },
    ],
    totales_por_grupo: [
      { grupo_id: 1, nombre: "CIRCULO A", votos_emitidos: 4, unidades_habilitadas: 4, participacion: 1 },
      { grupo_id: 2, nombre: "CIRCULO B", votos_emitidos: 0, unidades_habilitadas: 4, participacion: 0 },
    ],
  };
}

/**
 * Graficos de `ResultadosView` (Mision 13, DEC-035): junto a cada una de las
 * 3 tablas existentes, alimentados por los mismos datos ya cargados (sin
 * fetch nuevo). Este componente solo se monta con estado CERRADA o
 * RESULTADOS_REVELADOS (sin cambios en esa condicion), asi que los 3
 * graficos heredan la misma garantia de DEC-022 que las tablas -- la
 * cobertura de "nunca por opcion mientras ABIERTA" vive en
 * `no-resultados-prematuros.test.tsx`, que ejercita `VotacionDetailPage`
 * completo con los cuatro estados.
 */
describe("graficos de ResultadosView", () => {
  it("muestra un grafico por cada tabla, con los mismos valores", async () => {
    vi.mocked(votacionesApi.obtenerResultados).mockResolvedValue(resultados());

    render(<ResultadosView votacionId={1} estado="CERRADA" onRevelado={() => {}} />);

    await waitFor(() => expect(screen.getByTestId("chart-por-opcion")).toBeInTheDocument());

    const chartOpcion = screen.getByTestId("chart-por-opcion");
    expect(chartOpcion).toHaveTextContent("Opción A");
    expect(chartOpcion).toHaveTextContent("20 (66.7%)");
    expect(chartOpcion).toHaveTextContent("Opción B");
    expect(chartOpcion).toHaveTextContent("10 (33.3%)");

    const chartTipo = screen.getByTestId("chart-por-tipo-unidad");
    expect(chartTipo).toHaveTextContent("MATRIMONIO_CONSAGRADO");
    expect(chartTipo).toHaveTextContent("50.0%");
    expect(chartTipo).toHaveTextContent("BLOQUE_NO_CONSAGRADO");
    expect(chartTipo).toHaveTextContent("—");

    const chartCirculo = screen.getByTestId("chart-por-circulo");
    expect(chartCirculo).toHaveTextContent("CIRCULO A");
    expect(chartCirculo).toHaveTextContent("100.0%");
    expect(chartCirculo).toHaveTextContent("CIRCULO B");
    expect(chartCirculo).toHaveTextContent("0.0%");
  });
});
