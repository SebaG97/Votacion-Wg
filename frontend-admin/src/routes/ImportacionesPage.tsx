import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import { ejecutarImportacion, listarImportaciones, type ImportacionPadron } from "../api/padron";
import { useOperador } from "../context/OperadorContext";
import { mensajeDeError } from "../lib/errores";
import { traducirErrorVotacion } from "../lib/erroresVotacion";

/**
 * `POST /padron/importaciones` reescribe todo el padron (personas,
 * matrimonios, unidades electorales e incidencias): no debe poder dispararse
 * con un solo click. `mostrarConfirmacion` es el segundo paso explicito que
 * el operador tiene que pedir antes de que se ejecute la request real.
 */
export function ImportacionesPage() {
  const { operador } = useOperador();
  const [importaciones, setImportaciones] = useState<ImportacionPadron[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [mostrarConfirmacion, setMostrarConfirmacion] = useState(false);
  const [excelPath, setExcelPath] = useState("");
  const [ejecutando, setEjecutando] = useState(false);
  const [errorEjecucion, setErrorEjecucion] = useState<string | null>(null);

  async function cargar() {
    setError(null);
    try {
      setImportaciones(await listarImportaciones());
    } catch (err) {
      setError(mensajeDeError(err));
    }
  }

  useEffect(() => {
    void cargar();
  }, []);

  async function handleConfirmarImportacion() {
    setEjecutando(true);
    setErrorEjecucion(null);
    try {
      await ejecutarImportacion({
        excel_path: excelPath.trim() || undefined,
        usuario: operador.trim() || undefined,
      });
      setMostrarConfirmacion(false);
      setExcelPath("");
      await cargar();
    } catch (err) {
      setErrorEjecucion(traducirErrorVotacion(err));
    } finally {
      setEjecutando(false);
    }
  }

  return (
    <section className="panel ancho">
      <p className="eyebrow">Padrón</p>
      <h1>Importaciones</h1>

      {!mostrarConfirmacion && (
        <button
          type="button"
          className="primary-button"
          onClick={() => setMostrarConfirmacion(true)}
        >
          Nueva importación
        </button>
      )}

      {mostrarConfirmacion && (
        <div className="warning-banner">
          <p>
            <strong>Esta operación reescribe todo el padrón actual</strong>: personas,
            matrimonios, unidades electorales e incidencias se recrean desde cero a partir del
            Excel. Se rechaza si hay una votación más allá de BORRADOR. ¿Confirmás que querés
            ejecutarla?
          </p>

          <div className="field">
            <label htmlFor="excel-path">
              Ruta del Excel (opcional, por defecto usa el padrón oficial)
            </label>
            <input
              id="excel-path"
              className="text-input"
              value={excelPath}
              disabled={ejecutando}
              onChange={(e) => setExcelPath(e.target.value)}
            />
          </div>

          {errorEjecucion && (
            <p className="error-message" role="alert">
              {errorEjecucion}
            </p>
          )}

          <div className="form-row">
            <button
              type="button"
              className="danger-button"
              disabled={ejecutando}
              onClick={() => void handleConfirmarImportacion()}
            >
              {ejecutando ? <Loader2 size={18} className="spin" /> : null}
              {ejecutando ? "Ejecutando..." : "Sí, ejecutar importación"}
            </button>
            <button
              type="button"
              className="secondary-button"
              disabled={ejecutando}
              onClick={() => setMostrarConfirmacion(false)}
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      <h2 style={{ marginTop: 24 }}>Historial</h2>

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

      {!importaciones && !error && (
        <p className="loading-message">
          <Loader2 size={18} className="spin" /> Cargando historial...
        </p>
      )}

      {importaciones && importaciones.length === 0 && (
        <p>Todavía no se corrió ninguna importación.</p>
      )}

      {importaciones && importaciones.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Fecha</th>
                <th>Archivo</th>
                <th>Usuario</th>
                <th>Estado</th>
                <th>Error</th>
              </tr>
            </thead>
            <tbody>
              {importaciones.map((i) => (
                <tr key={i.id}>
                  <td>{i.id}</td>
                  <td>{i.fecha}</td>
                  <td style={{ maxWidth: 320, overflowWrap: "anywhere" }}>{i.archivo_origen}</td>
                  <td>{i.usuario ?? "—"}</td>
                  <td>{i.estado}</td>
                  <td>{i.error ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
