/**
 * TypeScript definitions for the PythonBackend Capacitor plugin.
 *
 * This plugin bridges the React frontend to the Python/FastAPI backend
 * running on Android via Chaquopy. It mirrors the Electron IPC pattern
 * (window.electronAPI.getApiConfig()) but uses Capacitor's native bridge.
 */
import { registerPlugin } from '@capacitor/core';

export interface ApiConfig {
  host: string;
  port: number;
}

export interface BackendStatus {
  running: boolean;
  port: number;
}

export interface PythonBackendPlugin {
  /**
   * Get the API configuration (host and port) for the local backend.
   * This call blocks until the backend is ready (health check passes).
   */
  getApiConfig(): Promise<ApiConfig>;

  /**
   * Get the current backend service status.
   */
  getBackendStatus(): Promise<BackendStatus>;
}

const PythonBackend = registerPlugin<PythonBackendPlugin>('PythonBackend');

export default PythonBackend;
