/**
 * SourceCard
 * Shows a single source with its tier, health status,
 * and an enable/disable toggle.
 */

import SourceHealthBadge from "./SourceHealthBadge";

const TIER_LABELS = {
  1: { label: "Tier 1 · Public API",  color: "text-blue-400"  },
  2: { label: "Tier 2 · Startup",     color: "text-purple-400"},
  3: { label: "Tier 3 · Remote",      color: "text-cyan-400"  },
  4: { label: "Tier 4 · India",       color: "text-orange-400"},
  5: { label: "Tier 5 · Aggregator",  color: "text-gray-400"  },
};

export default function SourceCard({ source, onToggle, loading }) {
  const tierInfo = TIER_LABELS[source.tier] ?? { label: `Tier ${source.tier}`, color: "text-gray-400" };
  const healthStatus = source.health?.status ?? "unknown";
  const consecutiveFails = source.health?.consecutive_failures ?? 0;

  return (
    <div className={`card flex items-center justify-between gap-4 transition-opacity
                    ${loading ? "opacity-50 pointer-events-none" : ""}`}>

      {/* Left: Name + meta */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-semibold text-white truncate">{source.name}</span>
          <SourceHealthBadge status={healthStatus} />
        </div>

        <div className="flex items-center gap-3 mt-1 flex-wrap">
          <span className={`text-xs ${tierInfo.color}`}>{tierInfo.label}</span>
          <span className="text-xs text-gray-500">
            Trust {Math.round(source.trust_score * 100)}%
          </span>
          <span className="text-xs text-gray-500">
            Every {source.poll_interval}m
          </span>
          {consecutiveFails > 0 && (
            <span className="text-xs text-red-400">
              {consecutiveFails} consecutive fail{consecutiveFails > 1 ? "s" : ""}
            </span>
          )}
        </div>

        {/* Error message preview */}
        {healthStatus === "failed" && source.health?.error_message && (
          <p className="text-xs text-red-400/70 mt-1 truncate max-w-xs">
            {source.health.error_message}
          </p>
        )}
      </div>

      {/* Right: Toggle */}
      <button
        onClick={() => onToggle(source.id, !source.is_enabled)}
        className={`relative w-11 h-6 rounded-full transition-colors duration-200 flex-shrink-0
                   ${source.is_enabled ? "bg-blue-600" : "bg-gray-700"}`}
        aria-label={source.is_enabled ? "Disable source" : "Enable source"}
      >
        <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full
                         shadow transition-transform duration-200
                         ${source.is_enabled ? "translate-x-5" : "translate-x-0"}`}
        />
      </button>
    </div>
  );
}