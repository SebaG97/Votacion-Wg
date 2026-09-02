import { BrowserRouter, Route, Routes } from "react-router-dom";

import { RequireAuth } from "./components/RequireAuth";
import { AuthProvider } from "./context/AuthContext";
import { OperadorProvider } from "./context/OperadorContext";
import { CrearVotacionPage } from "./routes/CrearVotacionPage";
import { DashboardPage } from "./routes/DashboardPage";
import { ImportacionesPage } from "./routes/ImportacionesPage";
import { IncidenciasPage } from "./routes/IncidenciasPage";
import { LoginPage } from "./routes/LoginPage";
import { PadronPage } from "./routes/PadronPage";
import { VotacionDetailPage } from "./routes/VotacionDetailPage";

export function App() {
  return (
    <AuthProvider>
      <OperadorProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/"
              element={
                <RequireAuth>
                  <DashboardPage />
                </RequireAuth>
              }
            />
            <Route
              path="/votaciones/nueva"
              element={
                <RequireAuth>
                  <CrearVotacionPage />
                </RequireAuth>
              }
            />
            <Route
              path="/votaciones/:id"
              element={
                <RequireAuth>
                  <VotacionDetailPage />
                </RequireAuth>
              }
            />
            <Route
              path="/incidencias"
              element={
                <RequireAuth>
                  <IncidenciasPage />
                </RequireAuth>
              }
            />
            <Route
              path="/importaciones"
              element={
                <RequireAuth>
                  <ImportacionesPage />
                </RequireAuth>
              }
            />
            <Route
              path="/padron"
              element={
                <RequireAuth>
                  <PadronPage />
                </RequireAuth>
              }
            />
          </Routes>
        </BrowserRouter>
      </OperadorProvider>
    </AuthProvider>
  );
}
