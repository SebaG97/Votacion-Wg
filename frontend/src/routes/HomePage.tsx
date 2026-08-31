import { useCallback, useEffect, useState } from "react";

import { getHealth, type HealthResponse } from "../api/health";
import { ConnectionStatus } from "../components/ConnectionStatus";

export function HomePage() {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadHealth = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const health = await getHealth();
      setData(health);
    } catch {
      setData(null);
      setError("No se pudo consultar la API.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadHealth();
  }, [loadHealth]);

  return (
    <main className="app-shell">
      <div className="top-bar">
        <span className="brand">VOTACION WG</span>
        <span className="mode">Mision 01</span>
      </div>

      <ConnectionStatus data={data} error={error} isLoading={isLoading} onRetry={loadHealth} />
    </main>
  );
}
