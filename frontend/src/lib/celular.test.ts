import { describe, expect, it } from "vitest";

import { esCelularValido } from "./celular";

describe("esCelularValido", () => {
  it("acepta 10 digitos con cero inicial", () => {
    expect(esCelularValido("0981000001")).toBe(true);
  });

  it("acepta 9 digitos sin cero inicial", () => {
    expect(esCelularValido("981000001")).toBe(true);
  });

  it("acepta numeros con separadores", () => {
    expect(esCelularValido("0981 000 001")).toBe(true);
  });

  it("rechaza vacio", () => {
    expect(esCelularValido("")).toBe(false);
  });

  it("rechaza el placeholder de todos ceros", () => {
    expect(esCelularValido("0000000000")).toBe(false);
  });

  it("rechaza una cantidad de digitos invalida", () => {
    expect(esCelularValido("123")).toBe(false);
    expect(esCelularValido("12345678901")).toBe(false);
  });
});
