import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Navigate } from "react-router-dom";

import { listarVotaciones } from "../api/votaciones";
import { useAuth } from "../context/AuthContext";
import { mensajeDeError } from "../lib/errores";

/**
 * Pega el `ADMIN_API_KEY` y lo valida contra `GET /votaciones` antes de
 * entrar al dashboard: `login()` lo guarda de forma optimista (sessionStorage
 * via `adminToken.ts`), y si la llamada de prueba da `401`/`403`,
 * `client.ts` dispara `notificarNoAutorizado()` -> `AuthContext.logout()` lo
 * limpia solo, sin dejarlo cacheado. Evita el parpadeo de "entrar al
 * dashboard y rebotar al login" que pasaria si se confiara ciegamente en el
 * valor pegado.
 */
export function LoginPage() {
  const { token, login } = useAuth();
  const [tokenInput, setTokenInput] = useState("");
  const [verificando, setVerificando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (token) {
    return <Navigate to="/" replace />;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!tokenInput.trim() || verificando) {
      return;
    }
    setVerificando(true);
    setError(null);
    login(tokenInput.trim());
    try {
      await listarVotaciones();
    } catch (err) {
      setError(mensajeDeError(err));
    } finally {
      setVerificando(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="panel">
        <p className="eyebrow">Panel administrativo</p>
        <h1>VOTACION</h1>
        <p>Pegá el token administrativo (X-Admin-Token) para continuar.</p>

        <form onSubmit={(e) => void handleSubmit(e)}>
          <div className="field">
            <label htmlFor="admin-token">Token administrativo</label>
            <input
              id="admin-token"
              className="text-input"
              type="password"
              autoComplete="off"
              value={tokenInput}
              disabled={verificando}
              onChange={(e) => setTokenInput(e.target.value)}
            />
          </div>

          {error && (
            <p className="error-message" role="alert">
              {error}
            </p>
          )}

          <button type="submit" className="primary-button" disabled={verificando}>
            {verificando ? <Loader2 size={18} className="spin" /> : null}
            {verificando ? "Verificando..." : "Ingresar"}
          </button>
        </form>
      </section>
    </main>
  );
}
