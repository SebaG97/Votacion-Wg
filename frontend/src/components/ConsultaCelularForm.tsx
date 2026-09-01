import { useState, type FormEvent } from "react";
import { Loader2, Search } from "lucide-react";

import { consultarHabilitacion, type HabilitacionConsultaResponse } from "../api/habilitacion";
import { mensajeDeError } from "../lib/errores";
import { esCelularValido } from "../lib/celular";

type ConsultaCelularFormProps = {
  onResultado: (datos: HabilitacionConsultaResponse, celularConsultado: string) => void;
};

export function ConsultaCelularForm({ onResultado }: ConsultaCelularFormProps) {
  const [celular, setCelular] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    if (!esCelularValido(celular)) {
      setError("Ingresá un número de celular válido.");
      return;
    }

    setError(null);
    setCargando(true);
    try {
      const datos = await consultarHabilitacion(celular);
      onResultado(datos, celular);
    } catch (err) {
      setError(mensajeDeError(err));
    } finally {
      setCargando(false);
    }
  }

  return (
    <section className="panel consulta-panel">
      <p className="eyebrow">Consultá tu habilitación</p>
      <h1>¿Con qué celular estás en el padrón?</h1>

      <form className="consulta-form" onSubmit={handleSubmit}>
        <input
          type="tel"
          inputMode="numeric"
          className="celular-input"
          placeholder="0981 000 000"
          value={celular}
          onChange={(event) => setCelular(event.target.value)}
          disabled={cargando}
          aria-label="Número de celular"
        />
        <button type="submit" className="primary-button" disabled={cargando}>
          {cargando ? <Loader2 size={18} className="spin" /> : <Search size={18} />}
          {cargando ? "Consultando..." : "Consultar"}
        </button>
      </form>

      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
