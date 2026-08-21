import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    // Bind all interfaces so the dashboard is reachable from other machines
    // on the LAN. The /api proxy below still dials the backend over loopback
    // from within this process, so the backend itself stays off the network.
    host: true,
    port: 5173,
    proxy: {
      "/api": "http://localhost:8050",
    },
  },
  build: {
    outDir: "dist",
  },
});
