import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as padronApi from "../api/padron";
import * as votacionesApi from "../api/votaciones";
import type { EstadoVotacion, Votacion, VotacionEstado } from "../api/votaciones";
import { OperadorProvider } from "../context/OperadorContext";
import { VotacionDetailPage } from "../routes/VotacionDetailPage";

vi.mock("../api/votaciones");
vi.mock("../api/padron");

function votacion(estado: EstadoVotacion): Votacion {
  return {
    id: 1,
    nombre: "Consejo 2026",
    estado,
    fecha_apertura: null,
    fecha_cierre: null,
    abierta_por: null,
    cerrada_por: null,
    resultados_revelados_at: null,
  };
}

function estadoOperativo(estado: EstadoVotacion): VotacionEstado {
  return {
    votacion_id: 1,
    estado,
    unidades_por_estado: {
      habilitada: 0,
      bloqueada_por_incidencia: 0,
      pendiente_definicion_postulantes: 0,
      pendiente_definicion_baja: 0,
    },
    votos_emitidos: 0,
    pendientes: 0,
  };
}

function renderDetalle() {
  return render(
    <MemoryRouter initialEntries={["/votaciones/1"]}>
      <OperadorProvider>
        <Routes>
          <Route path="/votaciones/:id" element={<VotacionDetailPage />} />
        </Routes>
      </OperadorProvider>
    </MemoryRouter>,
  );
}

/**
 * REGLAS_NEGOCIO.md prohibe mostrar un desglose por opcion antes del cierre.
 * A diferencia del frontend de votacion (Mision 09, `no-resultados.test.ts`),
 * este panel SI tiene que llamar a `GET /resultados` y `POST /revelar` en
 * algun momento -- por eso el test no puede ser un grep estatico de "nunca
 * aparece la palabra resultados en el codigo". En cambio, verifica en tiempo
 * de ejecucion que esas dos llamadas nunca ocurren mientras la votacion no
 * esta CERRADA o RESULTADOS_REVELADOS, y que la vista de resultados ni
 * siquiera se monta (nunca oculta en el DOM).
 */
describe("los resultados finales solo se consultan con la votacion CERRADA o RESULTADOS_REVELADOS", () => {
  beforeEach(() => {
    vi.mocked(padronApi.listarImportaciones).mockResolvedValue([]);
    vi.mocked(votacionesApi.listarOpciones).mockResolvedValue([]);
  });

  it.each(["BORRADOR", "ABIERTA"] as const)(
    "con estado %s nunca llama a obtenerResultados ni a revelarResultados, y no monta la vista",
    async (estado) => {
      vi.mocked(votacionesApi.listarVotaciones).mockResolvedValue([votacion(estado)]);
      vi.mocked(votacionesApi.obtenerEstadoOperativo).mockResolvedValue(estadoOperativo(estado));

      renderDetalle();

      await screen.findByText("Estado operativo");

      expect(votacionesApi.obtenerResultados).not.toHaveBeenCalled();
      expect(votacionesApi.revelarResultados).not.toHaveBeenCalled();
      expect(screen.queryByText("Resultados finales")).not.toBeInTheDocument();
    },
  );

  it("con estado CERRADA si llama a obtenerResultados y muestra la vista", async () => {
    vi.mocked(votacionesApi.listarVotaciones).mockResolvedValue([votacion("CERRADA")]);
    vi.mocked(votacionesApi.obtenerEstadoOperativo).mockResolvedValue(estadoOperativo("CERRADA"));
    vi.mocked(votacionesApi.obtenerResultados).mockResolvedValue({
      votacion_id: 1,
      estado: "CERRADA",
      total_votos: 0,
      totales_por_opcion: [],
      totales_por_tipo_unidad: [],
      totales_por_grupo: [],
    });

    renderDetalle();

    await waitFor(() => expect(votacionesApi.obtenerResultados).toHaveBeenCalledTimes(1));
    expect(screen.getByText("Resultados finales")).toBeInTheDocument();
  });

  it("con estado RESULTADOS_REVELADOS si llama a obtenerResultados y no ofrece revelar de nuevo", async () => {
    vi.mocked(votacionesApi.listarVotaciones).mockResolvedValue([
      votacion("RESULTADOS_REVELADOS"),
    ]);
    vi.mocked(votacionesApi.obtenerEstadoOperativo).mockResolvedValue(
      estadoOperativo("RESULTADOS_REVELADOS"),
    );
    vi.mocked(votacionesApi.obtenerResultados).mockResolvedValue({
      votacion_id: 1,
      estado: "RESULTADOS_REVELADOS",
      total_votos: 0,
      totales_por_opcion: [],
      totales_por_tipo_unidad: [],
      totales_por_grupo: [],
    });

    renderDetalle();

    await waitFor(() => expect(votacionesApi.obtenerResultados).toHaveBeenCalledTimes(1));
    expect(screen.queryByRole("button", { name: /revelar resultados/i })).not.toBeInTheDocument();
  });
});
