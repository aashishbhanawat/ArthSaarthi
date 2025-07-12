import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
});

// We can add interceptors here later to automatically add the auth token
// to every request.

export default api;