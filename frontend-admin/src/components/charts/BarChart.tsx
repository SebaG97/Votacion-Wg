export type BarChartDatum = {
  key: string | number;
  label: string;
  /** Valor numerico crudo, solo para calcular el ancho de la barra. */
  value: number;
  /** Texto ya formateado (ej. "42" o "63.5%"), mostrado en la punta de la barra. */
  displayValue: string;
  /** Color de la barra (rol de "status", ej. habilitada/bloqueada). Sin esto,
   * usa el color unico por defecto (grafico de una sola serie). */
  color?: string;
};

type BarChartProps = {
  data: BarChartDatum[];
  /** Texto accesible que resume el grafico completo (rol="img"). La misma
   * informacion ya esta en la tabla de al lado -- este grafico es un resumen
   * visual adicional, no la unica forma de leer los datos. */
  ariaLabel: string;
  /** Escala fija del eje (ej. 1 para porcentajes de 0 a 100%). Sin esto,
   * escala contra el maximo de `data` -- correcto para comparar categorias
   * entre si, pero enganoso para porcentajes (una participacion del 60% no
   * deberia verse como barra llena solo porque es la mas alta de la lista). */
  maxValue?: number;
  testId?: string;
};

/**
 * Barras horizontales, una fila por categoria (Mision 13, DEC-035). Sin
 * libreria de graficos: 5 usos en todo el panel, sin necesidad de
 * interactividad mas alla de un tooltip nativo por barra (`title`). Sigue el
 * spec de barras de la skill `dataviz` (grosor <=24px, extremos redondeados,
 * separador de 2px entre barras) adaptado a un layout de "meter" -- cada fila
 * tiene su propio track, no un eje compartido, asi que ambos extremos van
 * redondeados en vez de solo la punta.
 *
 * Sin libreria de graficos, la tabla ya existente al lado cubre el rol de
 * "vista de tabla" que pide la skill como respaldo de accesibilidad.
 */
export function BarChart({ data, ariaLabel, maxValue, testId }: BarChartProps) {
  const escala = maxValue ?? Math.max(1, ...data.map((d) => d.value));

  return (
    <div className="bar-chart" role="img" aria-label={ariaLabel} data-testid={testId}>
      {data.map((d) => {
        const porcentaje = Math.max(0, Math.min(100, (d.value / escala) * 100));
        return (
          <div className="bar-chart-row" key={d.key}>
            <span className="bar-chart-label" title={d.label}>
              {d.label}
            </span>
            <div className="bar-chart-track">
              <div
                className="bar-chart-fill"
                style={{ width: `${porcentaje}%`, background: d.color }}
                title={`${d.label}: ${d.displayValue}`}
              />
            </div>
            <span className="bar-chart-value">{d.displayValue}</span>
          </div>
        );
      })}
    </div>
  );
}
