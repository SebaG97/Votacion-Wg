import { BrowserRouter, Route, Routes } from "react-router-dom";

import { HomePage } from "./routes/HomePage";
import { VotacionPage } from "./routes/VotacionPage";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<VotacionPage />} />
        <Route path="/estado" element={<HomePage />} />
      </Routes>
    </BrowserRouter>
  );
}
