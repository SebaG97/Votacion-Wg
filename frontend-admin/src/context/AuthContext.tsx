import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";

import {
  guardarAdminToken,
  obtenerAdminToken,
  setEscuchaNoAutorizado,
} from "../api/adminToken";

type AuthContextValue = {
  token: string | null;
  login: (token: string) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

/**
 * Fuente de verdad de si el panel esta autenticado. `logout` se registra
 * como el "escucha de no autorizado" de `client.ts`: cualquier `401`/`403`
 * real de un endpoint administrativo -- no solo el intento de login -- limpia
 * el token guardado y hace que `RequireAuth` vuelva a mostrar el login, sin
 * que quede cacheado un token invalido reintentando en loop.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => obtenerAdminToken());

  const logout = useCallback(() => {
    guardarAdminToken(null);
    setToken(null);
  }, []);

  useEffect(() => {
    setEscuchaNoAutorizado(logout);
    return () => setEscuchaNoAutorizado(null);
  }, [logout]);

  function login(nuevoToken: string) {
    guardarAdminToken(nuevoToken);
    setToken(nuevoToken);
  }

  return <AuthContext.Provider value={{ token, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth debe usarse dentro de AuthProvider");
  }
  return ctx;
}
