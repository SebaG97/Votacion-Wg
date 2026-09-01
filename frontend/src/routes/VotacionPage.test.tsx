import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import * as habilitacionApi from "../api/habilitacion";
import * as votacionApi from "../api/votacion";
import { VotacionPage } from "./VotacionPage";

vi.mock("../api/habilitacion");
vi.mock("../api/votacion");

describe("VotacionPage", () => {
  it("recorre el flujo completo: consulta, eleccion de unidad, opcion y confirmacion", async () => {
    const user = userEvent.setup();

    vi.mocked(habilitacionApi.consultarHabilitacion).mockResolvedValue({
      celular_normalizado: "0981000001",
      habilitado: true,
      personas: [{ persona_id: 1, nombres: "Ana", apellidos: "Gomez" }],
      unidades: [
        {
          unidad_electoral_id: 7,
          tipo: "MATRIMONIO_CONSAGRADO",
          descripcion: null,
          estado: "HABILITADA",
          disponible: true,
          motivo_no_disponible: null,
          incidencias: [],
        },
      ],
    });
    vi.mocked(votacionApi.getVotacionAbierta).mockResolvedValue({
      votacion_id: 1,
      nombre: "Consejo 2026",
      opciones: [{ id: 10, nombre: "Lista A", orden: 1 }],
    });
    vi.mocked(votacionApi.registrarVoto).mockResolvedValue({
      id: 1,
      votacion_id: 1,
      unidad_electoral_id: 7,
      opcion_id: 10,
      emitido_por_persona_id: 1,
      celular_consultado: "0981000001",
      fecha_emision: "2026-09-01T12:00:00",
      canal: null,
    });

    render(<VotacionPage />);

    await user.type(screen.getByRole("textbox"), "0981000001");
    await user.click(screen.getByRole("button", { name: /consultar/i }));

    const votarUnidad = await screen.findByRole("button", {
      name: /votar por tu matrimonio consagrado/i,
    });
    await user.click(votarUnidad);

    await user.click(await screen.findByText("Lista A"));
    await user.click(screen.getByRole("button", { name: /confirmar voto/i }));

    expect(await screen.findByText(/tu voto se registró correctamente/i)).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(votacionApi.registrarVoto).toHaveBeenCalledWith(1, {
      celular_consultado: "0981000001",
      unidad_electoral_id: 7,
      opcion_id: 10,
      emitido_por_persona_id: 1,
    });
  });

  it("muestra el 409 de voto duplicado como 'tu voto ya fue registrado'", async () => {
    const user = userEvent.setup();

    vi.mocked(habilitacionApi.consultarHabilitacion).mockResolvedValue({
      celular_normalizado: "0981000001",
      habilitado: true,
      personas: [{ persona_id: 1, nombres: "Ana", apellidos: "Gomez" }],
      unidades: [
        {
          unidad_electoral_id: 7,
          tipo: "MATRIMONIO_CONSAGRADO",
          descripcion: null,
          estado: "HABILITADA",
          disponible: true,
          motivo_no_disponible: null,
          incidencias: [],
        },
      ],
    });
    vi.mocked(votacionApi.getVotacionAbierta).mockResolvedValue({
      votacion_id: 1,
      nombre: "Consejo 2026",
      opciones: [{ id: 10, nombre: "Lista A", orden: 1 }],
    });
    const { ApiError } = await import("../api/client");
    vi.mocked(votacionApi.registrarVoto).mockRejectedValue(
      new ApiError("La API respondio con error.", 409, "Ya existe un voto registrado."),
    );

    render(<VotacionPage />);

    await user.type(screen.getByRole("textbox"), "0981000001");
    await user.click(screen.getByRole("button", { name: /consultar/i }));
    await user.click(
      await screen.findByRole("button", { name: /votar por tu matrimonio consagrado/i }),
    );
    await user.click(await screen.findByText("Lista A"));
    await user.click(screen.getByRole("button", { name: /confirmar voto/i }));

    expect(await screen.findByText(/tu voto ya fue registrado/i)).toBeInTheDocument();
  });
});
