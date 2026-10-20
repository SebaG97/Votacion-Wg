import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as votacionesApi from "../api/votaciones";
import type { Opcion } from "../api/votaciones";
import { OpcionFotoEditor } from "../components/OpcionFotoEditor";
import * as redimensionar from "../lib/redimensionarImagen";

vi.mock("../api/votaciones");
vi.mock("../lib/redimensionarImagen");

function opcion(tieneFoto: boolean): Opcion {
  return { id: 7, votacion_id: 3, nombre: "Matrimonio A", orden: null, tiene_foto: tieneFoto };
}

/** Foto del candidato (Mision 15, DEC-037). */
describe("OpcionFotoEditor", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(votacionesApi.urlFotoOpcion).mockReturnValue("/foto.jpg");
  });

  it("sin foto ofrece subirla y no muestra Quitar", () => {
    render(<OpcionFotoEditor opcion={opcion(false)} onCambio={() => {}} />);

    expect(screen.getByText("Subir foto")).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.queryByText("Quitar")).not.toBeInTheDocument();
  });

  it("achica la imagen, la sube y avisa el cambio", async () => {
    const achicada = new Blob(["x"], { type: "image/jpeg" });
    vi.mocked(redimensionar.redimensionarImagen).mockResolvedValue(achicada);
    vi.mocked(votacionesApi.subirFotoOpcion).mockResolvedValue(opcion(true));
    const onCambio = vi.fn();
    render(<OpcionFotoEditor opcion={opcion(false)} onCambio={onCambio} />);

    const archivo = new File(["foto"], "foto.png", { type: "image/png" });
    await userEvent.upload(screen.getByLabelText("Subir foto"), archivo);

    await waitFor(() => expect(onCambio).toHaveBeenCalledWith(opcion(true)));
    expect(redimensionar.redimensionarImagen).toHaveBeenCalledWith(archivo);
    expect(votacionesApi.subirFotoOpcion).toHaveBeenCalledWith(3, 7, achicada);
  });

  it("con foto la muestra y permite quitarla", async () => {
    vi.mocked(votacionesApi.quitarFotoOpcion).mockResolvedValue(opcion(false));
    const onCambio = vi.fn();
    render(<OpcionFotoEditor opcion={opcion(true)} onCambio={onCambio} />);

    expect(screen.getByRole("img", { name: "Foto de Matrimonio A" })).toHaveAttribute(
      "src",
      "/foto.jpg",
    );
    await userEvent.click(screen.getByRole("button", { name: /Quitar/ }));

    await waitFor(() => expect(onCambio).toHaveBeenCalledWith(opcion(false)));
  });

  it("si no puede leer la imagen muestra un error claro y no sube nada", async () => {
    vi.mocked(redimensionar.redimensionarImagen).mockRejectedValue(new Error("heic"));
    render(<OpcionFotoEditor opcion={opcion(false)} onCambio={() => {}} />);

    await userEvent.upload(
      screen.getByLabelText("Subir foto"),
      new File(["foto"], "foto.png", { type: "image/png" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo leer la imagen");
    expect(votacionesApi.subirFotoOpcion).not.toHaveBeenCalled();
  });
});
