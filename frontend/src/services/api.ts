import axios from "axios";
import { Capacitor } from "@capacitor/core";
import PythonBackend from "../plugins/PythonBackend";

const apiClient = axios.create({
  // Base URL is determined dynamically by an interceptor.
  // In a standard web build, this will be empty (relying on relative paths).
  // In Electron, it will be set to http://localhost:<port>.
  // On Android (Capacitor), it will be set to http://127.0.0.1:<port>.
});

// Only log in development mode
const isDev = import.meta.env.DEV;

// This interceptor dynamically sets the baseURL when running in Electron or Android.
// It runs only once and then passes through on subsequent requests.
apiClient.interceptors.request.use(
  async (config) => {
    // If the baseURL is already set, we don't need to do anything.
    if (apiClient.defaults.baseURL) {
      return config;
    }

    // Path 1: Electron desktop mode
    if (window.electronAPI && typeof window.electronAPI.getApiConfig === 'function') {
      try {
        const apiConfig = await window.electronAPI.getApiConfig();
        const baseUrl = `http://${apiConfig.host}:${apiConfig.port}`;
        if (isDev) {
          console.log(`Electron environment detected. Setting API base URL to: ${baseUrl}`);
        }
        apiClient.defaults.baseURL = baseUrl;
        config.baseURL = baseUrl;
      } catch (error) {
        if (isDev) {
          console.error("Failed to get API config from Electron main process:", error);
        }
      }
    }
    // Path 2: Android (Capacitor) mode
    else if (Capacitor.isNativePlatform()) {
      try {
        const apiConfig = await PythonBackend.getApiConfig();
        const baseUrl = `http://${apiConfig.host}:${apiConfig.port}`;
        if (isDev) {
          console.log(`Android/Capacitor environment detected. Setting API base URL to: ${baseUrl}`);
        }
        apiClient.defaults.baseURL = baseUrl;
        config.baseURL = baseUrl;
      } catch (error) {
        console.error("Failed to get API config from Android backend:", error);
      }
    }
    // Path 3: Web/Docker mode — uses relative paths (Vite proxy handles /api)

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);


apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    if (isDev) {
      console.log("API Request:", config.method?.toUpperCase(), config.url);
    }
    return config;
  },
  (error) => {
    if (isDev) {
      console.error("API Request Error:", error);
    }
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => {
    if (isDev) {
      console.log("API Response:", response.status, response.config.url);
    }
    return response;
  },
  (error) => {
    if (isDev) {
      console.error("API Response Error:", error.response?.status, error.config.url, error.response?.data);
    }
    return Promise.reject(error);
  }
);

export default apiClient;

export const getAuthStatus = async () => {
  const response = await apiClient.get("/api/v1/auth/status");
  return response.data;
};

export const setupAdminUser = async (full_name: string, email: string, password: string) => {
  const userData = {
    full_name,
    email,
    password,
  };
  const response = await apiClient.post("/api/v1/auth/setup", userData);
  return response.data;
};

export const loginUser = async (email: string, password: string) => {
  const response = await apiClient.post(
    "/api/v1/auth/login",
    new URLSearchParams({ username: email, password: password }),
    {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    }
  );
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await apiClient.get("/api/v1/users/me");
  return response.data;
};

/**
 * Helper to download CSVs using the authenticated API client. 
 */
export const downloadCsv = async (url: string, filename: string) => {
  try {
    const response = await apiClient.get(url, {
      responseType: 'blob', // Important for file downloads
    });

    // Create blob link to download
    const urlBlob = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = urlBlob;
    link.setAttribute('download', filename);
    /* eslint-disable testing-library/no-node-access */
    document.body.appendChild(link);
    link.click();

    // Clean up
    if (link.parentNode) {
      link.parentNode.removeChild(link);
    }
    /* eslint-enable testing-library/no-node-access */
  } catch (error) {
    console.error(`Failed to download CSV from ${url}`, error);
  }
};