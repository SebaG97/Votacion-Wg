import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import {
  listarIncidencias,
  resolverIncidencia,
  type FiltrosIncidencias,
  type IncidenciaPadron,
  type SeveridadIncidencia,
} from "../api/padron";
import { useOperador } from "../context/OperadorContext";
import { mensajeDeError } from "../lib/errores";
import { traducirErrorVotacion } from "../lib/erroresVotacion";

const SEVERIDADES: SeveridadIncidencia[] = ["CRITICA", "ALTA", "MEDIA", "BAJA"];

export function IncidenciasPage() {
  const { operador } = useOperador();
  const [incidencias, setIncidencias] = useState<IncidenciaPadron[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [accionError, setAccionError] = useState<string | null>(null);
  const [resolviendoId, setResolviendoId] = useState<number | null>(null);

  const [severidad, setSeveridad] = useState<SeveridadIncidencia | "">("");
  const [tipo, setTipo] = useState("");
  const [resuelta, setResuelta] = useState<"" | "si" | "no">("");

  async function cargar() {
    setError(null);
    const filtros: FiltrosIncidencias = {};
    if (severidad) filtros.severidad = severidad;
    if (tipo.trim()) filtros.tipo = tipo.trim();
    if (resuelta === "si") filtros.resuelta = true;
    if (resuelta === "no") filtros.resuelta = false;

    try {
      const datos = await listarIncidencias(filtros);
      setIncidencias(datos);
    } catch (err) {
      setError(mensajeDeError(err));
    }
  }

  useEffect(() => {
    void cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [severidad, tipo, resuelta]);

  async function handleResolver(id: number) {
    if (!operador.trim() || resolviendoId !== null) return;
    setResolviendoId(id);
    setAccionError(null);
    try {
      await resolverIncidencia(id, operador.trim());
      await cargar();
    } catch (err) {
      setAccionError(traducirErrorVotacion(err));
    } finally {
      setResolviendoId(null);
    }
  }

  return (
    <section className="panel ancho">
      <p className="eyebrow">Padrón</p>
      <h1>Incidencias</h1>
      <p className="warning-banner">
        Marcar una incidencia como "revisada" es solo trazabilidad administrativa: no rehabilita
        ninguna unidad electoral ni cambia su estado de votación.
      </p>

      <div className="filters">
        <select
          value={severidad}
          onChange={(e) => setSeveridad(e.target.value as SeveridadIncidencia | "")}
          aria-label="Filtrar por severidad"
        >
          <option value="">Todas las severidades</option>
          {SEVERIDADES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>

        <input
          className="text-input"
          style={{ width: 220 }}
          placeholder="Filtrar por tipo (ej: CI_FALTANTE)"
          value={tipo}
          onChange={(e) => setTipo(e.target.value)}
          aria-label="Filtrar por tipo"
        />

        <select
          value={resuelta}
          onChange={(e) => setResuelta(e.target.value as "" | "si" | "no")}
          aria-label="Filtrar por resuelta"
        >
          <option value="">Resueltas y no resueltas</option>
          <option value="no">Solo no resueltas</option>
          <option value="si">Solo resueltas</option>
        </select>
      </div>

      {accionError && (
        <p className="error-message" role="alert">
          {accionError}
        </p>
      )}

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

      {!incidencias && !error && (
        <p className="loading-message">
          <Loader2 size={18} className="spin" /> Cargando incidencias...
        </p>
      )}

      {incidencias && incidencias.length === 0 && <p>No hay incidencias con estos filtros.</p>}

      {incidencias && incidencias.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Severidad</th>
                <th>Tipo</th>
                <th>Descripción</th>
                <th>Estado</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {incidencias.map((i) => (
                <tr key={i.id}>
                  <td>{i.id}</td>
                  <td>
                    <span className={`badge ${i.severidad.toLowerCase()}`}>{i.severidad}</span>
                  </td>
                  <td>{i.tipo}</td>
                  <td style={{ maxWidth: 420 }}>{i.descripcion}</td>
                  <td>
                    {i.resuelto_at ? (
                      <span>
                        Revisada por {i.resuelto_por} el {i.resuelto_at}
                      </span>
                    ) : (
                      "Pendiente"
                    )}
                  </td>
                  <td>
                    {!i.resuelto_at && (
                      <button
                        type="button"
                        className="secondary-button"
                        disabled={!operador.trim() || resolviendoId === i.id}
                        onClick={() => void handleResolver(i.id)}
                      >
                        {resolviendoId === i.id ? "Marcando..." : "Marcar como revisada"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
