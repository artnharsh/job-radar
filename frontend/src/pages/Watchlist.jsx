/**
 * Watchlist page — Day 5.
 * Monitor target companies. Get immediate Telegram alerts when they post.
 */

import { useState, useEffect, useRef } from "react";
import { watchlistApi } from "../services/api";

// ── Company Card ──────────────────────────────────────────────────
function CompanyCard({ entry, onRemove, removing }) {
  const initials = entry.company_name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join("");

  const createdAt = new Date(entry.created_at);
  const addedAgo = () => {
    const diff = (Date.now() - createdAt.getTime()) / 1000;
    if (diff < 60) return "just now";
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  };

  return (
    <div
      className={`flex items-center gap-4 p-4 bg-gray-900 border border-gray-800 rounded-xl
        transition-all duration-200 hover:border-amber-500/30 group
        ${removing ? "opacity-50 scale-98" : ""}`}
    >
      {/* Avatar */}
      <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20
        flex items-center justify-center text-amber-400 text-sm font-bold shrink-0">
        {initials || "?"}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <p className="text-white font-medium truncate">{entry.company_name}</p>
        <p className="text-xs text-gray-600">Watching · Added {addedAgo()}</p>
      </div>

      {/* Alert badge */}
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs text-emerald-400">Active</span>
        </div>

        {/* Remove button */}
        <button
          onClick={() => onRemove(entry.id)}
          disabled={removing}
          className="p-2 rounded-lg text-gray-600 hover:text-red-400 hover:bg-red-400/10
            transition-all opacity-0 group-hover:opacity-100 disabled:opacity-30"
          title="Stop watching"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" />
            <path d="M10 11v6M14 11v6" />
          </svg>
        </button>
      </div>
    </div>
  );
}

