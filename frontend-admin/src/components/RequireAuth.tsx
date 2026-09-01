import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { AdminShell } from "./AdminShell";

/**
 * Sin token guardado no hay forma de saber si es valido sin llamar a la API
 * (`ADMIN_API_KEY` es texto que se compara del lado del servidor, DEC-021):
 * mandar directo a `/login` es lo mas simple y evita parpadear el dashboard
 * antes de que la primera llamada administrativa confirme o rechace el
 * token. Si el token guardado resulta invalido, `client.ts` dispara
 * `notificarNoAutorizado()` en la primera llamada real y `AuthContext` lo
 * limpia, lo que hace que este componente vuelva a redirigir aca.
 */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { token } = useAuth();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <AdminShell>{children}</AdminShell>;
}
