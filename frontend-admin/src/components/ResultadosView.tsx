import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import { obtenerResultados, revelarResultados, type VotacionResultados } from "../api/votaciones";
import { mensajeDeError } from "../lib/errores";
import { traducirErrorVotacion } from "../lib/erroresVotacion";

type ResultadosViewProps = {
  votacionId: number;
  estado: "CERRADA" | "RESULTADOS_REVELADOS";
  onRevelado: () => void;
};

/**
 * Vista de resultados finales (Mision 10). El componente que la monta
 * (`VotacionDetailPage`) es responsable de solo renderizarla con `estado`
 * CERRADA o RESULTADOS_REVELADOS -- REGLAS_NEGOCIO.md prohibe exponer un
 * desglose por opcion antes del cierre, y esta vista nunca debe montarse
 * (ni oculta en el DOM) fuera de esos dos estados. El tipo de `estado` en
 * `ResultadosViewProps` ya excluye BORRADOR/ABIERTA en tiempo de compilacion.
 */
export function ResultadosView({ votacionId, estado, onRevelado }: ResultadosViewProps) {
  const [resultados, setResultados] = useState<VotacionResultados | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [revelando, setRevelando] = useState(false);
  const [errorRevelar, setErrorRevelar] = useState<string | null>(null);

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

  async function handleRevelar() {
    setRevelando(true);
    setErrorRevelar(null);
    try {
      await revelarResultados(votacionId);
      onRevelado();
    } catch (err) {
      setErrorRevelar(traducirErrorVotacion(err));
    } finally {
      setRevelando(false);
    }
  }

  return (
    <section className="panel ancho">
      <p className="eyebrow">Resultados finales</p>
      <h1>Resultados</h1>

      {estado === "CERRADA" && (
        <div className="warning-banner">
          Votación cerrada pero todavía no comunicada. "Revelar" es un hito administrativo
          formal; no cambia lo que ya podés ver acá.
        </div>
      )}

      {errorRevelar && (
        <p className="error-message" role="alert">
          {errorRevelar}
        </p>
      )}

      {estado === "CERRADA" && (
        <button
          type="button"
          className="primary-button"
          disabled={revelando}
          onClick={() => void handleRevelar()}
        >
          {revelando ? <Loader2 size={18} className="spin" /> : null}
          {revelando ? "Revelando..." : "Revelar resultados"}
        </button>
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
        </>
      )}
    </section>
  );
}
