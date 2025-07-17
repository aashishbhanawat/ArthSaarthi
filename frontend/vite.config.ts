import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0", // This is required for Docker
    port: 3000,      // Explicitly set the port to 3000
    allowedHosts: [
      "librephotos.aashish.ai.in",
    ],
    proxy: {
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true,
      },
    },
  },
});