import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { crearVotacion } from "../api/votaciones";
import { traducirErrorVotacion } from "../lib/erroresVotacion";

export function CrearVotacionPage() {
  const navigate = useNavigate();
  const [nombre, setNombre] = useState("");
  const [creando, setCreando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!nombre.trim() || creando) return;
    setCreando(true);
    setError(null);
    try {
      const votacion = await crearVotacion(nombre.trim());
      navigate(`/votaciones/${votacion.id}`);
    } catch (err) {
      setError(traducirErrorVotacion(err));
    } finally {
      setCreando(false);
    }
  }

  return (
    <section className="panel">
      <p className="eyebrow">Crear votación</p>
      <h1>Nueva votación</h1>
      <p>Se crea en BORRADOR. Cargá sus opciones y abrila desde el detalle.</p>

      <form onSubmit={(e) => void handleSubmit(e)}>
        <div className="field">
          <label htmlFor="nombre-votacion">Nombre</label>
          <input
            id="nombre-votacion"
            className="text-input"
            value={nombre}
            disabled={creando}
            onChange={(e) => setNombre(e.target.value)}
          />
        </div>

        {error && (
          <p className="error-message" role="alert">
            {error}
          </p>
        )}

        <button type="submit" className="primary-button" disabled={creando}>
          {creando ? "Creando..." : "Crear votación"}
        </button>
      </form>
    </section>
  );
}
