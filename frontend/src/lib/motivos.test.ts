import { describe, expect, it } from "vitest";

import { etiquetaUnidad, traducirMotivoNoDisponible } from "./motivos";

describe("traducirMotivoNoDisponible", () => {
  it("traduce BLOQUEADA_POR_INCIDENCIA a lenguaje claro", () => {
    expect(traducirMotivoNoDisponible("BLOQUEADA_POR_INCIDENCIA")).toBe(
      "Hay un problema con tus datos, contactá al administrador.",
    );
  });

  it("traduce CELULAR_DUPLICADO a lenguaje claro (DEC-039)", () => {
    expect(traducirMotivoNoDisponible("CELULAR_DUPLICADO")).toContain(
      "más de un matrimonio",
    );
  });

  it("traduce YA_VOTADO a lenguaje claro", () => {
    expect(traducirMotivoNoDisponible("YA_VOTADO")).toBe(
      "Esta unidad ya emitió su voto.",
    );
  });

  it("traduce PENDIENTE_DEFINICION_POSTULANTES y PENDIENTE_DEFINICION_BAJA al mismo mensaje", () => {
    expect(traducirMotivoNoDisponible("PENDIENTE_DEFINICION_POSTULANTES")).toBe(
      "Esta unidad no tiene voto habilitado en esta elección.",
    );
    expect(traducirMotivoNoDisponible("PENDIENTE_DEFINICION_BAJA")).toBe(
      "Esta unidad no tiene voto habilitado en esta elección.",
    );
  });

  it("nunca devuelve el codigo tecnico crudo", () => {
    const motivos = [
      "BLOQUEADA_POR_INCIDENCIA",
      "CELULAR_DUPLICADO",
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
    expect(etiquetaUnidad("MATRIMONIO_CONSAGRADO")).toBe(
      "Votar por tu matrimonio",
    );
  });

  it("etiqueta el bloque no consagrado", () => {
    expect(etiquetaUnidad("BLOQUE_NO_CONSAGRADO")).toBe(
      "Votar por el bloque de tu círculo",
    );
  });

  it("nombra el circulo del bloque cuando viene en la descripcion (DEC-042)", () => {
    expect(
      etiquetaUnidad(
        "BLOQUE_NO_CONSAGRADO",
        'Bloque no consagrado de POSTULANTES 2024  "F"',
      ),
    ).toBe('Votar por el bloque de POSTULANTES 2024  "F"');
  });
});
