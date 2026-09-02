import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { PadronListado } from "../api/padron";
import { PadronPage } from "../routes/PadronPage";

function listado(overrides: Partial<PadronListado> = {}): PadronListado {
  return {
    total: 1,
    pagina: 1,
    tamanio_pagina: 50,
    items: [
      {
        id: 1,
        nombres: "Juan",
        apellidos: "Pereira",
        documento: "1234567",
        celular: "0981111111",
        estado: "ACTIVA",
        grupo_id: 1,
        circulo: "CIRCULO A",
        es_jefe_grupo: false,
        matrimonio_id: 1,
        matrimonio_estado: null,
        es_consagrado: true,
        unidades_electorales: [{ id: 1, tipo: "MATRIMONIO_CONSAGRADO", estado: "HABILITADA" }],
      },
    ],
    ...overrides,
  };
}

function respuestaJson(body: unknown) {
  return { ok: true, status: 200, json: async () => body } as Response;
}

/**
 * Visor de padron (Mision 12, DEC-031): filtros que arman la query string de
 * `GET /padron/personas`, tabla con los datos devueltos y paginacion.
 * Verifica ademas que la tabla no muestra ni pide ningun dato de voto (la
 * exclusion deliberada de `Voto` de DEC-031).
 */
describe("PadronPage", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("carga el listado al montar y muestra la tabla", async () => {
    const fetchMock = vi.fn().mockResolvedValue(respuestaJson(listado()));
    vi.stubGlobal("fetch", fetchMock);

    render(<PadronPage />);

    await waitFor(() => expect(screen.getByText("Pereira, Juan")).toBeInTheDocument());
    expect(screen.getByText("1234567")).toBeInTheDocument();
    expect(screen.getByText(/MATRIMONIO_CONSAGRADO \(HABILITADA\)/)).toBeInTheDocument();

    const [path] = fetchMock.mock.calls[0];
    expect(String(path)).toContain("/padron/personas");
  });

  it("filtrar por círculo arma la query string y reinicia a la página 1", async () => {
    const fetchMock = vi.fn().mockResolvedValue(respuestaJson(listado()));
    vi.stubGlobal("fetch", fetchMock);
    const usuario = userEvent.setup();

    render(<PadronPage />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));

    await usuario.type(screen.getByLabelText("Filtrar por círculo"), "CIRCULO A");

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1 + "CIRCULO A".length));
    const ultimaLlamada = fetchMock.mock.calls[fetchMock.mock.calls.length - 1][0] as string;
    expect(ultimaLlamada).toContain("circulo=CIRCULO");
    expect(ultimaLlamada).toContain("pagina=1");
  });

  it("nunca pide ni muestra datos de voto", async () => {
    const fetchMock = vi.fn().mockResolvedValue(respuestaJson(listado()));
    vi.stubGlobal("fetch", fetchMock);

    render(<PadronPage />);
    await waitFor(() => expect(screen.getByText("Pereira, Juan")).toBeInTheDocument());

    const [path] = fetchMock.mock.calls[0];
    expect(String(path).toLowerCase()).not.toContain("voto");
    expect(document.body.textContent?.toLowerCase()).not.toContain("opción votada");
  });

  it("la paginación pide la página siguiente con el mismo tamaño de página", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      respuestaJson(listado({ total: 120, pagina: 1 })),
    );
    vi.stubGlobal("fetch", fetchMock);
    const usuario = userEvent.setup();

    render(<PadronPage />);
    await waitFor(() => expect(screen.getByText(/Página 1 de 3/)).toBeInTheDocument());

    await usuario.click(screen.getByRole("button", { name: "Siguiente" }));

    await waitFor(() => {
      const ultimaLlamada = fetchMock.mock.calls[fetchMock.mock.calls.length - 1][0] as string;
      expect(ultimaLlamada).toContain("pagina=2");
      expect(ultimaLlamada).toContain("tamanio_pagina=50");
    });
  });
});
