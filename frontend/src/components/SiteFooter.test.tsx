import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SiteFooter } from "./SiteFooter";

describe("SiteFooter", () => {
  it("muestra un link al panel administrativo", () => {
    render(<SiteFooter />);

    const link = screen.getByRole("link", { name: "Panel administrativo" });
    expect(link).toBeInTheDocument();
    // En modo test (`vite dev`/`vitest`, `import.meta.env.DEV === true`) sin
    // `VITE_ADMIN_PANEL_URL` configurada, cae al puerto por defecto de
    // `frontend-admin/` (`frontend-admin/vite.config.ts`).
    expect(link).toHaveAttribute("href", "http://localhost:5174");
  });
});
