import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "../api/client";
import * as habilitacionApi from "../api/habilitacion";
import { ConsultaCelularForm } from "./ConsultaCelularForm";

vi.mock("../api/habilitacion");

describe("ConsultaCelularForm", () => {
  it("no llama a la API y muestra un error si el celular es invalido", async () => {
    const user = userEvent.setup();
    const onResultado = vi.fn();
    const consultarHabilitacion = vi.mocked(habilitacionApi.consultarHabilitacion);

    render(<ConsultaCelularForm onResultado={onResultado} />);

    await user.type(screen.getByRole("textbox"), "123");
    await user.click(screen.getByRole("button", { name: /consultar/i }));

    expect(screen.getByText(/ingresá un número de celular válido/i)).toBeInTheDocument();
    expect(consultarHabilitacion).not.toHaveBeenCalled();
    expect(onResultado).not.toHaveBeenCalled();
  });

  it("muestra el estado de carga mientras espera la respuesta", async () => {
    const user = userEvent.setup();
    let resolver: (value: habilitacionApi.HabilitacionConsultaResponse) => void = () => {};
    vi.mocked(habilitacionApi.consultarHabilitacion).mockReturnValue(
      new Promise((resolve) => {
        resolver = resolve;
      }),
    );

    render(<ConsultaCelularForm onResultado={vi.fn()} />);

    await user.type(screen.getByRole("textbox"), "0981000001");
    await user.click(screen.getByRole("button", { name: /consultar/i }));

    expect(screen.getByText(/consultando/i)).toBeInTheDocument();

    resolver({ celular_normalizado: "0981000001", habilitado: false, personas: [], unidades: [] });
  });

  it("muestra un mensaje de sin conexion cuando la API no responde", async () => {
    const user = userEvent.setup();
    vi.mocked(habilitacionApi.consultarHabilitacion).mockRejectedValue(
      new ApiError("No se pudo conectar con la API."),
    );

    render(<ConsultaCelularForm onResultado={vi.fn()} />);

    await user.type(screen.getByRole("textbox"), "0981000001");
    await user.click(screen.getByRole("button", { name: /consultar/i }));

    expect(await screen.findByText(/sin conexión/i)).toBeInTheDocument();
  });

  it("llama a onResultado con la respuesta y el celular consultado", async () => {
    const user = userEvent.setup();
    const onResultado = vi.fn();
    const respuesta: habilitacionApi.HabilitacionConsultaResponse = {
      celular_normalizado: "0981000001",
      habilitado: true,
      personas: [{ persona_id: 1, nombres: "Ana", apellidos: "Gomez" }],
      unidades: [],
    };
    vi.mocked(habilitacionApi.consultarHabilitacion).mockResolvedValue(respuesta);

    render(<ConsultaCelularForm onResultado={onResultado} />);

    await user.type(screen.getByRole("textbox"), "0981000001");
    await user.click(screen.getByRole("button", { name: /consultar/i }));

    expect(onResultado).toHaveBeenCalledWith(respuesta, "0981000001");
  });
});
