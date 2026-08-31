import { AlertCircle, CheckCircle2, Loader2, RefreshCw } from "lucide-react";

import type { HealthResponse } from "../api/health";

type ConnectionStatusProps = {
  data: HealthResponse | null;
  error: string | null;
  isLoading: boolean;
  onRetry: () => void;
};

export function ConnectionStatus({
  data,
  error,
  isLoading,
  onRetry,
}: ConnectionStatusProps) {
  const statusLabel = data ? "Conectado" : error ? "Sin conexion" : "Verificando";

  return (
    <section className="connection-panel" aria-live="polite">
      <div className="status-row">
        <div className={`status-icon ${data ? "ok" : error ? "error" : "loading"}`}>
          {data ? <CheckCircle2 size={28} /> : error ? <AlertCircle size={28} /> : <Loader2 size={28} />}
        </div>
        <div>
          <p className="eyebrow">Estado tecnico</p>
          <h1>{statusLabel}</h1>
        </div>
        <button className="icon-button" type="button" onClick={onRetry} disabled={isLoading} title="Reintentar conexion">
          <RefreshCw size={20} />
        </button>
      </div>

      <dl className="status-grid">
        <div>
          <dt>API</dt>
          <dd>{data?.app_name ?? "Pendiente"}</dd>
        </div>
        <div>
          <dt>Entorno</dt>
          <dd>{data?.environment ?? "Sin respuesta"}</dd>
        </div>
        <div>
          <dt>Prefijo</dt>
          <dd>{data?.api_prefix ?? "/api/v1"}</dd>
        </div>
        <div>
          <dt>Health</dt>
          <dd>{data?.status ?? error ?? "Consultando"}</dd>
        </div>
      </dl>
    </section>
  );
}
