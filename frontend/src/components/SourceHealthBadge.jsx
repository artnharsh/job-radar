/**
 * SourceHealthBadge
 * Displays a coloured pill showing source health status.
 * Used inside SourceCard and the health dashboard.
 */

const STATUS_STYLES = {
  healthy:  "bg-green-500/15 text-green-400 border border-green-500/30",
  degraded: "bg-yellow-500/15 text-yellow-400 border border-yellow-500/30",
  failed:   "bg-red-500/15 text-red-400 border border-red-500/30",
  unknown:  "bg-gray-500/15 text-gray-400 border border-gray-500/30",
};

const STATUS_DOTS = {
  healthy:  "bg-green-400",
  degraded: "bg-yellow-400",
  failed:   "bg-red-400",
  unknown:  "bg-gray-500",
};

export default function SourceHealthBadge({ status = "unknown", showLabel = true }) {
  const style = STATUS_STYLES[status] ?? STATUS_STYLES.unknown;
  const dot   = STATUS_DOTS[status]   ?? STATUS_DOTS.unknown;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${style}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dot}`} />
      {showLabel && status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}