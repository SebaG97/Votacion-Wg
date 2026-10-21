import { SantuarioIlustracion } from "./SantuarioIlustracion";

/**
 * Encabezado de la pagina de votacion con la tematica del Santuario de
 * Schoenstatt (Asuncion). En el primer paso se muestra completo; en los
 * siguientes, compacto para no empujar la papeleta hacia abajo.
 */
export function EncabezadoSantuario({ compacto = false }: { compacto?: boolean }) {
  return (
    <header className={`encabezado ${compacto ? "compacto" : ""}`}>
      {!compacto && <SantuarioIlustracion className="encabezado-ilustracion" />}
      <p className="encabezado-movimiento">
        Liga Apostólica de Familias · Movimiento Apostólico de Schoenstatt
      </p>
      <h1 className="encabezado-titulo">
        Elección de Jefes de Miembros de Liga
        <span className="encabezado-periodo">Período 2027 – 2028</span>
      </h1>
      {!compacto && (
        <p className="encabezado-lema">
          «Nada sin ti, nada sin nosotros»
        </p>
      )}
    </header>
  );
}

export function PieSantuario() {
  return (
    <footer className="pie">
      <span className="pie-cruz" aria-hidden="true">
        ✝
      </span>
      <p>Madre, Reina y Victoriosa Tres Veces Admirable de Schoenstatt</p>
      <p className="pie-lugar">Asunción · Paraguay</p>
    </footer>
  );
}
