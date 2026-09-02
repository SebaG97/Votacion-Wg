import { apiPost } from "./client";

export type LoginResponse = {
  token: string;
};

/** `POST /auth/login` (Mision 12, DEC-030): cambia el token administrativo
 * crudo pegado a mano por usuario/contraseña convencionales, validados en el
 * servidor contra `ADMIN_USERNAME`/`ADMIN_PASSWORD`. Devuelve el mismo token
 * (`ADMIN_API_KEY`) que el resto del panel ya manda como `X-Admin-Token`. */
export function login(usuario: string, contrasena: string): Promise<LoginResponse> {
  return apiPost<LoginResponse, { usuario: string; contrasena: string }>("/auth/login", {
    usuario,
    contrasena,
  });
}
