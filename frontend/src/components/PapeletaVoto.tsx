import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import type { PersonaConsultada, UnidadElectoralDisponible } from "../api/habilitacion";
import { ApiError } from "../api/client";
import {
  getVotacionAbierta,
  registrarVoto,
  type VotacionAbierta,
  type VotoResponse,
} from "../api/votacion";
import { mensajeDeError } from "../lib/errores";

type PapeletaVotoProps = {
  unidad: UnidadElectoralDisponible;
  personas: PersonaConsultada[];
  celularConsultado: string;
  onVotoRegistrado: (voto: VotoResponse) => void;
  onYaVotado: () => void;
};

function esPersonaNoAutorizada(err: unknown): boolean {
  return err instanceof ApiError && err.status === 400 && !!err.detail?.toLowerCase().includes("autorizada");
}

/**
 * `POST /votaciones/{id}/votos` devuelve 409 para tres errores distintos
 * (`backend/app/services/voto.py`): `VotoDuplicadoError` (la unidad ya votó
 * -- ahí sí corresponde "ya votado"), `VotacionNoDisponibleError` (la
 * votación se cerró en la ventana entre cargar la papeleta y confirmar) y
 * `UnidadElectoralNoDisponibleError` (la unidad quedó bloqueada por una
 * incidencia nueva en ese mismo lapso). Los tres llegan con `status === 409`,
 * asi que hay que distinguirlos por el texto de `detail` -- nunca asumir que
 * todo 409 es un voto duplicado, porque en los otros dos casos el voto nunca
 * se registró y afirmar lo contrario rompe la trazabilidad de quien votó.
 */
function clasificarConflicto(
  err: unknown,
): "duplicado" | "votacion-no-disponible" | "unidad-no-disponible" | "desconocido" {
  if (!(err instanceof ApiError) || err.status !== 409) {
    return "desconocido";
  }
  const detalle = err.detail?.toLowerCase() ?? "";
  if (detalle.includes("ya existe un voto")) {
    return "duplicado";
  }
  if (detalle.includes("no existe o no esta en estado abierta")) {
    return "votacion-no-disponible";
  }
  if (detalle.includes("no esta disponible para votar")) {
    return "unidad-no-disponible";
  }
  return "desconocido";
}

export function PapeletaVoto({
  unidad,
  personas,
  celularConsultado,
  onVotoRegistrado,
  onYaVotado,
}: PapeletaVotoProps) {
  const [personaId, setPersonaId] = useState<number | null>(
    personas.length === 1 ? personas[0].persona_id : null,
  );
  const [opcionId, setOpcionId] = useState<number | null>(null);

  const [papeleta, setPapeleta] = useState<VotacionAbierta | null>(null);
  const [cargandoPapeleta, setCargandoPapeleta] = useState(true);
  const [papeletaError, setPapeletaError] = useState<string | null>(null);

  const [enviando, setEnviando] = useState(false);
  const [votoError, setVotoError] = useState<string | null>(null);

  async function cargarPapeleta() {
    setCargandoPapeleta(true);
    setPapeletaError(null);
    try {
      const datos = await getVotacionAbierta();
      setPapeleta(datos);
    } catch (err) {
      setPapeletaError(mensajeDeError(err));
    } finally {
      setCargandoPapeleta(false);
    }
  }

  useEffect(() => {
    void cargarPapeleta();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleConfirmar() {
    if (personaId === null || opcionId === null || !papeleta || enviando) {
      return;
    }

    setEnviando(true);
    setVotoError(null);
    try {
      const voto = await registrarVoto(papeleta.votacion_id, {
        celular_consultado: celularConsultado,
        unidad_electoral_id: unidad.unidad_electoral_id,
        opcion_id: opcionId,
        emitido_por_persona_id: personaId,
      });
      onVotoRegistrado(voto);
    } catch (err) {
      const conflicto = clasificarConflicto(err);
      if (conflicto === "duplicado") {
        onYaVotado();
        return;
      }
      if (conflicto === "votacion-no-disponible") {
        setVotoError("La votación ya no está disponible. Volvé a intentarlo.");
        return;
      }
      if (conflicto === "unidad-no-disponible") {
        setVotoError("Esta unidad electoral ya no está disponible para votar. Volvé a intentarlo.");
        return;
      }
      if (esPersonaNoAutorizada(err) && personas.length > 1) {
        setVotoError("Esa persona no está autorizada para emitir este voto. Elegí a otra persona de la lista.");
        setPersonaId(null);
        return;
      }
      setVotoError(mensajeDeError(err));
    } finally {
      setEnviando(false);
    }
  }

  if (personaId === null) {
    return (
      <section className="panel">
        <p className="eyebrow">Confirmá quién vota</p>
        <h1>¿Quién de estas personas está emitiendo el voto?</h1>

        {votoError && (
          <p className="error-message" role="alert">
            {votoError}
          </p>
        )}

        <ul className="persona-list">
          {personas.map((persona) => (
            <li key={persona.persona_id}>
              <button
                type="button"
                className="persona-card"
                onClick={() => setPersonaId(persona.persona_id)}
              >
                {persona.nombres} {persona.apellidos}
              </button>
            </li>
          ))}
        </ul>
      </section>
    );
  }

  return (
    <section className="panel">
      <p className="eyebrow">Emitir voto</p>
      <h1>Elegí una opción</h1>

      {cargandoPapeleta && (
        <p className="loading-message">
          <Loader2 size={18} className="spin" /> Cargando papeleta...
        </p>
      )}

      {papeletaError && (
        <div>
          <p className="error-message" role="alert">
            {papeletaError}
          </p>
          <button type="button" className="secondary-button" onClick={() => void cargarPapeleta()}>
            Reintentar
          </button>
        </div>
      )}

      {papeleta && (
        <>
          <ul className="opcion-list" role="radiogroup" aria-label="Opciones de voto">
            {papeleta.opciones.map((opcion) => (
              <li key={opcion.id}>
                <button
                  type="button"
                  role="radio"
                  aria-checked={opcionId === opcion.id}
                  className={`opcion-card ${opcionId === opcion.id ? "seleccionada" : ""}`}
                  onClick={() => setOpcionId(opcion.id)}
                >
                  {opcion.nombre}
                </button>
              </li>
            ))}
          </ul>

          {votoError && (
            <p className="error-message" role="alert">
              {votoError}
            </p>
          )}

          <button
            type="button"
            className="primary-button"
            disabled={opcionId === null || enviando}
            onClick={() => void handleConfirmar()}
          >
            {enviando ? <Loader2 size={18} className="spin" /> : null}
            {enviando ? "Registrando voto..." : "Confirmar voto"}
          </button>
        </>
      )}
    </section>
  );
}
