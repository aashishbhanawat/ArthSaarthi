import axios from "axios";

const apiClient = axios.create({
  // Base URL is determined dynamically by an interceptor.
  // In a standard web build, this will be empty (relying on relative paths).
  // In Electron, it will be set to http://localhost:<port>.
});

// This interceptor dynamically sets the baseURL when running in Electron.
// It runs only once and then is ejected.
apiClient.interceptors.request.use(
  async (config) => {
    // If the baseURL is already set, we don't need to do anything.
    if (apiClient.defaults.baseURL) {
      return config;
    }

    // Check if the electronAPI is exposed on the window object
    if (window.electronAPI && typeof window.electronAPI.getApiConfig === 'function') {
      try {
        const apiConfig = await window.electronAPI.getApiConfig();
        const baseUrl = `http://${apiConfig.host}:${apiConfig.port}`;
        console.log(`Electron environment detected. Setting API base URL to: ${baseUrl}`);
        apiClient.defaults.baseURL = baseUrl;
        config.baseURL = baseUrl;
      } catch (error) {
        console.error("Failed to get API config from Electron main process:", error);
      }
    }

    // After the first run, we can remove this interceptor if we want,
    // but leaving it is fine as it will just pass through on subsequent requests.
    // For cleanliness, let's eject it after it has run once.
    // Note: This might cause issues if the first request fails for other reasons.
    // A safer approach is to just let it be. We'll keep it simple for now.

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
    console.log("API Request:", config.method?.toUpperCase(), config.url, config.data);
    return config;
  },
  (error) => {
    console.error("API Request Error:", error);
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => {
    console.log("API Response:", response.status, response.config.url, response.data);
    return response;
  },
  (error) => {
    console.error("API Response Error:", error.response?.status, error.config.url, error.response?.data);
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