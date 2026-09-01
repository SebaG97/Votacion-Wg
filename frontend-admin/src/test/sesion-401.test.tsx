import { useEffect } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { obtenerAdminToken, guardarAdminToken } from "../api/adminToken";
import { apiGet } from "../api/client";
import { RequireAuth } from "../components/RequireAuth";
import { AuthProvider } from "../context/AuthContext";
import { OperadorProvider } from "../context/OperadorContext";

function respuestaFalsa(status: number) {
  return {
    ok: false,
    status,
    json: async () => ({ detail: "Token administrativo invalido o ausente." }),
  } as Response;
}

function PaginaProtegidaQueLlamaALaApi() {
  useEffect(() => {
    apiGet("/votaciones").catch(() => {
      // El 401/403 ya dispara la limpieza de sesion via `client.ts`; esta
      // pantalla no necesita hacer nada mas con el error.
    });
  }, []);
  return <p>Contenido protegido</p>;
}

function renderApp() {
  return render(
    <MemoryRouter initialEntries={["/protegida"]}>
      <AuthProvider>
        <OperadorProvider>
          <Routes>
            <Route path="/login" element={<p>Pantalla de login</p>} />
            <Route
              path="/protegida"
              element={
                <RequireAuth>
                  <PaginaProtegidaQueLlamaALaApi />
                </RequireAuth>
              }
            />
          </Routes>
        </OperadorProvider>
      </AuthProvider>
    </MemoryRouter>,
  );
}

/**
 * Criterio de aceptacion de la Mision 10: "un 401/403 de cualquier endpoint
 * administrativo debe volver a la pantalla de login y limpiar el token
 * guardado". Este test ejercita el camino completo -- `client.ts` detecta el
 * 401/403, `AuthContext` lo escucha y limpia el token, `RequireAuth` deja de
 * ver un token y redirige -- en vez de solo probar una pieza aislada.
 */
describe("un 401/403 real de un endpoint administrativo vuelve al login", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    guardarAdminToken(null);
  });

  it.each([401, 403])("status %i limpia el token guardado y redirige a /login", async (status) => {
    guardarAdminToken("token-invalido");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(respuestaFalsa(status)));

    renderApp();

    expect(screen.getByText("Contenido protegido")).toBeInTheDocument();

    await waitFor(() => expect(screen.getByText("Pantalla de login")).toBeInTheDocument());
    expect(obtenerAdminToken()).toBeNull();
  });
});
