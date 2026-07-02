/**
 * Axios base instance + all API calls.
 * Updated Day 5: added skillsApi, watchlistApi, jobsApi enhancements.
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
  list:       (params = {}) => api.get("/jobs/", { params }),
  get:        (id)          => api.get(`/jobs/${id}`),
  markViewed: (id)          => api.post(`/jobs/${id}/view`),
  stats:      ()            => api.get("/jobs/stats"),
  highMatch:  (params = {}) => api.get("/jobs/high-match", { params }),
};

// ── Sources ───────────────────────────────────────────────────────
export const sourcesApi = {
  list:    ()                          => api.get("/sources/"),
  health:  ()                          => api.get("/sources/health"),
  tiers:   ()                          => api.get("/sources/tiers"),
  select:  (source_id, is_enabled)     => api.post("/sources/select", { source_id, is_enabled }),
  setMode: (mode, source_ids = [])     => api.post("/sources/mode", { mode, source_ids }),
};

// ── Skills ────────────────────────────────────────────────────────
export const skillsApi = {
  list:   ()          => api.get("/skills/"),
  add:    (skill_name) => api.post("/skills/", { skill_name }),
  remove: (id)        => api.delete(`/skills/${id}`),
};

// ── Watchlist ─────────────────────────────────────────────────────
export const watchlistApi = {
  list:   ()               => api.get("/watchlist/"),
  add:    (company_name)   => api.post("/watchlist/", { company_name }),
  remove: (id)             => api.delete(`/watchlist/${id}`),
};

export default api;
