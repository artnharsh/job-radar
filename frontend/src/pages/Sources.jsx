/**
 * Sources page — Day 3
 *
 * Sections:
 *  1. Mode selector (All / Trusted / India / Remote / Custom)
 *  2. Source health summary bar
 *  3. Source list grouped by tier with individual toggles
 */

import { useEffect, useState, useCallback } from "react";
import { sourcesApi } from "../services/api";
import SourceCard from "../components/SourceCard";
import SourceHealthBadge from "../components/SourceHealthBadge";

const MODES = [
  {
    id: "all",
    label: "All Sources",
    description: "Enable every source",
    icon: "⊕",
  },
  {
    id: "trusted",
    label: "Trusted Only",
    description: "Tier 1 public APIs — zero legal risk",
    icon: "✓",
  },
  {
    id: "india",
    label: "India Sources",
    description: "Internshala, Foundit, Shine, TimesJobs + Adzuna India",
    icon: "🇮🇳",
  },
  {
    id: "remote",
    label: "Remote Only",
    description: "Remotive, RemoteOK, WeWorkRemotely, Arbeitnow, Jobicy",
    icon: "🌐",
  },
];

const TIER_NAMES = {
  1: "Tier 1 — Public APIs",
  2: "Tier 2 — Startup Portals",
  3: "Tier 3 — Remote Boards",
  4: "Tier 4 — India",
  5: "Tier 5 — Aggregators",
};

export default function Sources() {
  const [sources, setSources]         = useState([]);
  const [loading, setLoading]         = useState(true);
  const [togglingId, setTogglingId]   = useState(null);
  const [activeMode, setActiveMode]   = useState(null);
  const [modeLoading, setModeLoading] = useState(false);
  const [error, setError]             = useState(null);
  const [lastRefresh, setLastRefresh] = useState(Date.now());

  // ── Fetch all sources ────────────────────────────────────────
  const fetchSources = useCallback(async () => {
    try {
      const res = await sourcesApi.list();
      if (Array.isArray(res.data)) {
        setSources(res.data);
        setError(null);
      } else {
        setSources([]);
        setError("Unexpected sources response from the backend.");
      }
    } catch (err) {
      setError("Failed to load sources. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSources();
  }, [fetchSources, lastRefresh]);

  // ── Toggle single source ──────────────────────────────────────
  const handleToggle = async (sourceId, isEnabled) => {
    setTogglingId(sourceId);
    try {
      await sourcesApi.select(sourceId, isEnabled);
      setSources(prev =>
        prev.map(s => s.id === sourceId ? { ...s, is_enabled: isEnabled } : s)
      );
    } catch {
      setError("Failed to update source. Try again.");
    } finally {
      setTogglingId(null);
    }
  };

  // ── Apply preset mode ─────────────────────────────────────────
  const handleMode = async (modeId) => {
    setModeLoading(true);
    setActiveMode(modeId);
    try {
      await sourcesApi.setMode(modeId);
      setLastRefresh(Date.now()); // re-fetch updated states
    } catch {
      setError("Failed to apply mode. Try again.");
      setActiveMode(null);
    } finally {
      setModeLoading(false);
    }
  };

  // ── Derived stats ─────────────────────────────────────────────
  const healthCounts = sources.reduce((acc, s) => {
    const status = s.health?.status ?? "unknown";
    acc[status] = (acc[status] ?? 0) + 1;
    return acc;
  }, {});

  const enabledCount  = sources.filter(s => s.is_enabled).length;
  const totalCount    = sources.length;

  // Group by tier
  const byTier = sources.reduce((acc, s) => {
    const tier = s.tier;
    if (!acc[tier]) acc[tier] = [];
    acc[tier].push(s);
    return acc;
  }, {});

  // ── Render ────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400 animate-pulse">Loading sources...</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Source Management</h1>
        <p className="text-gray-400 mt-1 text-sm">
          {enabledCount} of {totalCount} sources enabled
        </p>
      </div>

      {/* Error banner */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Health summary bar */}
      <div className="card">
        <h2 className="text-sm font-semibold text-gray-300 mb-3">
          Source Health Overview
        </h2>
        <div className="flex flex-wrap gap-3">
          {[
            { status: "healthy",  label: "Healthy"  },
            { status: "degraded", label: "Degraded" },
            { status: "failed",   label: "Failed"   },
            { status: "unknown",  label: "Unknown"  },
          ].map(({ status, label }) => (
            <div key={status} className="flex items-center gap-2">
              <SourceHealthBadge status={status} showLabel={false} />
              <span className="text-sm text-gray-400">
                {healthCounts[status] ?? 0} {label}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Mode selector */}
      <div>
        <h2 className="text-sm font-semibold text-gray-300 mb-3 uppercase tracking-wide">
          Quick Modes
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {MODES.map(mode => (
            <button
              key={mode.id}
              onClick={() => handleMode(mode.id)}
              disabled={modeLoading}
              className={`card text-left hover:border-blue-500/50 transition-colors
                         ${activeMode === mode.id
                           ? "border-blue-500 bg-blue-500/10"
                           : "hover:bg-gray-800/50"
                         }
                         ${modeLoading ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
            >
              <div className="text-xl mb-2">{mode.icon}</div>
              <div className="text-sm font-semibold text-white">{mode.label}</div>
              <div className="text-xs text-gray-500 mt-1">{mode.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Source list grouped by tier */}
      {Object.entries(byTier)
        .sort(([a], [b]) => Number(a) - Number(b))
        .map(([tier, tierSources]) => (
          <div key={tier}>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
                {TIER_NAMES[tier] ?? `Tier ${tier}`}
              </h2>
              <span className="text-xs text-gray-500">
                {tierSources.filter(s => s.is_enabled).length} / {tierSources.length} enabled
              </span>
            </div>

            <div className="space-y-2">
              {tierSources.map(source => (
                <SourceCard
                  key={source.id}
                  source={source}
                  onToggle={handleToggle}
                  loading={togglingId === source.id}
                />
              ))}
            </div>
          </div>
        ))
      }
    </div>
  );
}