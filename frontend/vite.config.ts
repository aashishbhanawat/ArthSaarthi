import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import packageJson from './package.json';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const allowedHostsFromEnv = env.ALLOWED_HOSTS ? env.ALLOWED_HOSTS.split(',') : [];
  // Determine the API proxy target based on the environment variable
  const apiProxyTarget = env.VITE_API_PROXY_TARGET || "http://backend:8000";

  return {
    base: './',
    define: {
      // Expose the app version from package.json to the app
      'import.meta.env.VITE_APP_VERSION': JSON.stringify(packageJson.version),
    },
    plugins: [react()],
    resolve: {
      alias: {
        '~': path.resolve(__dirname, 'src'),
      },
    },
    server: {
      host: "0.0.0.0", // This is required for Docker
      port: 3000, // Explicitly set the port to 3000
      allowedHosts: [
        "frontend",
        "localhost",
        "127.0.0.1",
        ...allowedHostsFromEnv,
      ],
      proxy: {
        "/api": {
          target: apiProxyTarget, // Use the dynamically determined target
        },
      },
    },
  };
});