import { useState } from "react";
import { CheckSquare } from "lucide-react";

import type { HabilitacionConsultaResponse, UnidadElectoralDisponible } from "../api/habilitacion";
import type { VotoResponse } from "../api/votacion";
import { ConsultaCelularForm } from "../components/ConsultaCelularForm";
import { ResultadoConsulta } from "../components/ResultadoConsulta";
import { PapeletaVoto } from "../components/PapeletaVoto";
import { ConfirmacionVoto } from "../components/ConfirmacionVoto";

type Paso = "consulta" | "resultado" | "papeleta" | "confirmado" | "ya-votado";

export function VotacionPage() {
  const [paso, setPaso] = useState<Paso>("consulta");
  const [consulta, setConsulta] = useState<HabilitacionConsultaResponse | null>(null);
  const [celularConsultado, setCelularConsultado] = useState("");
  const [unidadElegida, setUnidadElegida] = useState<UnidadElectoralDisponible | null>(null);
  const [voto, setVoto] = useState<VotoResponse | null>(null);

  function handleResultado(datos: HabilitacionConsultaResponse, celular: string) {
    setConsulta(datos);
    setCelularConsultado(datos.celular_normalizado ?? celular);
    setPaso("resultado");
  }

  function handleElegirUnidad(unidad: UnidadElectoralDisponible) {
    setUnidadElegida(unidad);
    setPaso("papeleta");
  }

  function handleVotoRegistrado(votoRegistrado: VotoResponse) {
    setVoto(votoRegistrado);
    setPaso("confirmado");
  }

  function handleYaVotado() {
    setPaso("ya-votado");
  }

  return (
    <main className="app-shell">
      <div className="top-bar">
        <span className="brand">
          <span className="brand-mark">
            <CheckSquare size={18} />
          </span>
          VOTACION WG
        </span>
      </div>

      {paso === "consulta" && <ConsultaCelularForm onResultado={handleResultado} />}

      {paso === "resultado" && consulta && (
        <ResultadoConsulta consulta={consulta} onElegirUnidad={handleElegirUnidad} />
      )}

      {paso === "papeleta" && consulta && unidadElegida && (
        <PapeletaVoto
          unidad={unidadElegida}
          personas={consulta.personas}
          celularConsultado={celularConsultado}
          onVotoRegistrado={handleVotoRegistrado}
          onYaVotado={handleYaVotado}
        />
      )}

      {paso === "confirmado" && voto && <ConfirmacionVoto voto={voto} />}

      {paso === "ya-votado" && (
        <section className="panel">
          <p className="eyebrow">Voto registrado</p>
          <h1>Tu voto ya fue registrado</h1>
        </section>
      )}
    </main>
  );
}
