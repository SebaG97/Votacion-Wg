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

async function ejecutar<TResponse>(path: string, init?: RequestInit): Promise<TResponse> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, init);
  } catch {
    // fetch rechaza por falla de red (sin conexion, DNS, CORS bloqueado):
    // sin `status`, para que el llamador lo distinga de un error HTTP real.
    throw new ApiError("No se pudo conectar con la API.");
  }

  if (!response.ok) {
    const detail = await detalleDeError(response);
    throw new ApiError("La API respondio con error.", response.status, detail);
  }

  return response.json() as Promise<TResponse>;
}

export function apiGet<TResponse>(path: string): Promise<TResponse> {
  return ejecutar<TResponse>(path);
}

export function apiPost<TResponse, TBody = unknown>(
  path: string,
  body: TBody,
): Promise<TResponse> {
  return ejecutar<TResponse>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
