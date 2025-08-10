import axios from "axios";

const apiClient = axios.create({
  // The base URL is no longer needed here because we are using a proxy.
  // The browser will make requests to the same origin (i.e., /api/...),
  // and Vite's dev server will forward them to the backend.
}); 

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