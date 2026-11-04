import { useCallback, useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, Loader2, Maximize, X } from "lucide-react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";

import {
  listarOpciones,
  listarVotaciones,
  obtenerEstadoOperativo,
  obtenerResultados,
  urlFotoOpcion,
  type Opcion,
  type VotacionResultados,
} from "../api/votaciones";
import { Confeti } from "../components/presentacion/Confeti";
import { useContador } from "../components/presentacion/useContador";
import { mensajeDeError } from "../lib/errores";

export type CandidatoPresentacion = {
  id: number;
  nombre: string;
  votos: number;
  porcentaje: number;
  fotoUrl: string | null;
};

export type DatosPresentacion = {
  nombre: string;
  totalVotos: number;
  habilitadas: number;
  candidatos: CandidatoPresentacion[];
  ensayo: boolean;
};

const PASOS = ["portada", "participacion", "candidatos", "ganador"] as const;
type Paso = (typeof PASOS)[number];

/** Duracion del crecimiento de las barras: el momento de suspenso. */
const DURACION_BARRAS_MS = 6000;

function prefiereMenosMovimiento(): boolean {
  return typeof window !== "undefined" && !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
}

function ordenarComoPapeleta(opciones: Opcion[]): Opcion[] {
  return [...opciones].sort((a, b) => (a.orden ?? a.id) - (b.orden ?? b.id) || a.id - b.id);
}

/** Datos reales: solo se llama con la votacion ya en RESULTADOS_REVELADOS. */
export function datosReales(
  nombre: string,
  votacionId: number,
  resultados: VotacionResultados,
  opciones: Opcion[],
): DatosPresentacion {
  const porId = new Map(resultados.totales_por_opcion.map((o) => [o.opcion_id, o]));
  return {
    nombre,
    totalVotos: resultados.total_votos,
    habilitadas: resultados.totales_por_tipo_unidad.reduce((s, t) => s + t.unidades_habilitadas, 0),
    candidatos: ordenarComoPapeleta(opciones).map((o) => ({
      id: o.id,
      nombre: o.nombre,
      votos: porId.get(o.id)?.votos ?? 0,
      porcentaje: porId.get(o.id)?.porcentaje ?? 0,
      fotoUrl: o.tiene_foto ? urlFotoOpcion(votacionId, o.id) : null,
    })),
    ensayo: false,
  };
}

/** Datos ficticios para ensayar el proyector sin ver nada real (DEC-044). */
export function datosEnsayo(
  nombre: string,
  votacionId: number,
  opciones: Opcion[],
  habilitadasReales: number,
): DatosPresentacion {
  const habilitadas = habilitadasReales > 0 ? habilitadasReales : 300;
  const total = Math.round(habilitadas * 0.8);
  const ordenadas = ordenarComoPapeleta(opciones);
  const pesos = ordenadas.map(() => 0.5 + Math.random());
  const sumaPesos = pesos.reduce((s, p) => s + p, 0) || 1;
  let restantes = total;
  const votos = pesos.map((p, i) => {
    if (i === pesos.length - 1) return restantes;
    const v = Math.round((p / sumaPesos) * total);
    restantes -= v;
    return v;
  });
  return {
    nombre,
    totalVotos: total,
    habilitadas,
    candidatos: ordenadas.map((o, i) => ({
      id: o.id,
      nombre: o.nombre,
      votos: votos[i],
      porcentaje: total ? (votos[i] / total) * 100 : 0,
      fotoUrl: o.tiene_foto ? urlFotoOpcion(votacionId, o.id) : null,
    })),
    ensayo: true,
  };
}

/**
 * Presentacion en vivo de los resultados (DEC-044), pensada para proyectar
 * en el salon con los votantes presentes. Avanza por pasos con la barra
 * espaciadora, las flechas o un clic, para que quien presenta maneje el
 * ritmo. Con `?ensayo=1` usa datos ficticios y nunca llama a
 * `obtenerResultados`; sin eso, solo los pide si la votacion ya esta en
 * RESULTADOS_REVELADOS.
 */
