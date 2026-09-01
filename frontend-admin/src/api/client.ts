import { notificarNoAutorizado, obtenerAdminToken } from "./adminToken";

const defaultApiBaseUrl = "http://localhost:8000/api/v1";

export const apiBaseUrl =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? defaultApiBaseUrl;

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
    public readonly detail?: string,
  ) {
    super(message);
  }
}

async function detalleDeError(response: Response): Promise<string | undefined> {
  try {
    const cuerpo = await response.json();
    if (cuerpo && typeof cuerpo.detail === "string") {
      return cuerpo.detail;
    }
  } catch {
    // El cuerpo no es JSON o esta vacio: no hay detalle que extraer.
  }
  return undefined;
}

/**
 * Todo request administrativo pasa por aca: agrega `X-Admin-Token` con el
 * valor guardado por `adminToken.ts`, y ante un `401`/`403` real del backend
 * dispara `notificarNoAutorizado()` -- `AuthContext` lo escucha para volver a
 * la pantalla de login y limpiar el token guardado, sin que quede cacheado
 * un token invalido reintentando en loop.
 */
async function ejecutar<TResponse>(path: string, init?: RequestInit): Promise<TResponse> {
  const token = obtenerAdminToken();
  const headers: Record<string, string> = {
    ...(init?.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers["X-Admin-Token"] = token;
  }

  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, { ...init, headers });
  } catch {
    throw new ApiError("No se pudo conectar con la API.");
  }

  if (!response.ok) {
    const detail = await detalleDeError(response);
    if (response.status === 401 || response.status === 403) {
      notificarNoAutorizado();
    }
    throw new ApiError("La API respondio con error.", response.status, detail);
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }
  return response.json() as Promise<TResponse>;
}

export function apiGet<TResponse>(path: string): Promise<TResponse> {
  return ejecutar<TResponse>(path);
}

export function apiPost<TResponse, TBody = unknown>(
  path: string,
  body?: TBody,
): Promise<TResponse> {
  return ejecutar<TResponse>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}
