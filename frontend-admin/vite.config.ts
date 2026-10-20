import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// En producción el admin se sirve bajo /admin (ruta de DO App Platform).
export default defineConfig(({ command }) => ({
  base: command === "build" ? "/admin/" : "/",
  plugins: [react()],
  server: {
    port: 5174,
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    globals: true,
  },
}));
