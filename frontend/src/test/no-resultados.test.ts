import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * REGLAS_NEGOCIO.md prohibe mostrar resultados por opcion antes del cierre,
 * y este frontend de votacion (Mision 09) no tiene forma de saber si la
 * votacion ya cerro. Ninguna pantalla de esta mision debe llamar a
 * `GET /resultados` ni a `POST /revelar` (eso es del panel administrativo,
 * Mision 10).
 */
function listarArchivosFuente(dir: string): string[] {
  const archivos: string[] = [];
  for (const entrada of readdirSync(dir)) {
    if (entrada === "test") continue;
    const ruta = join(dir, entrada);
    const info = statSync(ruta);
    if (info.isDirectory()) {
      archivos.push(...listarArchivosFuente(ruta));
    } else if (/\.(ts|tsx)$/.test(entrada)) {
      archivos.push(ruta);
    }
  }
  return archivos;
}

describe("frontend de votacion no referencia resultados", () => {
  it("ningun archivo de src/ menciona /resultados ni /revelar", () => {
    const raiz = join(__dirname, "..");
    const archivos = listarArchivosFuente(raiz);
    expect(archivos.length).toBeGreaterThan(0);

    const ofensores = archivos.filter((archivo) => {
      const contenido = readFileSync(archivo, "utf-8");
      return contenido.includes("/resultados") || contenido.includes("/revelar");
    });

    expect(ofensores).toEqual([]);
  });
});
