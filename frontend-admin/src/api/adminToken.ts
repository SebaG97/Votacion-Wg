/**
 * Almacenamiento del token administrativo (`ADMIN_API_KEY`, DEC-021).
 *
 * Se guarda en `sessionStorage`, nunca en `localStorage` ni hardcodeado: dura
 * solo mientras la pestaña esta abierta, y desaparece al cerrarla. `client.ts`
 * lo manda como header `X-Admin-Token` en cada request administrativo, y
 * llama a `notificarNoAutorizado()` ante cualquier `401`/`403`, que
 * `AuthContext` usa para volver a la pantalla de login y limpiar el token.
 */

const CLAVE_STORAGE = "votacion-wg-admin-token";

let tokenEnMemoria: string | null | undefined;

export function obtenerAdminToken(): string | null {
  if (tokenEnMemoria === undefined) {
    try {
      tokenEnMemoria = sessionStorage.getItem(CLAVE_STORAGE);
    } catch {
      tokenEnMemoria = null;
    }
  }
  return tokenEnMemoria;
}

export function guardarAdminToken(token: string | null): void {
  tokenEnMemoria = token;
  try {
    if (token) {
      sessionStorage.setItem(CLAVE_STORAGE, token);
    } else {
      sessionStorage.removeItem(CLAVE_STORAGE);
    }
  } catch {
    // sessionStorage no disponible (modo privado estricto, etc.): el token
    // sigue viviendo en memoria para esta misma sesion de la pestaña.
  }
}

type Escucha = () => void;
let escuchaNoAutorizado: Escucha | null = null;

export function setEscuchaNoAutorizado(fn: Escucha | null): void {
  escuchaNoAutorizado = fn;
}

export function notificarNoAutorizado(): void {
  escuchaNoAutorizado?.();
}
