import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import {
  obtenerResultados,
  obtenerResultadosCsv,
  type VotacionResultados,
} from "../api/votaciones";
import { mensajeDeError } from "../lib/errores";
import { BarChart } from "./charts/BarChart";

type ResultadosViewProps = {
  votacionId: number;
};

/**
 * Vista de resultados finales (Mision 10). El componente que la monta
 * (`VotacionDetailPage`) es responsable de solo renderizarla con `estado`
 * RESULTADOS_REVELADOS (DEC-044) -- antes de revelar nadie ve un desglose
 * por opcion, y esta vista nunca debe montarse (ni oculta en el DOM) en otro
 * estado. Revelar ya no vive aca: es el boton de la votacion CERRADA en
 * `VotacionDetailPage`, que abre la presentacion en vivo.
 */
export function ResultadosView({ votacionId }: ResultadosViewProps) {
  const [resultados, setResultados] = useState<VotacionResultados | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [descargando, setDescargando] = useState(false);
  const [errorCsv, setErrorCsv] = useState<string | null>(null);

  async function cargar() {
    setError(null);
    try {
      const datos = await obtenerResultados(votacionId);
      setResultados(datos);
    } catch (err) {
      setError(mensajeDeError(err));
    }
  }

  useEffect(() => {
    void cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [votacionId]);

  async function handleDescargarCsv() {
    setDescargando(true);
    setErrorCsv(null);
    try {
      const csv = await obtenerResultadosCsv(votacionId);
      const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
      const enlace = document.createElement("a");
      enlace.href = url;
      enlace.download = `resultados-votacion-${votacionId}.csv`;
      enlace.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setErrorCsv(mensajeDeError(err));
    } finally {
      setDescargando(false);
    }
  }

  return (
    <section className="panel ancho">
      <p className="eyebrow">Resultados finales</p>
      <h1>Resultados</h1>

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

      {!resultados && !error && (
        <p className="loading-message">
          <Loader2 size={18} className="spin" /> Cargando resultados...
        </p>
      )}

      {resultados && (
        <>
          <p>
            <strong>Total de votos:</strong> {resultados.total_votos}
          </p>

          <button
            type="button"
            className="secondary-button"
            disabled={descargando}
            onClick={() => void handleDescargarCsv()}
          >
            {descargando ? "Descargando..." : "Descargar CSV"}
          </button>
          {errorCsv && (
            <p className="error-message" role="alert">
              {errorCsv}
            </p>
          )}

          <h2>Por opción</h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Opción</th>
                  <th>Votos</th>
                  <th>%</th>
                </tr>
              </thead>
              <tbody>
                {resultados.totales_por_opcion.map((o) => (
                  <tr key={o.opcion_id}>
                    <td>{o.nombre}</td>
                    <td>{o.votos}</td>
                    <td>{o.porcentaje.toFixed(2)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="chart-wrap">
            <BarChart
              testId="chart-por-opcion"
              ariaLabel="Votos por opción"
              data={resultados.totales_por_opcion.map((o) => ({
                key: o.opcion_id,
                label: o.nombre,
                value: o.votos,
                displayValue: `${o.votos} (${o.porcentaje.toFixed(1)}%)`,
              }))}
            />
          </div>

          <h2>Por tipo de unidad electoral</h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Tipo</th>
                  <th>Votos emitidos</th>
                  <th>Unidades habilitadas</th>
                  <th>Participación</th>
                </tr>
              </thead>
              <tbody>
                {resultados.totales_por_tipo_unidad.map((t) => (
                  <tr key={t.tipo}>
                    <td>{t.tipo}</td>
                    <td>{t.votos_emitidos}</td>
                    <td>{t.unidades_habilitadas}</td>
                    <td>{t.participacion === null ? "—" : `${(t.participacion * 100).toFixed(1)}%`}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="chart-wrap">
            <BarChart
              testId="chart-por-tipo-unidad"
              ariaLabel="Participación por tipo de unidad electoral"
              maxValue={1}
              data={resultados.totales_por_tipo_unidad.map((t) => ({
                key: t.tipo,
                label: t.tipo,
                value: t.participacion ?? 0,
                displayValue: t.participacion === null ? "—" : `${(t.participacion * 100).toFixed(1)}%`,
              }))}
            />
          </div>

          <h2>Por círculo</h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Círculo</th>
                  <th>Votos emitidos</th>
                  <th>Unidades habilitadas</th>
                  <th>Participación</th>
                </tr>
              </thead>
              <tbody>
                {resultados.totales_por_grupo.map((g) => (
                  <tr key={g.grupo_id}>
                    <td>{g.nombre}</td>
                    <td>{g.votos_emitidos}</td>
                    <td>{g.unidades_habilitadas}</td>
                    <td>{g.participacion === null ? "—" : `${(g.participacion * 100).toFixed(1)}%`}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="chart-wrap">
            <BarChart
              testId="chart-por-circulo"
              ariaLabel="Participación por círculo"
              maxValue={1}
              data={resultados.totales_por_grupo.map((g) => ({
                key: g.grupo_id,
                label: g.nombre,
                value: g.participacion ?? 0,
                displayValue: g.participacion === null ? "—" : `${(g.participacion * 100).toFixed(1)}%`,
              }))}
            />
          </div>
        </>
      )}
    </section>
  );
}
