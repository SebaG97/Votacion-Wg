import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import {
  listarPadron,
  type EstadoPersona,
  type EstadoUnidadElectoral,
  type FiltrosPadron,
  type PadronPersona,
  type TipoUnidadElectoral,
} from "../api/padron";
import { mensajeDeError } from "../lib/errores";

const ESTADOS_PERSONA: EstadoPersona[] = ["ACTIVA", "BAJA_NO_ML", "BAJA_OBSERVACION"];

const ESTADOS_UNIDAD_ELECTORAL: EstadoUnidadElectoral[] = [
  "HABILITADA",
  "BLOQUEADA_POR_INCIDENCIA",
  "PENDIENTE_DEFINICION_POSTULANTES",
  "PENDIENTE_DEFINICION_BAJA",
];

const TIPOS_UNIDAD_ELECTORAL: TipoUnidadElectoral[] = [
  "MATRIMONIO_CONSAGRADO",
  "BLOQUE_NO_CONSAGRADO",
];

const TAMANIO_PAGINA = 50;

/**
 * Visor de padron (Mision 12, DEC-031): personas, su circulo, su matrimonio
 * y sus unidades electorales, filtrable y paginado. Deliberadamente no
 * incluye ni permite cruzar `Voto` -- ver DEC-031 en `docs/DECISIONES.md`:
 * este visor es para consultar quien es quien y su habilitacion el dia de la
 * votacion, no para ver que opcion eligio cada unidad.
 */