export function PresentacionPage() {
  const { id } = useParams<{ id: string }>();
  const votacionId = Number(id);
  const [searchParams] = useSearchParams();
  const ensayo = searchParams.get("ensayo") === "1";
  const navigate = useNavigate();

  const [datos, setDatos] = useState<DatosPresentacion | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [indicePaso, setIndicePaso] = useState(0);
  const raizRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelado = false;
    async function cargar() {
      try {
        const [votaciones, opciones] = await Promise.all([
          listarVotaciones(),
          listarOpciones(votacionId),
        ]);
        const votacion = votaciones.find((v) => v.id === votacionId);
        if (!votacion) {
          if (!cancelado) setError("No se encontró la votación.");
          return;
        }
        if (ensayo) {
          const estado = await obtenerEstadoOperativo(votacionId);
          if (!cancelado) {
            setDatos(
              datosEnsayo(votacion.nombre, votacionId, opciones, estado.unidades_por_estado.habilitada),
            );
          }
          return;
        }
        if (votacion.estado !== "RESULTADOS_REVELADOS") {
          if (!cancelado) {
            setAviso(
              "Los resultados todavía no se revelaron. Volvé al panel y usá “Revelar resultados en vivo”, o abrí el ensayo.",
            );
          }
          return;
        }
        const resultados = await obtenerResultados(votacionId);
        if (!cancelado) setDatos(datosReales(votacion.nombre, votacionId, resultados, opciones));
      } catch (err) {
        if (!cancelado) setError(mensajeDeError(err));
      }
    }
    void cargar();
    return () => {
      cancelado = true;
    };
  }, [votacionId, ensayo]);

  const avanzar = useCallback(() => setIndicePaso((i) => Math.min(PASOS.length - 1, i + 1)), []);
  const retroceder = useCallback(() => setIndicePaso((i) => Math.max(0, i - 1)), []);
  const salir = useCallback(() => {
    if (document.fullscreenElement) void document.exitFullscreen?.();
    navigate(`/votaciones/${votacionId}`);
  }, [navigate, votacionId]);
  const pantallaCompleta = useCallback(() => {
    if (document.fullscreenElement) {
      void document.exitFullscreen?.();
    } else {
      void raizRef.current?.requestFullscreen?.().catch(() => {});
    }
  }, []);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ([" ", "ArrowRight", "Enter", "PageDown"].includes(e.key)) {
        e.preventDefault();
        avanzar();
      } else if (["ArrowLeft", "Backspace", "PageUp"].includes(e.key)) {
        e.preventDefault();
        retroceder();
      } else if (e.key === "f" || e.key === "F") {
        pantallaCompleta();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [avanzar, retroceder, pantallaCompleta]);

  const paso: Paso = PASOS[indicePaso];

  return (
    <div
      ref={raizRef}
      className="presentacion"
      data-testid="presentacion"
      data-paso={paso}
      onClick={(e) => {
        if ((e.target as HTMLElement).closest(".presentacion-controles")) return;
        if (datos) avanzar();
      }}
    >
      <div className="presentacion-fondo" aria-hidden="true" />

      {datos?.ensayo && (
        <div className="presentacion-ensayo" role="note">
          ENSAYO · datos ficticios
        </div>
      )}

      {error && (
        <div className="presentacion-mensaje">
          <p role="alert">{error}</p>
        </div>
      )}
      {aviso && (
        <div className="presentacion-mensaje">
          <p role="alert">{aviso}</p>
        </div>
      )}
      {!datos && !error && !aviso && (
        <div className="presentacion-mensaje">
          <Loader2 size={40} className="spin" />
        </div>
      )}

      {datos && paso === "portada" && <Portada datos={datos} />}
      {datos && paso === "participacion" && <Participacion datos={datos} />}
      {datos && (paso === "candidatos" || paso === "ganador") && (
        <Candidatos datos={datos} mostrarGanador={paso === "ganador"} />
      )}

      <div className="presentacion-controles" aria-label="Controles de la presentación">
        <button type="button" onClick={retroceder} disabled={indicePaso === 0} aria-label="Anterior">
          <ChevronLeft size={20} />
        </button>
        <span className="presentacion-progreso">
          {indicePaso + 1} / {PASOS.length}
        </span>
        <button
          type="button"
          onClick={avanzar}
          disabled={!datos || indicePaso === PASOS.length - 1}
          aria-label="Siguiente"
        >
          <ChevronRight size={20} />
        </button>
        <button type="button" onClick={pantallaCompleta} aria-label="Pantalla completa">
          <Maximize size={18} />
        </button>
        <button type="button" onClick={salir} aria-label="Salir de la presentación">
          <X size={18} />
        </button>
      </div>
    </div>
  );
}

function Portada({ datos }: { datos: DatosPresentacion }) {
  return (
    <div className="presentacion-escena presentacion-portada">
      <p className="presentacion-eyebrow">Resultados</p>
      <h1 className="presentacion-titulo">{datos.nombre}</h1>
      <p className="presentacion-pista">Presioná la barra espaciadora para comenzar</p>
    </div>
  );
}

