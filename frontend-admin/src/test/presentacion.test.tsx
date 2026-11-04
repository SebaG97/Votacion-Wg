import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as votacionesApi from "../api/votaciones";
import type { EstadoVotacion, Opcion, Votacion } from "../api/votaciones";
import { datosEnsayo, PresentacionPage } from "../routes/PresentacionPage";

vi.mock("../api/votaciones", async () => {
  const actual = await vi.importActual<typeof import("../api/votaciones")>("../api/votaciones");
  return {
    ...actual,
    listarVotaciones: vi.fn(),
    listarOpciones: vi.fn(),
    obtenerEstadoOperativo: vi.fn(),
    obtenerResultados: vi.fn(),
    revelarResultados: vi.fn(),
  };
});

function votacion(estado: EstadoVotacion): Votacion {
  return {
    id: 1,
    nombre: "Jefes ML 2027-2028",
    estado,
    fecha_apertura: null,
    fecha_cierre: null,
    abierta_por: null,
    cerrada_por: null,
    resultados_revelados_at: null,
  };
}

const opciones: Opcion[] = [
  { id: 10, votacion_id: 1, nombre: "Matrimonio A", orden: 1, tiene_foto: true },
  { id: 11, votacion_id: 1, nombre: "Matrimonio B", orden: 2, tiene_foto: false },
];

function renderPresentacion(url: string) {
  return render(
    <MemoryRouter initialEntries={[url]}>
      <Routes>
        <Route path="/votaciones/:id/presentacion" element={<PresentacionPage />} />
        <Route path="/votaciones/:id" element={<p>detalle</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

function avanzar(veces: number) {
  for (let i = 0; i < veces; i++) {
    act(() => {
      fireEvent.keyDown(window, { key: " " });
    });
  }
}

describe("presentacion en vivo de resultados (DEC-044)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(votacionesApi.listarOpciones).mockResolvedValue(opciones);
    vi.mocked(votacionesApi.obtenerEstadoOperativo).mockResolvedValue({
      votacion_id: 1,
      estado: "CERRADA",
      unidades_por_estado: {
        habilitada: 299,
        bloqueada_por_incidencia: 0,
        pendiente_definicion_postulantes: 0,
        pendiente_definicion_baja: 0,
      },
      votos_emitidos: 250,
      pendientes: 49,
    });
  });

  it.each(["ABIERTA", "CERRADA"] as const)(
    "con la votacion %s sin ensayo no pide resultados y avisa",
    async (estado) => {
      vi.mocked(votacionesApi.listarVotaciones).mockResolvedValue([votacion(estado)]);
      renderPresentacion("/votaciones/1/presentacion");

      expect(await screen.findByRole("alert")).toHaveTextContent(/todavía no se revelaron/i);
      expect(votacionesApi.obtenerResultados).not.toHaveBeenCalled();
    },
  );

  it("el ensayo nunca pide resultados reales y se marca como ficticio", async () => {
    vi.mocked(votacionesApi.listarVotaciones).mockResolvedValue([votacion("CERRADA")]);
    renderPresentacion("/votaciones/1/presentacion?ensayo=1");

    expect(await screen.findByText("Jefes ML 2027-2028")).toBeInTheDocument();
    expect(screen.getByText(/ENSAYO · datos ficticios/)).toBeInTheDocument();
    expect(votacionesApi.obtenerResultados).not.toHaveBeenCalled();
  });

  it("revelada: recorre portada, participacion, candidatos y ganador", async () => {
    vi.mocked(votacionesApi.listarVotaciones).mockResolvedValue([votacion("RESULTADOS_REVELADOS")]);
    vi.mocked(votacionesApi.obtenerResultados).mockResolvedValue({
      votacion_id: 1,
      estado: "RESULTADOS_REVELADOS",
      total_votos: 250,
      totales_por_opcion: [
        { opcion_id: 10, nombre: "Matrimonio A", votos: 100, porcentaje: 40 },
        { opcion_id: 11, nombre: "Matrimonio B", votos: 150, porcentaje: 60 },
      ],
      totales_por_tipo_unidad: [
        { tipo: "MATRIMONIO_CONSAGRADO", votos_emitidos: 200, unidades_habilitadas: 240, participacion: 0.83 },
        { tipo: "BLOQUE_NO_CONSAGRADO", votos_emitidos: 50, unidades_habilitadas: 59, participacion: 0.85 },
      ],
      totales_por_grupo: [],
    });

    renderPresentacion("/votaciones/1/presentacion");
    expect(await screen.findByText("Jefes ML 2027-2028")).toBeInTheDocument();
    expect(screen.queryByText(/ENSAYO/)).not.toBeInTheDocument();

    avanzar(1);
    expect(screen.getByText("Participación")).toBeInTheDocument();
    expect(screen.getByText(/299 votos/)).toBeInTheDocument();

    avanzar(1);
    expect(screen.getByText("Conteo de votos")).toBeInTheDocument();
    expect(screen.getByTestId("columna-10")).toHaveTextContent("Matrimonio A");
    expect(screen.getByTestId("columna-11")).toHaveTextContent("Matrimonio B");

    avanzar(1);
    await waitFor(() => expect(screen.getByTestId("ganador")).toHaveTextContent("Matrimonio B"));
    expect(screen.getByTestId("columna-11")).toHaveTextContent("150");
    expect(screen.getByTestId("columna-11")).toHaveTextContent("60.0%");
    expect(screen.getByTestId("columna-11").className).toContain("ganador");
    expect(screen.getByTestId("columna-10").className).toContain("atenuado");
  });

  it("los datos de ensayo suman el total y respetan el orden de la papeleta", () => {
    const datos = datosEnsayo("X", 1, [opciones[1], opciones[0]], 299);
    expect(datos.candidatos.map((c) => c.id)).toEqual([10, 11]);
    expect(datos.candidatos.reduce((s, c) => s + c.votos, 0)).toBe(datos.totalVotos);
    expect(datos.ensayo).toBe(true);
  });
});
