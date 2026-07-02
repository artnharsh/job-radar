/**
 * Jobs page — Day 5.
 * Two tabs: All Jobs | High Match (ranked by priority score)
 */

import { useState, useEffect, useCallback } from "react";
import { jobsApi } from "../services/api";

// ── Helpers ──────────────────────────────────────────────────────
const FRESHNESS_COLOR = (score) => {
  if (score >= 0.9) return "text-emerald-400 bg-emerald-400/10";
  if (score >= 0.75) return "text-green-400 bg-green-400/10";
  if (score >= 0.5) return "text-yellow-400 bg-yellow-400/10";
  return "text-gray-400 bg-gray-400/10";
};

const FRESHNESS_LABEL = (score) => {
  if (score >= 0.9) return "< 6h";
  if (score >= 0.75) return "Today";
  if (score >= 0.5) return "1-3d";
  return "Old";
};

const MATCH_COLOR = (score) => {
  if (score >= 0.7) return "text-blue-400 bg-blue-400/10 border-blue-400/30";
  if (score >= 0.4) return "text-indigo-400 bg-indigo-400/10 border-indigo-400/30";
  return "text-gray-500 bg-gray-500/10 border-gray-500/30";
};

const TRUST_COLOR = (score) => {
  if (score >= 0.8) return "text-emerald-400";
  if (score >= 0.6) return "text-yellow-400";
  return "text-orange-400";
};

