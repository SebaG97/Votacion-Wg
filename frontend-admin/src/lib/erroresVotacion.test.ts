import { describe, expect, it } from "vitest";

import { ApiError } from "../api/client";
import { traducirErrorVotacion } from "./erroresVotacion";

function conflicto(detail: string, status = 409): ApiError {
  return new ApiError("La API respondio con error.", status, detail);
}

describe("traducirErrorVotacion", () => {
  it("clasifica OtraVotacionAbiertaError", () => {
    expect(
      traducirErrorVotacion(conflicto("Ya existe otra votacion ABIERTA (id=2): no se puede abrir una segunda.")),
    ).toMatch(/ya hay otra votación abierta/i);
  });

  it("clasifica VotacionSinOpcionesError", () => {
    expect(
      traducirErrorVotacion(
        conflicto("La votacion 1 no tiene ninguna opcion cargada: no se puede abrir."),
      ),
    ).toMatch(/cargá al menos una opción/i);
  });

  it("clasifica VotacionNoEsBorradorError al agregar opciones", () => {
    expect(
      traducirErrorVotacion(
        conflicto("La votacion 1 ya no esta en BORRADOR (estado actual 'ABIERTA'): no se pueden agregar ni editar opciones."),
      ),
    ).toMatch(/ya salió de borrador/i);
  });

  it("clasifica VotacionNoEsBorradorError al abrir", () => {
    expect(
      traducirErrorVotacion(
        conflicto("La votacion 1 no esta en BORRADOR (estado actual 'ABIERTA'): no se puede abrir."),
      ),
    ).toMatch(/ya salió de borrador/i);
  });

  it("clasifica VotacionNoAbiertaError", () => {
    expect(
      traducirErrorVotacion(
        conflicto("La votacion 1 no esta ABIERTA (estado actual 'CERRADA'): no se puede cerrar."),
      ),
    ).toMatch(/no está abierta/i);
  });

  it("clasifica VotacionNoCerradaError", () => {
    expect(
      traducirErrorVotacion(
        conflicto("La votacion 1 no esta CERRADA (estado actual 'ABIERTA'): no se pueden revelar resultados."),
      ),
    ).toMatch(/no está cerrada/i);
  });

  it("clasifica ResultadosYaReveladosError", () => {
    expect(
      traducirErrorVotacion(conflicto("La votacion 1 ya fueron revelados el 2026-09-01 10:00:00.")),
    ).toMatch(/ya fueron revelados/i);
  });

  it("clasifica ResultadosBloqueadosError", () => {
    expect(
      traducirErrorVotacion(conflicto("Resultados bloqueados hasta el cierre (estado actual 'ABIERTA').")),
    ).toMatch(/bloqueados hasta el cierre/i);
  });

  it("clasifica ImportacionRechazadaError", () => {
    expect(
      traducirErrorVotacion(
        conflicto(
          "La votacion 1 ('Consejo') esta en estado ABIERTA: no se puede reimportar el padron mientras haya una votacion abierta o cerrada.",
        ),
      ),
    ).toMatch(/no se puede reimportar/i);
  });

  it("clasifica IncidenciaYaResueltaError", () => {
    expect(
      traducirErrorVotacion(conflicto("La incidencia 5 ya fue resuelta por 'admin' el 2026-09-01.")),
    ).toMatch(/ya había sido marcada como revisada/i);
  });

  it("clasifica un 404 generico de 'no existe'", () => {
    expect(traducirErrorVotacion(conflicto("La votacion 999 no existe.", 404))).toMatch(
      /no se encontró/i,
    );
  });

  it("delega en mensajeDeError para un error sin status (sin conexion)", () => {
    expect(traducirErrorVotacion(new ApiError("No se pudo conectar con la API."))).toMatch(
      /sin conexión/i,
    );
  });

  it("delega en mensajeDeError para un error que no es ApiError", () => {
    expect(traducirErrorVotacion(new Error("boom"))).toMatch(/ocurrió un error inesperado/i);
  });
});
