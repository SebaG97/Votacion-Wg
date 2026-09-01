import { createContext, useContext, useState } from "react";
import type { ReactNode } from "react";

const CLAVE_STORAGE = "votacion-wg-admin-operador";

function leerOperadorGuardado(): string {
  try {
    return sessionStorage.getItem(CLAVE_STORAGE) ?? "";
  } catch {
    return "";
  }
}

type OperadorContextValue = {
  operador: string;
  setOperador: (nombre: string) => void;
};

const OperadorContext = createContext<OperadorContextValue | null>(null);

/**
 * Nombre de quien opera el panel en esta sesion: texto libre, sin relacion
 * con el token administrativo (mismo criterio que el campo `usuario` de
 * `abrir`/`cerrar` de la Mision 07, DEC-021). Se usa como valor de `usuario`
 * al abrir/cerrar una votacion o resolver una incidencia, para no pedirlo de
 * nuevo en cada accion.
 */
export function OperadorProvider({ children }: { children: ReactNode }) {
  const [operador, setOperadorState] = useState<string>(() => leerOperadorGuardado());

  function setOperador(nombre: string) {
    setOperadorState(nombre);
    try {
      sessionStorage.setItem(CLAVE_STORAGE, nombre);
    } catch {
      // sessionStorage no disponible: el nombre sigue viviendo en memoria.
    }
  }

  return (
    <OperadorContext.Provider value={{ operador, setOperador }}>
      {children}
    </OperadorContext.Provider>
  );
}

export function useOperador(): OperadorContextValue {
  const ctx = useContext(OperadorContext);
  if (!ctx) {
    throw new Error("useOperador debe usarse dentro de OperadorProvider");
  }
  return ctx;
}
