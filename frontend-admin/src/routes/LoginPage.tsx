import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Navigate } from "react-router-dom";

import { login as loginRequest } from "../api/auth";
import { ApiError } from "../api/client";
import { useAuth } from "../context/AuthContext";

/**
 * Login usuario/contraseña (Mision 12, DEC-030): `POST /auth/login` valida
 * las credenciales en el servidor contra `ADMIN_USERNAME`/`ADMIN_PASSWORD` y
 * devuelve el mismo token (`ADMIN_API_KEY`) que el resto del panel ya manda
 * como `X-Admin-Token` -- `login()` de `AuthContext` solo lo guarda una vez
 * que el servidor ya lo confirmo, a diferencia del flujo anterior que pegaba
 * el token crudo de forma optimista y lo verificaba despues.
 */
function mensajeDeErrorLogin(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === undefined) {
      return "Sin conexión. Verificá tu internet e intentá de nuevo.";
    }
    if (err.status === 401) {
      return "Usuario o contraseña incorrectos.";
    }
    if (err.status === 403) {
      return "Login deshabilitado: contactá a quien administra el servidor.";
    }
    if (err.status === 429) {
      return "Demasiados intentos. Esperá un minuto e intentá de nuevo.";
    }
    return "No se pudo iniciar sesión. Intentá de nuevo.";
  }
  return "Ocurrió un error inesperado.";
}

export function LoginPage() {
  const { token, login } = useAuth();
  const [usuario, setUsuario] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [verificando, setVerificando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (token) {
    return <Navigate to="/" replace />;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!usuario.trim() || !contrasena || verificando) {
      return;
    }
    setVerificando(true);
    setError(null);
    try {
      const { token: nuevoToken } = await loginRequest(usuario.trim(), contrasena);
      login(nuevoToken);
    } catch (err) {
      setError(mensajeDeErrorLogin(err));
    } finally {
      setVerificando(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="panel">
        <p className="eyebrow">Panel administrativo</p>
        <h1>VOTACION</h1>
        <p>Ingresá tu usuario y contraseña para continuar.</p>

        <form onSubmit={(e) => void handleSubmit(e)}>
          <div className="field">
            <label htmlFor="usuario">Usuario</label>
            <input
              id="usuario"
              className="text-input"
              type="text"
              autoComplete="username"
              value={usuario}
              disabled={verificando}
              onChange={(e) => setUsuario(e.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="contrasena">Contraseña</label>
            <input
              id="contrasena"
              className="text-input"
              type="password"
              autoComplete="current-password"
              value={contrasena}
              disabled={verificando}
              onChange={(e) => setContrasena(e.target.value)}
            />
          </div>

          {error && (
            <p className="error-message" role="alert">
              {error}
            </p>
          )}

          <button type="submit" className="primary-button" disabled={verificando}>
            {verificando ? <Loader2 size={18} className="spin" /> : null}
            {verificando ? "Ingresando..." : "Ingresar"}
          </button>
        </form>
      </section>
    </main>
  );
}
