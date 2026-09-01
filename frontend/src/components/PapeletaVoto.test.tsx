import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { PersonaConsultada, UnidadElectoralDisponible } from "../api/habilitacion";
import { ApiError } from "../api/client";
import * as votacionApi from "../api/votacion";
import { PapeletaVoto } from "./PapeletaVoto";

vi.mock("../api/votacion");

const unidad: UnidadElectoralDisponible = {
  unidad_electoral_id: 7,
  tipo: "MATRIMONIO_CONSAGRADO",
  descripcion: null,
  estado: "HABILITADA",
  disponible: true,
  motivo_no_disponible: null,
  incidencias: [],
};

const papeleta: votacionApi.VotacionAbierta = {
  votacion_id: 1,
  nombre: "Consejo 2026",
  opciones: [
    { id: 10, nombre: "Lista A", orden: 1 },
    { id: 11, nombre: "Lista B", orden: 2 },
  ],
};

function personas(n: number): PersonaConsultada[] {
  const todas = [
    { persona_id: 1, nombres: "Ana", apellidos: "Gomez" },
    { persona_id: 2, nombres: "Luis", apellidos: "Gomez" },
  ];
  return todas.slice(0, n);
}

beforeEach(() => {
  vi.mocked(votacionApi.getVotacionAbierta).mockResolvedValue(papeleta);
});

describe("PapeletaVoto", () => {
  it("pide confirmar la persona cuando el celular es compartido entre conyuges", async () => {
    render(
      <PapeletaVoto
        unidad={unidad}
        personas={personas(2)}
        celularConsultado="0981000001"
        onVotoRegistrado={vi.fn()}
        onYaVotado={vi.fn()}
      />,
    );

    expect(
      screen.getByText(/quién de estas personas está emitiendo el voto/i),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ana Gomez" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Luis Gomez" })).toBeInTheDocument();
    expect(screen.queryByText("Lista A")).not.toBeInTheDocument();
  });

  it("no pide confirmar persona cuando hay una sola", async () => {
    render(
      <PapeletaVoto
        unidad={unidad}
        personas={personas(1)}
        celularConsultado="0981000001"
        onVotoRegistrado={vi.fn()}
        onYaVotado={vi.fn()}
      />,
    );

    expect(
      screen.queryByText(/quién de estas personas está emitiendo el voto/i),
    ).not.toBeInTheDocument();
    expect(await screen.findByText("Lista A")).toBeInTheDocument();
  });

  it("registra el voto exitoso y deshabilita el boton para evitar doble submit", async () => {
    const user = userEvent.setup();
    const onVotoRegistrado = vi.fn();
    let resolver: (value: votacionApi.VotoResponse) => void = () => {};
    vi.mocked(votacionApi.registrarVoto).mockReturnValue(
      new Promise((resolve) => {
        resolver = resolve;
      }),
    );

    render(
      <PapeletaVoto
        unidad={unidad}
        personas={personas(1)}
        celularConsultado="0981000001"
        onVotoRegistrado={onVotoRegistrado}
        onYaVotado={vi.fn()}
      />,
    );

    await user.click(await screen.findByText("Lista A"));
    const confirmar = screen.getByRole("button", { name: /confirmar voto/i });
    await user.click(confirmar);

    expect(confirmar).toBeDisabled();

    resolver({
      id: 1,
      votacion_id: 1,
      unidad_electoral_id: 7,
      opcion_id: 10,
      emitido_por_persona_id: 1,
      celular_consultado: "0981000001",
      fecha_emision: "2026-09-01T12:00:00",
      canal: null,
    });

    await waitFor(() => expect(onVotoRegistrado).toHaveBeenCalledTimes(1));
    expect(votacionApi.registrarVoto).toHaveBeenCalledTimes(1);
  });

  it("muestra el 409 de voto duplicado como mensaje amigable, delegando al padre", async () => {
    const user = userEvent.setup();
    const onYaVotado = vi.fn();
    vi.mocked(votacionApi.registrarVoto).mockRejectedValue(
      new ApiError("La API respondio con error.", 409, "Ya existe un voto registrado."),
    );

    render(
      <PapeletaVoto
        unidad={unidad}
        personas={personas(1)}
        celularConsultado="0981000001"
        onVotoRegistrado={vi.fn()}
        onYaVotado={onYaVotado}
      />,
    );

    await user.click(await screen.findByText("Lista A"));
    await user.click(screen.getByRole("button", { name: /confirmar voto/i }));

    await waitFor(() => expect(onYaVotado).toHaveBeenCalledTimes(1));
  });

  it("un 409 porque la votacion ya no esta disponible NO dispara 'ya votado'", async () => {
    const user = userEvent.setup();
    const onYaVotado = vi.fn();
    vi.mocked(votacionApi.registrarVoto).mockRejectedValue(
      new ApiError(
        "La API respondio con error.",
        409,
        "La votacion 1 no existe o no esta en estado ABIERTA.",
      ),
    );

    render(
      <PapeletaVoto
        unidad={unidad}
        personas={personas(1)}
        celularConsultado="0981000001"
        onVotoRegistrado={vi.fn()}
        onYaVotado={onYaVotado}
      />,
    );

    await user.click(await screen.findByText("Lista A"));
    await user.click(screen.getByRole("button", { name: /confirmar voto/i }));

    expect(await screen.findByText(/la votación ya no está disponible/i)).toBeInTheDocument();
    expect(onYaVotado).not.toHaveBeenCalled();
  });

  it("un 409 porque la unidad electoral ya no esta disponible NO dispara 'ya votado'", async () => {
    const user = userEvent.setup();
    const onYaVotado = vi.fn();
    vi.mocked(votacionApi.registrarVoto).mockRejectedValue(
      new ApiError(
        "La API respondio con error.",
        409,
        "La unidad electoral no esta disponible para votar: estado actual 'BLOQUEADA_POR_INCIDENCIA'.",
      ),
    );

    render(
      <PapeletaVoto
        unidad={unidad}
        personas={personas(1)}
        celularConsultado="0981000001"
        onVotoRegistrado={vi.fn()}
        onYaVotado={onYaVotado}
      />,
    );

    await user.click(await screen.findByText("Lista A"));
    await user.click(screen.getByRole("button", { name: /confirmar voto/i }));

    expect(
      await screen.findByText(/esta unidad electoral ya no está disponible para votar/i),
    ).toBeInTheDocument();
    expect(onYaVotado).not.toHaveBeenCalled();
  });

  it("si la persona elegida no esta autorizada, deja elegir a la otra persona de la lista", async () => {
    const user = userEvent.setup();
    vi.mocked(votacionApi.registrarVoto).mockRejectedValue(
      new ApiError(
        "La API respondio con error.",
        400,
        "La persona emisora no esta autorizada para votar por esta unidad electoral.",
      ),
    );

    render(
      <PapeletaVoto
        unidad={unidad}
        personas={personas(2)}
        celularConsultado="0981000001"
        onVotoRegistrado={vi.fn()}
        onYaVotado={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Ana Gomez" }));
    await user.click(await screen.findByText("Lista A"));
    await user.click(screen.getByRole("button", { name: /confirmar voto/i }));

    expect(
      await screen.findByText(/no está autorizada para emitir este voto/i),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ana Gomez" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Luis Gomez" })).toBeInTheDocument();
  });
});
