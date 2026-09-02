/**
 * Link discreto al panel administrativo (`frontend-admin/`), fijo abajo a la
 * izquierda en todas las paginas de este frontend de votacion.
 *
 * `frontend/` y `frontend-admin/` son dos builds de Vite separados (puertos
 * distintos en desarrollo). La URL es configurable via `VITE_ADMIN_PANEL_URL`
 * para cuando ambos se sirvan bajo el mismo dominio en produccion (por
 * ejemplo, dos componentes de una misma app de DigitalOcean App Platform,
 * con rutas "/" y "/admin"): en ese caso `VITE_ADMIN_PANEL_URL=/admin` hace
 * que el link sea relativo al mismo dominio, sin CORS ni puerto de por
 * medio. Sin esa variable, el valor por defecto depende del modo: en
 * desarrollo (`vite dev`) apunta al puerto por defecto de `frontend-admin/`
 * (5174, ver `frontend-admin/vite.config.ts`); en un build de produccion sin
 * la variable configurada, cae a la misma ruta relativa "/admin".
 */
const adminPanelUrl =
  import.meta.env.VITE_ADMIN_PANEL_URL?.trim() ||
  (import.meta.env.DEV ? "http://localhost:5174" : "/admin");

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <a href={adminPanelUrl}>Panel administrativo</a>
    </footer>
  );
}
