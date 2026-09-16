import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { PadronListado } from "../api/padron";
import { OperadorProvider } from "../context/OperadorContext";
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

function respuestaJson(status: number, body: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

function renderPadron() {
  return render(
    <OperadorProvider>
      <PadronPage />
    </OperadorProvider>,
  );
}

async function abrirFormularioEdicion() {
  const usuario = userEvent.setup();
  renderPadron();
  await waitFor(() => expect(screen.getByText("Pereira, Juan")).toBeInTheDocument());
  await usuario.click(screen.getByRole("button", { name: "Editar" }));
  return usuario;
}

/**
 * Formulario de edicion de contacto del padron (Mision 13, DEC-034): nombres,
 * apellidos, documento, celular. `estado` y consagracion quedan de solo
 * lectura. El backend normaliza el celular y avisa (no bloqueante, 409 +
 * `confirmar_duplicado_celular`) si ya pertenece a otra persona de un
 * matrimonio distinto -- este archivo cubre esa clasificacion en el
 * frontend, sin volver a probar la logica de normalizacion (ya cubierta en
 * backend).
 */
describe("PersonaEditForm (dentro de PadronPage)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    try {
      sessionStorage.clear();
    } catch {
      // sessionStorage no disponible en este entorno: no hay nada que limpiar.
    }
  });

  it("estado y consagración se muestran como texto, nunca como input editable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(respuestaJson(200, listado())));
    await abrirFormularioEdicion();

    expect(screen.getByTestId("persona-estado-solo-lectura")).toHaveTextContent("ACTIVA");
    expect(screen.getByTestId("persona-consagrado-solo-lectura")).toHaveTextContent("Sí");
    expect(screen.queryByLabelText(/^estado$/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/consagrad/i)).not.toBeInTheDocument();
  });

  it("el botón guardar está deshabilitado sin nombre de operador cargado", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(respuestaJson(200, listado())));
    await abrirFormularioEdicion();

    expect(screen.getByRole("button", { name: /guardar/i })).toBeDisabled();
    expect(
      screen.getByText("Ingresá tu nombre de operador arriba para poder guardar."),
    ).toBeInTheDocument();
  });

  it("guardar manda PATCH con los 4 campos y el operador", async () => {
    sessionStorage.setItem("votacion-wg-admin-operador", "admin@wg");
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(respuestaJson(200, listado()))
      .mockResolvedValueOnce(
        respuestaJson(200, {
          persona: { ...listado().items[0], celular: "0981000002" },
          ediciones: [
            {
              id: 1,
              persona_id: 1,
              campo: "celular",
              valor_anterior: "0981111111",
              valor_nuevo: "0981000002",
              usuario: "admin@wg",
              fecha: "2026-09-16T00:00:00",
            },
          ],
        }),
      )
      .mockResolvedValueOnce(respuestaJson(200, listado()));
    vi.stubGlobal("fetch", fetchMock);

    const usuario = await abrirFormularioEdicion();

    const inputCelular = screen.getByLabelText("Celular");
    await usuario.clear(inputCelular);
    await usuario.type(inputCelular, "0981-000-002");

    await usuario.click(screen.getByRole("button", { name: /guardar/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    const [path, init] = fetchMock.mock.calls[1];
    expect(String(path)).toContain("/padron/personas/1");
    expect(init?.method).toBe("PATCH");
    const body = JSON.parse(String(init?.body));
    expect(body).toMatchObject({
      nombres: "Juan",
      apellidos: "Pereira",
      documento: "1234567",
      celular: "0981-000-002",
      usuario: "admin@wg",
      confirmar_duplicado_celular: false,
    });

    await waitFor(() => expect(screen.getByText(/actualizado\/a/)).toBeInTheDocument());
  });

  it("un 409 muestra el detalle del backend y permite confirmar y reenviar", async () => {
    sessionStorage.setItem("votacion-wg-admin-operador", "admin@wg");
    const detalleDuplicado =
      "El celular 0985555555 ya esta asignado a: Laura Benitez Rojas (persona 7) (matrimonio distinto). Confirme para guardar el cambio de todos modos.";
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(respuestaJson(200, listado()))
      .mockResolvedValueOnce(respuestaJson(409, { detail: detalleDuplicado }))
      .mockResolvedValueOnce(
        respuestaJson(200, {
          persona: { ...listado().items[0], celular: "0985555555" },
          ediciones: [],
        }),
      )
      .mockResolvedValueOnce(respuestaJson(200, listado()));
    vi.stubGlobal("fetch", fetchMock);

    const usuario = await abrirFormularioEdicion();

    const inputCelular = screen.getByLabelText("Celular");
    await usuario.clear(inputCelular);
    await usuario.type(inputCelular, "0985555555");
    await usuario.click(screen.getByRole("button", { name: /guardar/i }));

    await waitFor(() => expect(screen.getByText(detalleDuplicado)).toBeInTheDocument());

    await usuario.click(screen.getByRole("button", { name: /confirmar y guardar igual/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(4));
    const [, initConfirmado] = fetchMock.mock.calls[2];
    const bodyConfirmado = JSON.parse(String(initConfirmado?.body));
    expect(bodyConfirmado.confirmar_duplicado_celular).toBe(true);
  });
});
