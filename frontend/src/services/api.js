/**
 * Axios base instance.
 * All API calls go through this — base URL from env, 
 * auto JSON headers, centralised error interceptor.
 */

import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
  timeout: 10000,
});

// Response interceptor — log errors in dev
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (import.meta.env.DEV) {
      console.error("[API Error]", error.response?.status, error.response?.data);
    }
    return Promise.reject(error);
  }
);

export default api;