// ── Job Card ─────────────────────────────────────────────────────
function JobCard({ job, showScore = false, onView }) {
  const [expanded, setExpanded] = useState(false);

  const handleExpand = () => {
    if (!expanded && onView) onView(job.id);
    setExpanded(!expanded);
  };

  return (
    <div
      className={`group relative bg-gray-900 border rounded-xl transition-all duration-200 overflow-hidden
        ${expanded ? "border-blue-500/50 shadow-lg shadow-blue-500/10" : "border-gray-800 hover:border-gray-700"}`}
    >
      {/* Viewed indicator */}
      {job.is_viewed && (
        <div className="absolute top-3 right-3 w-2 h-2 rounded-full bg-gray-600" title="Viewed" />
      )}

      <div className="p-5 cursor-pointer" onClick={handleExpand}>
        {/* Top row: title + badges */}
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-white text-base leading-tight truncate group-hover:text-blue-300 transition-colors">
              {job.title}
            </h3>
            <p className="text-gray-400 text-sm mt-0.5">
              {job.company}
              {job.location && <span className="text-gray-600 mx-1">·</span>}
              {job.location && <span className="text-gray-500">{job.location}</span>}
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {/* Freshness badge */}
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${FRESHNESS_COLOR(job.freshness_score)}`}>
              {FRESHNESS_LABEL(job.freshness_score)}
            </span>

            {/* Trust score */}
            <span className={`text-xs font-medium ${TRUST_COLOR(job.trust_score)}`} title={`Trust: ${(job.trust_score * 100).toFixed(0)}%`}>
              T{(job.trust_score * 10).toFixed(0)}
            </span>

            {/* Expand chevron */}
            <span className={`text-gray-500 transition-transform duration-200 ${expanded ? "rotate-180" : ""}`}>
              ▾
            </span>
          </div>
        </div>

        {/* Score row — only in High Match tab */}
        {showScore && (
          <div className="flex items-center gap-2 mt-3 flex-wrap">
            {/* Priority score bar */}
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <span className="text-xs text-gray-500 shrink-0">Priority</span>
              <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-600 to-purple-500 rounded-full transition-all duration-500"
                  style={{ width: `${(job.priority_score * 100).toFixed(0)}%` }}
                />
              </div>
              <span className="text-xs font-mono text-blue-400 shrink-0">
                {(job.priority_score * 100).toFixed(0)}%
              </span>
            </div>

            {/* Match badge */}
            <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${MATCH_COLOR(job.match_score)}`}>
              {(job.match_score * 100).toFixed(0)}% match
            </span>
          </div>
        )}

        {/* Tags row */}
        <div className="flex items-center gap-2 mt-2 flex-wrap">
          {job.is_remote && (
            <span className="text-xs px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
              Remote
            </span>
          )}
          {job.job_type && (
            <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-400">
              {job.job_type.replace("_", " ")}
            </span>
          )}
          {job.experience_level && (
            <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-400 capitalize">
              {job.experience_level}
            </span>
          )}
        </div>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="px-5 pb-5 border-t border-gray-800 pt-4 space-y-4 animate-in slide-in-from-top-2 duration-200">
          {/* Skill gap */}
          {showScore && job.skill_gap && job.skill_gap.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-2">Missing skills</p>
              <div className="flex flex-wrap gap-1.5">
                {job.skill_gap.map((skill) => (
                  <span
                    key={skill}
                    className="text-xs px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Description preview */}
          {job.description && (
            <div>
              <p className="text-xs text-gray-500 mb-1">Description</p>
              <p className="text-sm text-gray-400 leading-relaxed line-clamp-4">
                {job.description}
              </p>
            </div>
          )}

          {/* Source + apply */}
          <div className="flex items-center justify-between pt-1">
            <span className="text-xs text-gray-600">
              via {job.source_name} · {job.source_type}
            </span>
            <a
              href={job.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              Apply →
            </a>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Filter Bar ────────────────────────────────────────────────────
function FilterBar({ filters, onChange }) {
  return (
    <div className="flex items-center gap-3 flex-wrap">
      <input
        type="text"
        placeholder="Search title or company..."
        value={filters.search}
        onChange={(e) => onChange({ ...filters, search: e.target.value })}
        className="flex-1 min-w-[180px] bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
      />
      <select
        value={filters.is_remote}
        onChange={(e) => onChange({ ...filters, is_remote: e.target.value })}
        className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-blue-500"
      >
        <option value="">All Locations</option>
        <option value="true">Remote Only</option>
        <option value="false">On-site Only</option>
      </select>
      <select
        value={filters.experience_level}
        onChange={(e) => onChange({ ...filters, experience_level: e.target.value })}
        className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-blue-500"
      >
        <option value="">All Levels</option>
        <option value="entry">Entry</option>
        <option value="mid">Mid</option>
        <option value="senior">Senior</option>
        <option value="lead">Lead</option>
      </select>
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={filters.unseen_only}
          onChange={(e) => onChange({ ...filters, unseen_only: e.target.checked })}
          className="w-4 h-4 rounded border-gray-700 bg-gray-900 accent-blue-500"
        />
        <span className="text-sm text-gray-400">Unseen only</span>
      </label>
    </div>
  );
}

// ── Stats Bar ─────────────────────────────────────────────────────
function StatsBar({ stats }) {
  if (!stats) return null;
  return (
    <div className="flex items-center gap-4 text-xs text-gray-500 flex-wrap">
      <span><span className="text-white font-medium">{stats.total_jobs?.toLocaleString()}</span> total jobs</span>
      <span>·</span>
      <span><span className="text-emerald-400 font-medium">{stats.new_last_24h}</span> new today</span>
      <span>·</span>
      <span><span className="text-blue-400 font-medium">{stats.unseen}</span> unseen</span>
    </div>
  );
}

// ── Main Jobs Page ────────────────────────────────────────────────
export default function Jobs() {
  const [activeTab, setActiveTab] = useState("all");
  const [allJobs, setAllJobs] = useState([]);
  const [highMatchJobs, setHighMatchJobs] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingMatch, setLoadingMatch] = useState(false);
  const [error, setError] = useState(null);
  const [userSkillCount, setUserSkillCount] = useState(0);
  const [filters, setFilters] = useState({
    search: "",
    is_remote: "",
    experience_level: "",
    unseen_only: false,
  });

  // Load stats once
  useEffect(() => {
    jobsApi.stats().then((r) => setStats(r.data)).catch(() => {});
  }, []);

  // Load all jobs when filters change
  useEffect(() => {
    if (activeTab !== "all") return;
    setLoading(true);
    setError(null);
    const params = {};
    if (filters.search)          params.search = filters.search;
    if (filters.is_remote)       params.is_remote = filters.is_remote === "true";
    if (filters.experience_level) params.experience_level = filters.experience_level;
    if (filters.unseen_only)     params.unseen_only = true;

    const timer = setTimeout(() => {
      jobsApi.list({ ...params, limit: 50 })
        .then((r) => {
          setAllJobs(r.data.jobs || []);
          setLoading(false);
        })
        .catch((e) => {
          setError(e.message);
          setLoading(false);
        });
    }, 300);
    return () => clearTimeout(timer);
  }, [filters, activeTab]);

  // Load high-match jobs when tab switches
  useEffect(() => {
    if (activeTab !== "match") return;
    setLoadingMatch(true);
    jobsApi.highMatch({ limit: 50 })
      .then((r) => {
        setHighMatchJobs(r.data.jobs || []);
        setUserSkillCount(r.data.user_skill_count || 0);
        setLoadingMatch(false);
      })
      .catch(() => setLoadingMatch(false));
  }, [activeTab]);

  const handleView = useCallback((jobId) => {
    jobsApi.markViewed(jobId).catch(() => {});
  }, []);

  const jobs = activeTab === "all" ? allJobs : highMatchJobs;
  const isLoading = activeTab === "all" ? loading : loadingMatch;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Job Feed</h1>
          <StatsBar stats={stats} />
        </div>

        {/* Tab switcher */}
        <div className="flex items-center bg-gray-900 border border-gray-800 rounded-xl p-1 gap-1">
          <button
            onClick={() => setActiveTab("all")}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === "all"
                ? "bg-blue-600 text-white shadow"
                : "text-gray-400 hover:text-white"
            }`}
          >
            All Jobs
          </button>
          <button
            onClick={() => setActiveTab("match")}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center gap-1.5 ${
              activeTab === "match"
                ? "bg-blue-600 text-white shadow"
                : "text-gray-400 hover:text-white"
            }`}
          >
            ⚡ High Match
          </button>
        </div>
      </div>

      {/* High Match info banner */}
      {activeTab === "match" && (
        <div className="mb-4 p-3 rounded-xl bg-blue-600/10 border border-blue-500/20 text-sm text-blue-300 flex items-center gap-2">
          <span className="text-base">🎯</span>
          {userSkillCount === 0
            ? "Add skills in the Skills page to unlock personalised rankings."
            : `Ranked by: Match (50%) + Trust (30%) + Freshness (20%) · Based on ${userSkillCount} skill${userSkillCount !== 1 ? "s" : ""}`
          }
        </div>
      )}

      {/* Filters — only for All Jobs tab */}
      {activeTab === "all" && (
        <div className="mb-5">
          <FilterBar filters={filters} onChange={setFilters} />
        </div>
      )}

      {/* Content */}
      {isLoading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-900 border border-gray-800 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <div className="text-center py-16 text-red-400">
          <p className="text-lg mb-2">Failed to load jobs</p>
          <p className="text-sm text-gray-500">{error}</p>
        </div>
      ) : jobs.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-4xl mb-4">
            {activeTab === "match" ? "🎯" : "🔍"}
          </p>
          <p className="text-gray-400 text-lg mb-2">
            {activeTab === "match" ? "No matching jobs found" : "No jobs found"}
          </p>
          <p className="text-gray-600 text-sm">
            {activeTab === "match"
              ? "Add skills in the Skills page to see personalised matches."
              : "Try adjusting your filters or wait for the next collection run."}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              showScore={activeTab === "match"}
              onView={handleView}
            />
          ))}

          <p className="text-center text-xs text-gray-600 pt-2">
            Showing {jobs.length} job{jobs.length !== 1 ? "s" : ""} · updated every 15 min
          </p>
        </div>
      )}
    </div>
  );
}
