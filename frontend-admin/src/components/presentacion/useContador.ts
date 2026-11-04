import { useEffect, useState } from "react";

export type Curva = "suave" | "lineal";

const curvas: Record<Curva, (t: number) => number> = {
  suave: (t) => 1 - Math.pow(1 - t, 3),
  lineal: (t) => t,
};

/**
 * Cuenta de 0 a `objetivo` en `duracionMs` (presentacion en vivo, DEC-044).
 * Con duracion 0 devuelve el valor final de entrada (sin animacion).
 */
export function useContador(
  objetivo: number,
  duracionMs: number,
  activo: boolean,
  decimales = 0,
  curva: Curva = "suave",
): number {
  const [valor, setValor] = useState(() => (duracionMs <= 0 ? objetivo : 0));

  useEffect(() => {
    if (!activo) return;
    if (duracionMs <= 0) {
      setValor(objetivo);
      return;
    }
    const factor = Math.pow(10, decimales);
    const inicio = performance.now();
    let frame = 0;
    const paso = (ahora: number) => {
      const t = Math.min(1, (ahora - inicio) / duracionMs);
      setValor(Math.round(curvas[curva](t) * objetivo * factor) / factor);
      if (t < 1) frame = requestAnimationFrame(paso);
    };
    frame = requestAnimationFrame(paso);
    return () => cancelAnimationFrame(frame);
  }, [objetivo, duracionMs, activo, decimales, curva]);

  return valor;
}
