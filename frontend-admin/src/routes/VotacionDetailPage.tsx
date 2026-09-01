import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import { listarImportaciones, type ImportacionPadron } from "../api/padron";
import {
  abrirVotacion,
  agregarOpcion,
  cerrarVotacion,
  listarOpciones,
  listarVotaciones,
  obtenerEstadoOperativo,
  type Opcion,
  type Votacion,
  type VotacionEstado,
} from "../api/votaciones";
import { EstadoBadge } from "../components/EstadoBadge";
import { ResultadosView } from "../components/ResultadosView";
import { useOperador } from "../context/OperadorContext";
import { mensajeDeError } from "../lib/errores";
import { traducirErrorVotacion } from "../lib/erroresVotacion";

/**
 * `GET /votaciones/{id}/estado` (Mision 07) es deliberadamente el unico dato
 * "en vivo" que se muestra aca mientras la votacion no esta CERRADA o
 * RESULTADOS_REVELADOS: nunca nada agrupado por opcion (REGLAS_NEGOCIO.md).
 * El resumen de la ultima importacion es el JSON que ya guarda
 * `ImportacionPadron.resumen` (Mision 04) sin recalcular nada.
 */
export function VotacionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const votacionId = Number(id);
  const navigate = useNavigate();
  const { operador } = useOperador();

  const [votacion, setVotacion] = useState<Votacion | null>(null);
  const [estadoOperativo, setEstadoOperativo] = useState<VotacionEstado | null>(null);
  const [opciones, setOpciones] = useState<Opcion[]>([]);
  const [ultimaImportacion, setUltimaImportacion] = useState<ImportacionPadron | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [nombreOpcion, setNombreOpcion] = useState("");
  const [accionError, setAccionError] = useState<string | null>(null);
  const [ejecutandoAccion, setEjecutandoAccion] = useState(false);

  async function cargar() {
    setError(null);
    try {
      const [votaciones, estado, importaciones] = await Promise.all([
        listarVotaciones(),
        obtenerEstadoOperativo(votacionId),
        listarImportaciones(),
      ]);
      const encontrada = votaciones.find((v) => v.id === votacionId) ?? null;
      setVotacion(encontrada);
      setEstadoOperativo(estado);
      setUltimaImportacion(importaciones[0] ?? null);

      if (encontrada?.estado === "BORRADOR") {
        setOpciones(await listarOpciones(votacionId));
      } else {
        setOpciones([]);
      }
    } catch (err) {
      setError(mensajeDeError(err));
    }
  }

  useEffect(() => {
    void cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [votacionId]);

  async function handleAgregarOpcion(e: React.FormEvent) {
    e.preventDefault();
    if (!nombreOpcion.trim() || ejecutandoAccion) return;
    setEjecutandoAccion(true);
    setAccionError(null);
    try {
      await agregarOpcion(votacionId, { nombre: nombreOpcion.trim() });
      setNombreOpcion("");
      await cargar();
    } catch (err) {
      setAccionError(traducirErrorVotacion(err));
    } finally {
      setEjecutandoAccion(false);
    }
  }

  async function handleAbrir() {
    if (!operador.trim() || ejecutandoAccion) return;
    setEjecutandoAccion(true);
    setAccionError(null);
    try {
      await abrirVotacion(votacionId, operador.trim());
      await cargar();
    } catch (err) {
      setAccionError(traducirErrorVotacion(err));
    } finally {
      setEjecutandoAccion(false);
    }
  }

  async function handleCerrar() {
    if (!operador.trim() || ejecutandoAccion) return;
    setEjecutandoAccion(true);
    setAccionError(null);
    try {
      await cerrarVotacion(votacionId, operador.trim());
      await cargar();
    } catch (err) {
      setAccionError(traducirErrorVotacion(err));
    } finally {
      setEjecutandoAccion(false);
    }
  }

  if (error) {
    return (
      <section className="panel ancho">
        <p className="error-message" role="alert">
          {error}
        </p>
        <button type="button" className="secondary-button" onClick={() => void cargar()}>
          Reintentar
        </button>
      </section>
    );
  }

  if (!votacion || !estadoOperativo) {
    return (
      <p className="loading-message">
        <Loader2 size={18} className="spin" /> Cargando votación...
      </p>
    );
  }

  return (
    <>
      <section className="panel ancho">
        <button type="button" className="link-button" onClick={() => navigate("/")}>
          ← Volver al dashboard
        </button>
        <p className="eyebrow">Votación #{votacion.id}</p>
        <h1>
          {votacion.nombre} <EstadoBadge estado={votacion.estado} />
        </h1>

        <h2>Estado operativo</h2>
        <dl className="stat-grid">
          <div>
            <dt>Habilitadas</dt>
            <dd>{estadoOperativo.unidades_por_estado.habilitada}</dd>
          </div>
          <div>
            <dt>Bloqueadas por incidencia</dt>
            <dd>{estadoOperativo.unidades_por_estado.bloqueada_por_incidencia}</dd>
          </div>
          <div>
            <dt>Pendiente postulantes</dt>
            <dd>{estadoOperativo.unidades_por_estado.pendiente_definicion_postulantes}</dd>
          </div>
          <div>
            <dt>Pendiente baja</dt>
            <dd>{estadoOperativo.unidades_por_estado.pendiente_definicion_baja}</dd>
          </div>
          <div>
            <dt>Votos emitidos</dt>
            <dd>{estadoOperativo.votos_emitidos}</dd>
          </div>
          <div>
            <dt>Pendientes de votar</dt>
            <dd>{estadoOperativo.pendientes}</dd>
          </div>
        </dl>

        <h2>Última importación del padrón</h2>
        {ultimaImportacion ? (
          <dl className="stat-grid">
            <div>
              <dt>Fecha</dt>
              <dd>{ultimaImportacion.fecha}</dd>
            </div>
            <div>
              <dt>Estado</dt>
              <dd>{ultimaImportacion.estado}</dd>
            </div>
            <div>
              <dt>Personas</dt>
              <dd>{String((ultimaImportacion.resumen as any)?.personas?.total ?? "—")}</dd>
            </div>
            <div>
              <dt>Incidencias</dt>
              <dd>{String((ultimaImportacion.resumen as any)?.incidencias?.total ?? "—")}</dd>
            </div>
          </dl>
        ) : (
          <p>Todavía no se corrió ninguna importación.</p>
        )}

        {accionError && (
          <p className="error-message" role="alert">
            {accionError}
          </p>
        )}

        {votacion.estado === "BORRADOR" && (
          <>
            <h2>Opciones (BORRADOR)</h2>
            <ul className="opcion-list">
              {opciones.map((o) => (
                <li key={o.id} className="opcion-card">
                  {o.nombre}
                </li>
              ))}
            </ul>
            <form className="form-row" onSubmit={(e) => void handleAgregarOpcion(e)}>
              <div className="field" style={{ flex: 1 }}>
                <label htmlFor="nombre-opcion">Nueva opción</label>
                <input
                  id="nombre-opcion"
                  className="text-input"
                  value={nombreOpcion}
                  disabled={ejecutandoAccion}
                  onChange={(e) => setNombreOpcion(e.target.value)}
                />
              </div>
              <button type="submit" className="secondary-button" disabled={ejecutandoAccion}>
                Agregar opción
              </button>
            </form>

            <p style={{ marginTop: 16 }}>
              <button
                type="button"
                className="primary-button"
                disabled={ejecutandoAccion || !operador.trim() || opciones.length === 0}
                onClick={() => void handleAbrir()}
              >
                Abrir votación
              </button>
              {!operador.trim() && (
                <span style={{ marginLeft: 12, color: "#66756d" }}>
                  Ingresá tu nombre de operador arriba para poder abrir.
                </span>
              )}
            </p>
          </>
        )}

        {votacion.estado === "ABIERTA" && (
          <p>
            <button
              type="button"
              className="danger-button"
              disabled={ejecutandoAccion || !operador.trim()}
              onClick={() => void handleCerrar()}
            >
              Cerrar votación
            </button>
            {!operador.trim() && (
              <span style={{ marginLeft: 12, color: "#66756d" }}>
                Ingresá tu nombre de operador arriba para poder cerrar.
              </span>
            )}
          </p>
        )}
      </section>

      {(votacion.estado === "CERRADA" || votacion.estado === "RESULTADOS_REVELADOS") && (
        <ResultadosView votacionId={votacion.id} estado={votacion.estado} onRevelado={cargar} />
      )}
    </>
  );
}
