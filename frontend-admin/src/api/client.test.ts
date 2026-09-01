import { afterEach, describe, expect, it, vi } from "vitest";

import { guardarAdminToken, setEscuchaNoAutorizado } from "./adminToken";
import { apiGet, ApiError } from "./client";

function respuestaFalsa(status: number, detail?: string) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => (detail === undefined ? {} : { detail }),
  } as Response;
}

/**
 * `require_admin` (backend, DEC-021) devuelve 401 con token ausente/incorrecto
 * y 403 cuando `ADMIN_API_KEY` no esta configurado (falla cerrado). Un 401/403
 * real de cualquier endpoint administrativo debe limpiar el token guardado y
 * avisarle a `AuthContext` (via `notificarNoAutorizado`) para volver a la
 * pantalla de login -- nunca debe quedar un token invalido reintentando en
 * loop.
 */
describe("client: un 401/403 real dispara el escucha de no autorizado", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    setEscuchaNoAutorizado(null);
    guardarAdminToken(null);
  });

  it.each([401, 403])("status %i dispara la notificacion", async (status) => {
    guardarAdminToken("token-invalido");
    const escucha = vi.fn();
    setEscuchaNoAutorizado(escucha);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(respuestaFalsa(status, "Token administrativo invalido o ausente.")),
    );

    await expect(apiGet("/votaciones")).rejects.toBeInstanceOf(ApiError);
    expect(escucha).toHaveBeenCalledTimes(1);
  });

  it("un 404 real NO dispara la notificacion de no autorizado", async () => {
    guardarAdminToken("token-cualquiera");
    const escucha = vi.fn();
    setEscuchaNoAutorizado(escucha);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(respuestaFalsa(404, "La votacion 1 no existe.")));

    await expect(apiGet("/votaciones/1/estado")).rejects.toBeInstanceOf(ApiError);
    expect(escucha).not.toHaveBeenCalled();
  });

  it("un error de red (sin status) NO dispara la notificacion de no autorizado", async () => {
    guardarAdminToken("token-cualquiera");
    const escucha = vi.fn();
    setEscuchaNoAutorizado(escucha);
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network down")));

    await expect(apiGet("/votaciones")).rejects.toBeInstanceOf(ApiError);
    expect(escucha).not.toHaveBeenCalled();
  });

  it("manda el token guardado como header X-Admin-Token", async () => {
    guardarAdminToken("mi-token");
    const fetchMock = vi.fn().mockResolvedValue(respuestaFalsa(200, undefined));
    vi.stubGlobal("fetch", fetchMock);

    await apiGet("/votaciones");

    const [, init] = fetchMock.mock.calls[0];
    expect((init.headers as Record<string, string>)["X-Admin-Token"]).toBe("mi-token");
  });
});
