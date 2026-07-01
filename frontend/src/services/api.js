/**
 * Axios base instance + all API calls.
 * Sources section added in Day 3.
 */

import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (import.meta.env.DEV) {
      console.error("[API Error]", error.response?.status, error.response?.data);
    }
    return Promise.reject(error);
  }
);

// ── Jobs ──────────────────────────────────────────────────────────
export const jobsApi = {
  list: (params = {}) => api.get("/jobs/", { params }),
  get:  (id)          => api.get(`/jobs/${id}`),
};

// ── Sources ───────────────────────────────────────────────────────
export const sourcesApi = {
  list:       ()               => api.get("/sources/"),
  health:     ()               => api.get("/sources/health"),
  tiers:      ()               => api.get("/sources/tiers"),
  select:     (source_id, is_enabled) =>
                api.post("/sources/select", { source_id, is_enabled }),
  setMode:    (mode, source_ids = []) =>
                api.post("/sources/mode", { mode, source_ids }),
};

export default api;