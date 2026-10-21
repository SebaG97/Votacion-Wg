/**
 * Ilustracion propia (sin derechos de terceros) del Santuario de
 * Schoenstatt: capilla blanca de techo de tejas, torre con cruz y puerta en
 * arco, sobre un cielo calido con rayos. Decorativa: `aria-hidden`.
 */
export function SantuarioIlustracion({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 320 200"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      focusable="false"
    >
      <defs>
        <linearGradient id="cielo" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#1d4174" />
          <stop offset="0.55" stopColor="#5687c4" />
          <stop offset="1" stopColor="#f3dfae" />
        </linearGradient>
        <radialGradient id="resplandor" cx="0.5" cy="0.32" r="0.5">
          <stop offset="0" stopColor="#fff6dc" stopOpacity="0.9" />
          <stop offset="1" stopColor="#fff6dc" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="pared" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#fffdf8" />
          <stop offset="1" stopColor="#ece4d4" />
        </linearGradient>
        <linearGradient id="teja" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#b5562f" />
          <stop offset="1" stopColor="#8e3f22" />
        </linearGradient>
      </defs>

      <rect width="320" height="200" fill="url(#cielo)" />
      <g stroke="#fff6dc" strokeOpacity="0.35" strokeWidth="2">
        <line x1="160" y1="62" x2="20" y2="0" />
        <line x1="160" y1="62" x2="90" y2="0" />
        <line x1="160" y1="62" x2="160" y2="0" />
        <line x1="160" y1="62" x2="230" y2="0" />
        <line x1="160" y1="62" x2="300" y2="0" />
      </g>
      <rect width="320" height="200" fill="url(#resplandor)" />

      {/* Arboles */}
      <g fill="#2f5d3a">
        <ellipse cx="40" cy="168" rx="34" ry="26" />
        <ellipse cx="78" cy="176" rx="26" ry="18" fill="#3b6f47" />
        <ellipse cx="282" cy="166" rx="36" ry="28" />
        <ellipse cx="246" cy="178" rx="22" ry="15" fill="#3b6f47" />
      </g>

      {/* Nave */}
      <polygon points="96,108 150,78 204,108" fill="url(#teja)" />
      <rect x="104" y="106" width="92" height="66" fill="url(#pared)" />
      <path d="M140 172 v-30 a10 10 0 0 1 20 0 v30 z" fill="#6b4226" />
      <path d="M150 132 v40" stroke="#4e2f1a" strokeWidth="1.2" />
      <circle cx="150" cy="118" r="6" fill="#d9b45a" stroke="#a67c22" strokeWidth="1.2" />
      <path d="M116 150 v-14 a5 5 0 0 1 10 0 v14 z" fill="#5687c4" />
      <path d="M174 150 v-14 a5 5 0 0 1 10 0 v14 z" fill="#5687c4" />

      {/* Torre */}
      <rect x="196" y="74" width="26" height="98" fill="url(#pared)" />
      <polygon points="192,76 209,44 226,76" fill="url(#teja)" />
      <path d="M203 98 v-8 a6 6 0 0 1 12 0 v8 z" fill="#1d4174" />
      <g stroke="#d9b45a" strokeWidth="3" strokeLinecap="round">
        <line x1="209" y1="22" x2="209" y2="44" />
        <line x1="202" y1="29" x2="216" y2="29" />
      </g>

      {/* Suelo */}
      <rect x="0" y="172" width="320" height="28" fill="#c9b38a" />
      <rect x="0" y="172" width="320" height="3" fill="#b39c72" />
    </svg>
  );
}
