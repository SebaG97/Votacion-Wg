import { describe, expect, it } from "vitest";

import { etiquetaUnidad, traducirMotivoNoDisponible } from "./motivos";

describe("traducirMotivoNoDisponible", () => {
  it("traduce BLOQUEADA_POR_INCIDENCIA a lenguaje claro", () => {
    expect(traducirMotivoNoDisponible("BLOQUEADA_POR_INCIDENCIA")).toBe(
      "Hay un problema con tus datos, contactá al administrador.",
    );
  });

  it("traduce YA_VOTADO a lenguaje claro", () => {
    expect(traducirMotivoNoDisponible("YA_VOTADO")).toBe("Esta unidad ya emitió su voto.");
  });

  it("traduce PENDIENTE_DEFINICION_POSTULANTES y PENDIENTE_DEFINICION_BAJA al mismo mensaje", () => {
    expect(traducirMotivoNoDisponible("PENDIENTE_DEFINICION_POSTULANTES")).toBe(
      "Todavía no está habilitada para votar.",
    );
    expect(traducirMotivoNoDisponible("PENDIENTE_DEFINICION_BAJA")).toBe(
      "Todavía no está habilitada para votar.",
    );
  });

  it("nunca devuelve el codigo tecnico crudo", () => {
    const motivos = [
      "BLOQUEADA_POR_INCIDENCIA",
      "YA_VOTADO",
      "PENDIENTE_DEFINICION_POSTULANTES",
      "PENDIENTE_DEFINICION_BAJA",
      null,
    ];
    for (const motivo of motivos) {
      expect(traducirMotivoNoDisponible(motivo)).not.toBe(motivo);
    }
  });
});

describe("etiquetaUnidad", () => {
  it("etiqueta el matrimonio consagrado", () => {
    expect(etiquetaUnidad("MATRIMONIO_CONSAGRADO")).toBe("Votar por tu matrimonio consagrado");
  });

  it("etiqueta el bloque no consagrado", () => {
    expect(etiquetaUnidad("BLOQUE_NO_CONSAGRADO")).toBe("Votar por el bloque de tu círculo");
  });
});