export function PadronPage() {
  const [listado, setListado] = useState<{ total: number; items: PadronPersona[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pagina, setPagina] = useState(1);

  const [circulo, setCirculo] = useState("");
  const [nombre, setNombre] = useState("");
  const [documento, setDocumento] = useState("");
  const [celular, setCelular] = useState("");
  const [estadoPersona, setEstadoPersona] = useState<EstadoPersona | "">("");
  const [estadoUnidad, setEstadoUnidad] = useState<EstadoUnidadElectoral | "">("");
  const [tipoUnidad, setTipoUnidad] = useState<TipoUnidadElectoral | "">("");

  async function cargar(paginaAConsultar: number) {
    setError(null);
    const filtros: FiltrosPadron = { pagina: paginaAConsultar, tamanio_pagina: TAMANIO_PAGINA };
    if (circulo.trim()) filtros.circulo = circulo.trim();
    if (nombre.trim()) filtros.nombre = nombre.trim();
    if (documento.trim()) filtros.documento = documento.trim();
    if (celular.trim()) filtros.celular = celular.trim();
    if (estadoPersona) filtros.estado_persona = estadoPersona;
    if (estadoUnidad) filtros.estado_unidad_electoral = estadoUnidad;
    if (tipoUnidad) filtros.tipo_unidad_electoral = tipoUnidad;

    try {
      const datos = await listarPadron(filtros);
      setListado({ total: datos.total, items: datos.items });
    } catch (err) {
      setError(mensajeDeError(err));
    }
  }

  useEffect(() => {
    void cargar(pagina);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [circulo, nombre, documento, celular, estadoPersona, estadoUnidad, tipoUnidad, pagina]);

  function conFiltro<T>(setter: (valor: T) => void) {
    return (valor: T) => {
      setPagina(1);
      setter(valor);
    };
  }

  const totalPaginas = listado ? Math.max(1, Math.ceil(listado.total / TAMANIO_PAGINA)) : 1;

  return (
    <section className="panel ancho">
      <p className="eyebrow">Padrón</p>
      <h1>Padrón</h1>
      <p className="warning-banner">
        Este visor muestra datos del padrón (personas, círculos, unidades electorales) para
        consultar el día de la votación. No muestra ni permite cruzar qué opción votó cada unidad.
      </p>

      <div className="filters">
        <input
          className="text-input"
          style={{ width: 200 }}
          placeholder="Filtrar por círculo"
          value={circulo}
          onChange={(e) => conFiltro(setCirculo)(e.target.value)}
          aria-label="Filtrar por círculo"
        />
        <input
          className="text-input"
          style={{ width: 200 }}
          placeholder="Filtrar por nombre o apellido"
          value={nombre}
          onChange={(e) => conFiltro(setNombre)(e.target.value)}
          aria-label="Filtrar por nombre"
        />
        <input
          className="text-input"
          style={{ width: 160 }}
          placeholder="Filtrar por documento"
          value={documento}
          onChange={(e) => conFiltro(setDocumento)(e.target.value)}
          aria-label="Filtrar por documento"
        />
        <input
          className="text-input"
          style={{ width: 160 }}
          placeholder="Filtrar por celular"
          value={celular}
          onChange={(e) => conFiltro(setCelular)(e.target.value)}
          aria-label="Filtrar por celular"
        />

        <select
          value={estadoPersona}
          onChange={(e) => conFiltro(setEstadoPersona)(e.target.value as EstadoPersona | "")}
          aria-label="Filtrar por estado de la persona"
        >
          <option value="">Todos los estados de persona</option>
          {ESTADOS_PERSONA.map((e) => (
            <option key={e} value={e}>
              {e}
            </option>
          ))}
        </select>

        <select
          value={estadoUnidad}
          onChange={(e) =>
            conFiltro(setEstadoUnidad)(e.target.value as EstadoUnidadElectoral | "")
          }
          aria-label="Filtrar por estado de la unidad electoral"
        >
          <option value="">Todos los estados de unidad</option>
          {ESTADOS_UNIDAD_ELECTORAL.map((e) => (
            <option key={e} value={e}>
              {e}
            </option>
          ))}
        </select>

        <select
          value={tipoUnidad}
          onChange={(e) => conFiltro(setTipoUnidad)(e.target.value as TipoUnidadElectoral | "")}
          aria-label="Filtrar por tipo de unidad electoral"
        >
          <option value="">Todos los tipos de unidad</option>
          {TIPOS_UNIDAD_ELECTORAL.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div>
          <p className="error-message" role="alert">
            {error}
          </p>
          <button type="button" className="secondary-button" onClick={() => void cargar(pagina)}>
            Reintentar
          </button>
        </div>
      )}

      {!listado && !error && (
        <p className="loading-message">
          <Loader2 size={18} className="spin" /> Cargando padrón...
        </p>
      )}

      {listado && listado.items.length === 0 && <p>No hay personas con estos filtros.</p>}

      {listado && listado.items.length > 0 && (
        <>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Documento</th>
                  <th>Celular</th>
                  <th>Estado</th>
                  <th>Círculo</th>
                  <th>Jefe</th>
                  <th>Unidades electorales</th>
                </tr>
              </thead>
              <tbody>
                {listado.items.map((p) => (
                  <tr key={p.id}>
                    <td>
                      {p.apellidos}, {p.nombres}
                    </td>
                    <td>{p.documento ?? "—"}</td>
                    <td>{p.celular ?? "—"}</td>
                    <td>{p.estado}</td>
                    <td>{p.circulo ?? "—"}</td>
                    <td>{p.es_jefe_grupo ? "Sí" : "No"}</td>
                    <td>
                      {p.unidades_electorales.length === 0
                        ? "—"
                        : p.unidades_electorales
                            .map((u) => `${u.tipo} (${u.estado ?? "sin estado"})`)
                            .join(" / ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="filters" style={{ marginTop: 16, alignItems: "center" }}>
            <button
              type="button"
              className="secondary-button"
              disabled={pagina <= 1}
              onClick={() => setPagina((p) => Math.max(1, p - 1))}
            >
              Anterior
            </button>
            <span>
              Página {pagina} de {totalPaginas} ({listado.total} personas)
            </span>
            <button
              type="button"
              className="secondary-button"
              disabled={pagina >= totalPaginas}
              onClick={() => setPagina((p) => Math.min(totalPaginas, p + 1))}
            >
              Siguiente
            </button>
          </div>
        </>
      )}
    </section>
  );
}
