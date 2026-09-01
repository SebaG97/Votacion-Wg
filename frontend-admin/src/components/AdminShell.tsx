import type { ReactNode } from "react";
import { CheckSquare } from "lucide-react";
import { NavLink } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { useOperador } from "../context/OperadorContext";

export function AdminShell({ children }: { children: ReactNode }) {
  const { logout } = useAuth();
  const { operador, setOperador } = useOperador();

  return (
    <main className="app-shell">
      <div className="top-bar">
        <span className="brand">
          <span className="brand-mark">
            <CheckSquare size={18} />
          </span>
          VOTACION · Panel Administrativo
        </span>
        <nav>
          <NavLink to="/" end className={({ isActive }) => (isActive ? "activo" : "")}>
            Dashboard
          </NavLink>
          <NavLink to="/incidencias" className={({ isActive }) => (isActive ? "activo" : "")}>
            Incidencias
          </NavLink>
          <NavLink to="/importaciones" className={({ isActive }) => (isActive ? "activo" : "")}>
            Importaciones
          </NavLink>
          <NavLink to="/votaciones/nueva" className={({ isActive }) => (isActive ? "activo" : "")}>
            Nueva votación
          </NavLink>
        </nav>
        <div className="top-bar-actions">
          <input
            className="operador-input"
            placeholder="Tu nombre de operador"
            value={operador}
            onChange={(e) => setOperador(e.target.value)}
            aria-label="Nombre de operador"
          />
          <button type="button" className="secondary-button" onClick={logout}>
            Salir
          </button>
        </div>
      </div>
      <div className="content">{children}</div>
    </main>
  );
}
