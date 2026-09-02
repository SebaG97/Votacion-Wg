import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { guardarAdminToken, obtenerAdminToken } from "../api/adminToken";
import { AuthProvider } from "../context/AuthContext";
import { LoginPage } from "../routes/LoginPage";

function respuestaFalsa(status: number, detail: string) {
  return {
    ok: false,
    status,
    json: async () => ({ detail }),
  } as Response;
}

function respuestaExitosa(token: string) {
  return {
    ok: true,
    status: 200,
    json: async () => ({ token }),
  } as Response;
}

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={["/login"]}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<p>Dashboard</p>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  );
}

/**
 * Mision 12 (DEC-030): el login pasa de "pegar el token crudo" a dos campos
 * (usuario/contraseña) que llaman a `POST /auth/login`. Cubre el camino
 * feliz y los tres errores que el backend puede devolver: credenciales
 * incorrectas (401), login deshabilitado por falta de configuracion (403) y
 * demasiados intentos (429, DEC-030 reusa `slowapi` de la Mision 11).
 */
describe("LoginPage: usuario y contraseña", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    guardarAdminToken(null);
  });

  it("con credenciales correctas guarda el token devuelto por el backend y entra al panel", async () => {
    const fetchMock = vi.fn().mockResolvedValue(respuestaExitosa("token-real-del-servidor"));
    vi.stubGlobal("fetch", fetchMock);
    const usuario = userEvent.setup();

    renderLogin();

    await usuario.type(screen.getByLabelText("Usuario"), "admin");
    await usuario.type(screen.getByLabelText("Contraseña"), "votacion2026");
    await usuario.click(screen.getByRole("button", { name: "Ingresar" }));

    await waitFor(() => expect(screen.getByText("Dashboard")).toBeInTheDocument());
    expect(obtenerAdminToken()).toBe("token-real-del-servidor");

    const [path, init] = fetchMock.mock.calls[0];
    expect(String(path)).toContain("/auth/login");
    expect(JSON.parse(init.body as string)).toEqual({
      usuario: "admin",
      contrasena: "votacion2026",
    });
  });

  it("con credenciales incorrectas muestra un error y no guarda ningun token", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(respuestaFalsa(401, "Usuario o contraseña incorrectos.")),
    );
    const usuario = userEvent.setup();

    renderLogin();

    await usuario.type(screen.getByLabelText("Usuario"), "admin");
    await usuario.type(screen.getByLabelText("Contraseña"), "incorrecta");
    await usuario.click(screen.getByRole("button", { name: "Ingresar" }));

    await waitFor(() =>
      expect(screen.getByText("Usuario o contraseña incorrectos.")).toBeInTheDocument(),
    );
    expect(obtenerAdminToken()).toBeNull();
  });

  it("con el login deshabilitado (403) muestra un mensaje explicito", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        respuestaFalsa(403, "Login administrativo deshabilitado: faltan variables de entorno."),
      ),
    );
    const usuario = userEvent.setup();

    renderLogin();

    await usuario.type(screen.getByLabelText("Usuario"), "admin");
    await usuario.type(screen.getByLabelText("Contraseña"), "votacion2026");
    await usuario.click(screen.getByRole("button", { name: "Ingresar" }));

    await waitFor(() =>
      expect(
        screen.getByText("Login deshabilitado: contactá a quien administra el servidor."),
      ).toBeInTheDocument(),
    );
    expect(obtenerAdminToken()).toBeNull();
  });

  it("al superar el limite de intentos (429) muestra un mensaje de reintento", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(respuestaFalsa(429, "Rate limit exceeded")),
    );
    const usuario = userEvent.setup();

    renderLogin();

    await usuario.type(screen.getByLabelText("Usuario"), "admin");
    await usuario.type(screen.getByLabelText("Contraseña"), "votacion2026");
    await usuario.click(screen.getByRole("button", { name: "Ingresar" }));

    await waitFor(() =>
      expect(
        screen.getByText("Demasiados intentos. Esperá un minuto e intentá de nuevo."),
      ).toBeInTheDocument(),
    );
  });
});
