import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const allowedHostsFromEnv = env.ALLOWED_HOSTS ? env.ALLOWED_HOSTS.split(',') : [];

  return {
    plugins: [react()],
    server: {
      host: env.VITE_DEV_SERVER_HOST || "0.0.0.0", // This is required for Docker
      port: 3000, // Explicitly set the port to 3000
      allowedHosts: [
        "frontend",
        ...allowedHostsFromEnv,
      ],
      proxy: {
        "/api": {
          target: env.VITE_API_PROXY_TARGET || "http://backend:8000",
          changeOrigin: true,
        },
      },
    },
  };
});