function Participacion({ datos }: { datos: DatosPresentacion }) {
  const duracion = prefiereMenosMovimiento() ? 0 : 2500;
  const votos = useContador(datos.totalVotos, duracion, true);
  const fraccion = datos.habilitadas ? Math.min(1, datos.totalVotos / datos.habilitadas) : 0;
  const porcentaje = useContador(Math.round(fraccion * 1000) / 10, duracion, true, 1);
  const radio = 120;
  const circunferencia = 2 * Math.PI * radio;
  const progreso = datos.habilitadas ? Math.min(1, votos / datos.habilitadas) : 0;

  return (
    <div className="presentacion-escena presentacion-participacion">
      <p className="presentacion-eyebrow">Participación</p>
      <div className="presentacion-anillo">
        <svg viewBox="0 0 300 300" aria-hidden="true">
          <circle cx="150" cy="150" r={radio} className="anillo-track" />
          <circle
            cx="150"
            cy="150"
            r={radio}
            className="anillo-fill"
            strokeDasharray={circunferencia}
            strokeDashoffset={circunferencia * (1 - progreso)}
          />
        </svg>
        <div className="presentacion-anillo-centro">
          <span className="presentacion-numero-grande" data-testid="total-votos">
            {votos}
          </span>
          <span className="presentacion-subtexto">votos emitidos</span>
        </div>
      </div>
      {datos.habilitadas > 0 && (
        <p className="presentacion-detalle">
          <strong>{porcentaje.toFixed(1)}%</strong> de participación · {datos.habilitadas} votos
          habilitados
        </p>
      )}
    </div>
  );
}

function Candidatos({ datos, mostrarGanador }: { datos: DatosPresentacion; mostrarGanador: boolean }) {
  const maximo = Math.max(0, ...datos.candidatos.map((c) => c.votos));
  const ganadores = datos.candidatos.filter((c) => c.votos === maximo && maximo > 0);
  const empate = ganadores.length > 1;
  const escala = Math.max(1, maximo);
  const duracion = prefiereMenosMovimiento() || mostrarGanador ? 0 : DURACION_BARRAS_MS;

  return (
    <div className="presentacion-escena presentacion-candidatos">
      <p className="presentacion-eyebrow">
        {mostrarGanador ? (empate ? "¡Empate!" : "¡Felicitaciones!") : "Conteo de votos"}
      </p>
      {mostrarGanador && !empate && ganadores[0] && (
        <p className="presentacion-ganador-nombre" data-testid="ganador">
          {ganadores[0].nombre}
        </p>
      )}
      <div
        className={`presentacion-columnas${mostrarGanador ? " con-ganador" : ""}`}
        style={{ ["--columnas" as string]: datos.candidatos.length }}
      >
        {datos.candidatos.map((c, i) => (
          <ColumnaCandidato
            key={c.id}
            candidato={c}
            escala={escala}
            duracion={duracion * (c.votos / escala)}
            color={i}
            ganador={mostrarGanador && ganadores.some((g) => g.id === c.id)}
            atenuado={mostrarGanador && !ganadores.some((g) => g.id === c.id)}
          />
        ))}
      </div>
      {mostrarGanador && ganadores.length > 0 && !empate && !prefiereMenosMovimiento() && <Confeti />}
    </div>
  );
}

function ColumnaCandidato({
  candidato,
  escala,
  duracion,
  color,
  ganador,
  atenuado,
}: {
  candidato: CandidatoPresentacion;
  escala: number;
  duracion: number;
  color: number;
  ganador: boolean;
  atenuado: boolean;
}) {
  // Todas las barras suben a la misma velocidad: la que tiene menos votos se
  // detiene antes y la ganadora sigue subiendo sola hasta el final.
  const votos = useContador(candidato.votos, duracion, true, 0, "lineal");
  const porcentajeFinal = candidato.porcentaje;
  const terminado = votos === candidato.votos;
  const alto = (votos / escala) * 100;

  return (
    <div
      className={`presentacion-columna color-${color % 6}${ganador ? " ganador" : ""}${atenuado ? " atenuado" : ""}`}
      data-testid={`columna-${candidato.id}`}
    >
      <div className="presentacion-barra-zona">
        <div className="presentacion-barra" style={{ height: `${alto}%` }}>
          <span className="presentacion-barra-valor">
            <span className="presentacion-votos">{votos}</span>
            <span className={`presentacion-porcentaje${terminado ? " visible" : ""}`}>
              {porcentajeFinal.toFixed(1)}%
            </span>
          </span>
        </div>
      </div>
      <div className="presentacion-candidato">
        {candidato.fotoUrl ? (
          <img src={candidato.fotoUrl} alt="" className="presentacion-foto" />
        ) : (
          <div className="presentacion-foto presentacion-foto-vacia" aria-hidden="true">
            {candidato.nombre.charAt(0)}
          </div>
        )}
        <span className="presentacion-nombre">{candidato.nombre}</span>
      </div>
    </div>
  );
}
