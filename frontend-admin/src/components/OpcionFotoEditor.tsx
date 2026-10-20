import { useState } from "react";
import { ImagePlus, Loader2, Trash2 } from "lucide-react";

import { ApiError } from "../api/client";
import {
  quitarFotoOpcion,
  subirFotoOpcion,
  urlFotoOpcion,
  type Opcion,
} from "../api/votaciones";
import { redimensionarImagen } from "../lib/redimensionarImagen";
import { traducirErrorVotacion } from "../lib/erroresVotacion";

type OpcionFotoEditorProps = {
  opcion: Opcion;
  onCambio: (opcion: Opcion) => void;
};

/**
 * Foto del candidato de una opcion en BORRADOR (Mision 15, DEC-037). La
 * imagen se achica en el navegador antes de subirla; la vista previa usa la
 * misma URL publica que la papeleta.
 */
export function OpcionFotoEditor({ opcion, onCambio }: OpcionFotoEditorProps) {
  const [version, setVersion] = useState(() => Date.now());
  const [trabajando, setTrabajando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputId = `foto-opcion-${opcion.id}`;

  async function handleArchivo(e: React.ChangeEvent<HTMLInputElement>) {
    const archivo = e.target.files?.[0];
    e.target.value = "";
    if (!archivo || trabajando) return;
    setTrabajando(true);
    setError(null);
    let foto: Blob;
    try {
      foto = await redimensionarImagen(archivo);
    } catch {
      setError("No se pudo leer la imagen. Probá con una foto JPG o PNG.");
      setTrabajando(false);
      return;
    }
    try {
      const actualizada = await subirFotoOpcion(opcion.votacion_id, opcion.id, foto);
      setVersion(Date.now());
      onCambio(actualizada);
    } catch (err) {
      setError(err instanceof ApiError ? traducirErrorVotacion(err) : "No se pudo subir la foto.");
    } finally {
      setTrabajando(false);
    }
  }

  async function handleQuitar() {
    if (trabajando) return;
    setTrabajando(true);
    setError(null);
    try {
      onCambio(await quitarFotoOpcion(opcion.votacion_id, opcion.id));
    } catch (err) {
      setError(traducirErrorVotacion(err));
    } finally {
      setTrabajando(false);
    }
  }

  return (
    <div className="opcion-foto">
      {opcion.tiene_foto ? (
        <img
          className="opcion-foto-img"
          src={urlFotoOpcion(opcion.votacion_id, opcion.id, version)}
          alt={`Foto de ${opcion.nombre}`}
        />
      ) : (
        <div className="opcion-foto-vacia" aria-hidden="true">
          <ImagePlus size={20} />
        </div>
      )}
      <div className="opcion-foto-acciones">
        <label htmlFor={inputId} className="secondary-button opcion-foto-boton">
          {trabajando ? <Loader2 size={14} className="spin" /> : <ImagePlus size={14} />}
          {opcion.tiene_foto ? "Cambiar foto" : "Subir foto"}
        </label>
        <input
          id={inputId}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="visually-hidden"
          disabled={trabajando}
          onChange={(e) => void handleArchivo(e)}
        />
        {opcion.tiene_foto && (
          <button
            type="button"
            className="link-button opcion-foto-quitar"
            disabled={trabajando}
            onClick={() => void handleQuitar()}
          >
            <Trash2 size={14} /> Quitar
          </button>
        )}
      </div>
      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
