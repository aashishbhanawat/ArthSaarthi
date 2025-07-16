import axios from "axios";

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem("authToken");
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export  default api;


export const getAuthStatus = () => {
    return api.get("/auth/status").then((response) => response.data);
};

export const setupAdmin = (userData: any) => {
    return api.post("/auth/setup", userData).then((response) => response.data);
};

export const loginUser = async (email: string, password: string) => {
    try {
        const response = await api.post(
            "/auth/login",
            new URLSearchParams({ username: email, password: password }),
            {
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            }
        );
        return response.data;
    } catch (error: any) {
        throw error;
    }
};

export const getCurrentUser = () => {
    return api.get("/users/me").then((response) => response.data);
};