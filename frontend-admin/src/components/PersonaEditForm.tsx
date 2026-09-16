import { useState } from "react";
import { Loader2 } from "lucide-react";

import { ApiError } from "../api/client";
import { actualizarPersona, type PadronPersona, type PersonaUpdateResponse } from "../api/padron";
import { useOperador } from "../context/OperadorContext";
import { mensajeDeError } from "../lib/errores";

type PersonaEditFormProps = {
  persona: PadronPersona;
  onCancel: () => void;
  onGuardado: (respuesta: PersonaUpdateResponse) => void;
};

/**
 * Formulario inline de edicion de contacto del padron (Mision 13, DEC-034):
 * solo `nombres`, `apellidos`, `documento`, `celular`. `estado` de la persona
 * y consagracion del matrimonio se muestran como texto de solo lectura --
 * tocarlos implica recalcular/crear unidades electorales, fuera de alcance.
 *
 * No existe ningun patron de modal en este codebase: se sigue el mismo
 * estilo de formulario plano que `CrearVotacionPage.tsx`, montado inline
 * debajo de la fila que se esta editando.
 */
export function PersonaEditForm({ persona, onCancel, onGuardado }: PersonaEditFormProps) {
  const { operador } = useOperador();

  const [nombres, setNombres] = useState(persona.nombres);
  const [apellidos, setApellidos] = useState(persona.apellidos);
  const [documento, setDocumento] = useState(persona.documento ?? "");
  const [celular, setCelular] = useState(persona.celular ?? "");

  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [avisoDuplicado, setAvisoDuplicado] = useState<string | null>(null);

  async function guardar(confirmarDuplicado: boolean) {
    if (!operador.trim() || guardando) return;
    setGuardando(true);
    setError(null);
    if (!confirmarDuplicado) {
      setAvisoDuplicado(null);
    }
    try {
      const respuesta = await actualizarPersona(persona.id, {
        nombres: nombres.trim(),
        apellidos: apellidos.trim(),
        documento: documento.trim(),
        celular: celular.trim(),
        usuario: operador.trim(),
        confirmar_duplicado_celular: confirmarDuplicado,
      });
      setAvisoDuplicado(null);
      onGuardado(respuesta);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409 && err.detail) {
        // El detalle del 409 ya viene redactado en espanol por el backend
        // (incluye el nombre de la otra persona): se muestra tal cual en vez
        // de pasar por `mensajeDeError`, que lo generalizaria y perderia esa
        // informacion. No bloquea: el operador puede confirmar igual.
        setAvisoDuplicado(err.detail);
      } else {
        setError(mensajeDeError(err));
      }
    } finally {
      setGuardando(false);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    void guardar(false);
  }

  return (
    <tr>
      <td colSpan={7}>
        <form className="filters" onSubmit={handleSubmit} style={{ alignItems: "flex-end" }}>
          <div className="field">
            <label htmlFor={`edit-nombres-${persona.id}`}>Nombres</label>
            <input
              id={`edit-nombres-${persona.id}`}
              className="text-input"
              value={nombres}
              disabled={guardando}
              onChange={(e) => setNombres(e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor={`edit-apellidos-${persona.id}`}>Apellidos</label>
            <input
              id={`edit-apellidos-${persona.id}`}
              className="text-input"
              value={apellidos}
              disabled={guardando}
              onChange={(e) => setApellidos(e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor={`edit-documento-${persona.id}`}>Documento</label>
            <input
              id={`edit-documento-${persona.id}`}
              className="text-input"
              value={documento}
              disabled={guardando}
              onChange={(e) => setDocumento(e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor={`edit-celular-${persona.id}`}>Celular</label>
            <input
              id={`edit-celular-${persona.id}`}
              className="text-input"
              value={celular}
              disabled={guardando}
              onChange={(e) => setCelular(e.target.value)}
            />
          </div>
          <div className="field">
            <span className="hint-text">Estado (solo lectura)</span>
            <span data-testid="persona-estado-solo-lectura">{persona.estado}</span>
          </div>
          <div className="field">
            <span className="hint-text">Consagrado (solo lectura)</span>
            <span data-testid="persona-consagrado-solo-lectura">
              {persona.es_consagrado === null ? "—" : persona.es_consagrado ? "Sí" : "No"}
            </span>
          </div>

          <button type="submit" className="primary-button" disabled={guardando || !operador.trim()}>
            {guardando ? <Loader2 size={18} className="spin" /> : null}
            {guardando ? "Guardando..." : "Guardar"}
          </button>
          <button type="button" className="secondary-button" disabled={guardando} onClick={onCancel}>
            Cancelar
          </button>
          {!operador.trim() && (
            <span className="hint-text">Ingresá tu nombre de operador arriba para poder guardar.</span>
          )}
        </form>

        {avisoDuplicado && (
          <div className="warning-banner">
            <p>{avisoDuplicado}</p>
            <button
              type="button"
              className="secondary-button"
              disabled={guardando}
              onClick={() => void guardar(true)}
            >
              Confirmar y guardar igual
            </button>
          </div>
        )}

        {error && (
          <p className="error-message" role="alert">
            {error}
          </p>
        )}
      </td>
    </tr>
  );
}
