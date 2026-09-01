import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { listarVotaciones, type Votacion } from "../api/votaciones";
import { EstadoBadge } from "../components/EstadoBadge";
import { mensajeDeError } from "../lib/errores";

export function DashboardPage() {
  const navigate = useNavigate();
  const [votaciones, setVotaciones] = useState<Votacion[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function cargar() {
    setError(null);
    try {
      const datos = await listarVotaciones();
      setVotaciones(datos);
    } catch (err) {
      setError(mensajeDeError(err));
    }
  }

  useEffect(() => {
    void cargar();
  }, []);

  return (
    <section className="panel ancho">
      <p className="eyebrow">Dashboard</p>
      <h1>Votaciones</h1>

      {error && (
        <div>
          <p className="error-message" role="alert">
            {error}
          </p>
          <button type="button" className="secondary-button" onClick={() => void cargar()}>
            Reintentar
          </button>
        </div>
      )}

      {!votaciones && !error && (
        <p className="loading-message">
          <Loader2 size={18} className="spin" /> Cargando votaciones...
        </p>
      )}

      {votaciones && votaciones.length === 0 && <p>Todavía no se creó ninguna votación.</p>}

      {votaciones && votaciones.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Nombre</th>
                <th>Estado</th>
                <th>Apertura</th>
                <th>Cierre</th>
              </tr>
            </thead>
            <tbody>
              {votaciones.map((v) => (
                <tr
                  key={v.id}
                  className="clickable"
                  onClick={() => navigate(`/votaciones/${v.id}`)}
                >
                  <td>{v.id}</td>
                  <td>{v.nombre}</td>
                  <td>
                    <EstadoBadge estado={v.estado} />
                  </td>
                  <td>{v.fecha_apertura ?? "—"}</td>
                  <td>{v.fecha_cierre ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