// ── How It Works Card ─────────────────────────────────────────────
function HowItWorks() {
  const steps = [
    { icon: "➕", text: "Add a company to your watchlist" },
    { icon: "🔍", text: "JobRadar polls sources every 15 minutes" },
    { icon: "🚨", text: "New job detected from watched company" },
    { icon: "📱", text: "Instant Telegram alert with apply link" },
  ];

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
      <p className="text-sm font-medium text-gray-300 mb-4">How it works</p>
      <div className="space-y-3">
        {steps.map((s, i) => (
          <div key={i} className="flex items-center gap-3">
            <span className="text-base w-7 shrink-0 text-center">{s.icon}</span>
            <p className="text-sm text-gray-500">{s.text}</p>
          </div>
        ))}
      </div>
      <div className="mt-4 pt-4 border-t border-gray-800">
        <p className="text-xs text-gray-600">
          💡 Matching is case-insensitive. "Google" will also match "Google DeepMind", "Google LLC" etc.
        </p>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────
export default function Watchlist() {
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [input, setInput] = useState("");
  const [adding, setAdding] = useState(false);
  const [removingId, setRemovingId] = useState(null);
  const [error, setError] = useState("");
  const inputRef = useRef(null);

  const loadWatchlist = async () => {
    try {
      const r = await watchlistApi.list();
      setWatchlist(r.data);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWatchlist();
  }, []);

  const handleAdd = async () => {
    const name = input.trim();
    if (!name) return;
    if (watchlist.some((e) => e.company_name.toLowerCase() === name.toLowerCase())) {
      setError("Already watching this company");
      return;
    }
    setError("");
    setAdding(true);
    try {
      const r = await watchlistApi.add(name);
      setWatchlist((prev) =>
        [...prev, r.data].sort((a, b) => a.company_name.localeCompare(b.company_name))
      );
      setInput("");
      inputRef.current?.focus();
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to add company");
    } finally {
      setAdding(false);
    }
  };

  const handleRemove = async (id) => {
    setRemovingId(id);
    try {
      await watchlistApi.remove(id);
      setWatchlist((prev) => prev.filter((e) => e.id !== id));
    } catch {
      // silent
    } finally {
      setRemovingId(null);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleAdd();
    if (e.key === "Escape") setInput("");
  };

  // Example target companies for quick-add
  const suggestions = [
    "Google", "Microsoft", "OpenAI", "Anthropic", "Meta",
    "Apple", "Netflix", "Stripe", "Atlassian", "Figma",
    "Notion", "Vercel", "Cloudflare", "Hugging Face",
  ].filter((c) =>
    !watchlist.some((e) => e.company_name.toLowerCase() === c.toLowerCase()) &&
    (input === "" || c.toLowerCase().includes(input.toLowerCase()))
  ).slice(0, 8);

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-2xl font-bold text-white">Company Watchlist</h1>
          <span className="px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-400 text-sm font-medium">
            {watchlist.length}
          </span>
        </div>
        <p className="text-gray-500 text-sm">
          Get an instant Telegram alert the moment a watched company posts a new job.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        {/* Left: Add + List */}
        <div className="lg:col-span-3 space-y-5">
          {/* Add company input */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
            <p className="text-sm font-medium text-gray-300 mb-3">Watch a company</p>
            <div className="flex gap-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => { setInput(e.target.value); setError(""); }}
                onKeyDown={handleKeyDown}
                placeholder="e.g. Google, Atlassian, OpenAI…"
                className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white
                  placeholder-gray-500 focus:outline-none focus:border-amber-500 transition-colors"
              />
              <button
                onClick={handleAdd}
                disabled={adding || !input.trim()}
                className="px-5 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500
                  disabled:opacity-40 disabled:cursor-not-allowed
                  text-white text-sm font-medium transition-colors shrink-0"
              >
                {adding ? "Adding…" : "Watch"}
              </button>
            </div>
            {error && <p className="mt-2 text-xs text-red-400">{error}</p>}

            {/* Suggestions */}
            {suggestions.length > 0 && (
              <div className="mt-4">
                <p className="text-xs text-gray-600 mb-2">
                  {input ? "Suggestions" : "Popular companies"}
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {suggestions.map((c) => (
                    <button
                      key={c}
                      onClick={() => { setInput(c); inputRef.current?.focus(); }}
                      className="text-xs px-2.5 py-1 rounded-full bg-gray-800 text-gray-400
                        hover:bg-amber-500/10 hover:text-amber-400 hover:border-amber-500/30
                        border border-gray-700 transition-all"
                    >
                      {c}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Watched companies list */}
          <div>
            {loading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-[72px] bg-gray-900 border border-gray-800 rounded-xl animate-pulse" />
                ))}
              </div>
            ) : watchlist.length === 0 ? (
              <div className="text-center py-14 bg-gray-900 border border-gray-800 rounded-2xl">
                <p className="text-4xl mb-3">🏢</p>
                <p className="text-gray-400 text-sm">No companies on watch yet.</p>
                <p className="text-gray-600 text-xs mt-1">
                  Add a company above to start getting alerts.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {watchlist.map((entry) => (
                  <CompanyCard
                    key={entry.id}
                    entry={entry}
                    onRemove={handleRemove}
                    removing={removingId === entry.id}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right: How it works */}
        <div className="lg:col-span-2">
          <HowItWorks />

          {/* Telegram tip */}
          <div className="mt-4 p-4 rounded-xl border border-amber-500/20 bg-amber-500/5">
            <div className="flex items-start gap-2">
              <span className="text-lg shrink-0">📱</span>
              <div>
                <p className="text-xs font-medium text-amber-400 mb-1">Telegram Setup</p>
                <p className="text-xs text-gray-500">
                  Make sure <code className="text-amber-400 bg-amber-500/10 px-1 rounded">TELEGRAM_BOT_TOKEN</code>
                  {" "}and <code className="text-amber-400 bg-amber-500/10 px-1 rounded">TELEGRAM_CHAT_ID</code>
                  {" "}are set in your <code className="text-gray-400">.env</code> to receive alerts.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
