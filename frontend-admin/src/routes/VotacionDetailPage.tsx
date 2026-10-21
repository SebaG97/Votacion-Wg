import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, Clock3, HelpCircle, Loader2, Vote } from "lucide-react";
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
import { BarChart } from "../components/charts/BarChart";
import { EstadoBadge } from "../components/EstadoBadge";
import { OpcionFotoEditor } from "../components/OpcionFotoEditor";
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
    // Cerrar es irreversible: un click accidental terminaria la eleccion real.
    if (
      !window.confirm(
        `¿Cerrar la votación "${votacion?.nombre ?? ""}"? Después ya nadie podrá votar y no se puede deshacer.`,
      )
    ) {
      return;
    }
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
            <dt>
              <CheckCircle2 size={14} /> Habilitadas
            </dt>
            <dd>{estadoOperativo.unidades_por_estado.habilitada}</dd>
          </div>
          <div>
            <dt>
              <AlertTriangle size={14} /> Bloqueadas por incidencia
            </dt>
            <dd>{estadoOperativo.unidades_por_estado.bloqueada_por_incidencia}</dd>
          </div>
          <div>
            <dt>
              <HelpCircle size={14} /> Pendiente postulantes
            </dt>
            <dd>{estadoOperativo.unidades_por_estado.pendiente_definicion_postulantes}</dd>
          </div>
          <div>
            <dt>
              <HelpCircle size={14} /> Pendiente baja
            </dt>
            <dd>{estadoOperativo.unidades_por_estado.pendiente_definicion_baja}</dd>
          </div>
          <div>
            <dt>
              <Vote size={14} /> Votos emitidos
            </dt>
            <dd>{estadoOperativo.votos_emitidos}</dd>
          </div>
          <div>
            <dt>
              <Clock3 size={14} /> Pendientes de votar
            </dt>
            <dd>{estadoOperativo.pendientes}</dd>
          </div>
        </dl>

        {/* Graficos del tablero en vivo (Mision 13, DEC-035): solo los
            agregados que el stat-grid de arriba ya muestra (unidades por
            estado, votos emitidos vs pendientes). Nunca nada desglosado por
            opcion mientras la votacion no esta CERRADA/RESULTADOS_REVELADOS
            -- esa vista vive exclusivamente en `ResultadosView`, montada mas
            abajo solo en esos dos estados (DEC-022). */}
        <div className="chart-wrap">
          <BarChart
            testId="chart-unidades-por-estado"
            ariaLabel="Unidades electorales por estado"
            data={[
              {
                key: "habilitada",
                label: "Habilitadas",
                value: estadoOperativo.unidades_por_estado.habilitada,
                displayValue: String(estadoOperativo.unidades_por_estado.habilitada),
                color: "var(--color-success-solid)",
              },
              {
                key: "bloqueada",
                label: "Bloqueadas por incidencia",
                value: estadoOperativo.unidades_por_estado.bloqueada_por_incidencia,
                displayValue: String(estadoOperativo.unidades_por_estado.bloqueada_por_incidencia),
                color: "var(--color-danger-solid)",
              },
              {
                key: "pendiente-postulantes",
                label: "Pendiente postulantes",
                value: estadoOperativo.unidades_por_estado.pendiente_definicion_postulantes,
                displayValue: String(
                  estadoOperativo.unidades_por_estado.pendiente_definicion_postulantes,
                ),
                color: "var(--color-warning-solid)",
              },
              {
                key: "pendiente-baja",
                label: "Pendiente baja",
                value: estadoOperativo.unidades_por_estado.pendiente_definicion_baja,
                displayValue: String(estadoOperativo.unidades_por_estado.pendiente_definicion_baja),
                color: "var(--color-info-solid)",
              },
            ]}
          />
        </div>
        <div className="chart-wrap">
          <BarChart
            testId="chart-votos-vs-pendientes"
            ariaLabel="Votos emitidos vs. pendientes de votar"
            data={[
              {
                key: "emitidos",
                label: "Votos emitidos",
                value: estadoOperativo.votos_emitidos,
                displayValue: String(estadoOperativo.votos_emitidos),
                color: "var(--color-primary-500)",
              },
              {
                key: "pendientes",
                label: "Pendientes de votar",
                value: estadoOperativo.pendientes,
                displayValue: String(estadoOperativo.pendientes),
                color: "var(--color-neutral-400)",
              },
            ]}
          />
        </div>

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
                  <span>{o.nombre}</span>
                  <OpcionFotoEditor
                    opcion={o}
                    onCambio={(actualizada) =>
                      setOpciones((actuales) =>
                        actuales.map((x) => (x.id === actualizada.id ? actualizada : x)),
                      )
                    }
                  />
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
                <span className="hint-text" style={{ marginLeft: 12 }}>
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
              <span className="hint-text" style={{ marginLeft: 12 }}>
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
