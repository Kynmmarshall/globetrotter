import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Dev-time proxy so the Vite dev server behaves like the same origin the
// gateway will present in Docker: relative "/api/v1/..." and "/ws/chat"
// calls just work without CORS, whether the backend runs via Docker Compose
// (gateway on GATEWAY_PORT) or services run directly on the host.
const GATEWAY_URL = process.env.VITE_GATEWAY_URL ?? "http://localhost:8090";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": "/src",
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": { target: GATEWAY_URL, changeOrigin: true },
      "/static": { target: GATEWAY_URL, changeOrigin: true },
      "/ws": { target: GATEWAY_URL, changeOrigin: true, ws: true },
    },
  },
});
