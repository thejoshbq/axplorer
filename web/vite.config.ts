import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const pkg = JSON.parse(
  readFileSync(fileURLToPath(new URL("./package.json", import.meta.url)), "utf-8"),
) as { version: string };

export default defineConfig({
  plugins: [react()],
  define: {
    __APP_VERSION__: JSON.stringify(pkg.version),
  },
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
