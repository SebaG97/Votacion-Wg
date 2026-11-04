import { useEffect, useRef } from "react";

const COLORES = ["#fbbf24", "#f59e0b", "#fde68a", "#818cf8", "#a5b4fc", "#ffffff", "#f472b6", "#34d399"];

type Particula = {
  x: number;
  y: number;
  vx: number;
  vy: number;
  rot: number;
  vrot: number;
  ancho: number;
  alto: number;
  color: string;
};

/** Confeti en un canvas, sin librerias: dos rafagas desde abajo a los costados
 * y despues una lluvia suave desde arriba (presentacion en vivo, DEC-044). */
export function Confeti({ duracionMs = 9000 }: { duracionMs?: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext?.("2d");
    if (!canvas || !ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const ajustar = () => {
      canvas.width = window.innerWidth * dpr;
      canvas.height = window.innerHeight * dpr;
    };
    ajustar();
    window.addEventListener("resize", ajustar);

    const W = () => canvas.width;
    const H = () => canvas.height;
    const particulas: Particula[] = [];
    const nueva = (x: number, y: number, vx: number, vy: number): Particula => ({
      x,
      y,
      vx,
      vy,
      rot: Math.random() * Math.PI,
      vrot: (Math.random() - 0.5) * 0.3,
      ancho: (6 + Math.random() * 8) * dpr,
      alto: (10 + Math.random() * 10) * dpr,
      color: COLORES[Math.floor(Math.random() * COLORES.length)],
    });
    const rafaga = () => {
      for (let i = 0; i < 160; i++) {
        const izq = i % 2 === 0;
        particulas.push(
          nueva(
            izq ? 0 : W(),
            H() * 0.9,
            (izq ? 1 : -1) * (8 + Math.random() * 14) * dpr,
            -(14 + Math.random() * 16) * dpr,
          ),
        );
      }
    };
    rafaga();
    const segunda = window.setTimeout(rafaga, 700);

    const inicio = performance.now();
    let frame = 0;
    const dibujar = (ahora: number) => {
      const transcurrido = ahora - inicio;
      if (transcurrido < duracionMs - 2500 && Math.random() < 0.6) {
        particulas.push(nueva(Math.random() * W(), -20, (Math.random() - 0.5) * 2 * dpr, 2 * dpr));
      }
      ctx.clearRect(0, 0, W(), H());
      for (let i = particulas.length - 1; i >= 0; i--) {
        const p = particulas[i];
        p.vy += 0.35 * dpr;
        p.vx *= 0.985;
        p.vy = Math.min(p.vy, 6 * dpr);
        p.x += p.vx + Math.sin((ahora + i * 40) / 300) * 0.8 * dpr;
        p.y += p.vy;
        p.rot += p.vrot;
        if (p.y > H() + 40) {
          particulas.splice(i, 1);
          continue;
        }
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rot);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.ancho / 2, -p.alto / 2, p.ancho, Math.abs(Math.cos(p.rot * 2)) * p.alto + 2);
        ctx.restore();
      }
      if (transcurrido < duracionMs || particulas.length > 0) {
        frame = requestAnimationFrame(dibujar);
      }
    };
    frame = requestAnimationFrame(dibujar);

    return () => {
      cancelAnimationFrame(frame);
      window.clearTimeout(segunda);
      window.removeEventListener("resize", ajustar);
    };
  }, [duracionMs]);

  return <canvas ref={canvasRef} className="presentacion-confeti" aria-hidden="true" />;
}
