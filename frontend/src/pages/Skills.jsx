/**
 * Skills page — Day 5.
 * Add/remove skills used by the match engine.
 */

import { useState, useEffect, useRef } from "react";
import { skillsApi, jobsApi } from "../services/api";

// ── Skill Chip ────────────────────────────────────────────────────
const CHIP_COLORS = [
  "bg-blue-500/15 text-blue-300 border-blue-500/30",
  "bg-purple-500/15 text-purple-300 border-purple-500/30",
  "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  "bg-cyan-500/15 text-cyan-300 border-cyan-500/30",
  "bg-indigo-500/15 text-indigo-300 border-indigo-500/30",
  "bg-teal-500/15 text-teal-300 border-teal-500/30",
  "bg-violet-500/15 text-violet-300 border-violet-500/30",
];

function colorForSkill(name) {
  let h = 0;
  for (const c of name) h = (h * 31 + c.charCodeAt(0)) & 0xffffffff;
  return CHIP_COLORS[Math.abs(h) % CHIP_COLORS.length];
}

function SkillChip({ skill, onRemove, removing }) {
  return (
    <div
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-sm font-medium
        transition-all duration-200 ${colorForSkill(skill.skill_name)}
        ${removing ? "opacity-50 scale-95" : "hover:scale-105"}`}
    >
      {skill.skill_name}
      <button
        onClick={() => onRemove(skill.id)}
        disabled={removing}
        className="ml-0.5 opacity-50 hover:opacity-100 transition-opacity text-xs leading-none"
        title="Remove skill"
      >
        ✕
      </button>
    </div>
  );
}

// ── Quick-add suggestions ─────────────────────────────────────────
const POPULAR_SKILLS = [
  "Python", "JavaScript", "TypeScript", "React", "Node.js",
  "FastAPI", "Django", "PostgreSQL", "Docker", "Kubernetes",
  "AWS", "GCP", "Go", "Rust", "Java", "Spring",
  "TensorFlow", "PyTorch", "Spark", "Kafka",
];

// ── Stats Card ────────────────────────────────────────────────────
function StatCard({ label, value, sub, color = "text-white" }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-gray-600 mt-1">{sub}</p>}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────
export default function Skills() {
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [input, setInput] = useState("");
  const [adding, setAdding] = useState(false);
  const [removingId, setRemovingId] = useState(null);
  const [jobStats, setJobStats] = useState(null);
  const [error, setError] = useState("");
  const inputRef = useRef(null);

  const loadSkills = async () => {
    try {
      const r = await skillsApi.list();
      setSkills(r.data);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSkills();
    jobsApi.stats().then((r) => setJobStats(r.data)).catch(() => {});
  }, []);

  const handleAdd = async (nameOverride) => {
    const name = (nameOverride || input).trim();
    if (!name) return;
    if (skills.some((s) => s.skill_name.toLowerCase() === name.toLowerCase())) {
      setError("Skill already added");
      return;
    }
    setError("");
    setAdding(true);
    try {
      const r = await skillsApi.add(name);
      setSkills((prev) => [...prev, r.data].sort((a, b) => a.skill_name.localeCompare(b.skill_name)));
      setInput("");
      inputRef.current?.focus();
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to add skill");
    } finally {
      setAdding(false);
    }
  };

  const handleRemove = async (id) => {
    setRemovingId(id);
    try {
      await skillsApi.remove(id);
      setSkills((prev) => prev.filter((s) => s.id !== id));
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

  const suggestions = POPULAR_SKILLS.filter(
    (s) =>
      !skills.some((sk) => sk.skill_name.toLowerCase() === s.toLowerCase()) &&
      (input === "" || s.toLowerCase().includes(input.toLowerCase()))
  ).slice(0, 8);

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-2xl font-bold text-white">My Skills</h1>
          <span className="px-2.5 py-0.5 rounded-full bg-blue-600/20 text-blue-400 text-sm font-medium">
            {skills.length}
          </span>
        </div>
        <p className="text-gray-500 text-sm">
          Skills are used to compute your match score on every job. Add more to improve ranking accuracy.
        </p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-3 mb-8">
        <StatCard label="Skills added" value={skills.length} sub="Your profile" color="text-blue-400" />
        <StatCard label="Total jobs" value={jobStats?.total_jobs?.toLocaleString() ?? "—"} sub="In database" />
        <StatCard label="Unseen jobs" value={jobStats?.unseen ?? "—"} sub="Not viewed yet" color="text-emerald-400" />
      </div>

      {/* Add skill input */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 mb-6">
        <p className="text-sm font-medium text-gray-300 mb-3">Add a skill</p>
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => { setInput(e.target.value); setError(""); }}
            onKeyDown={handleKeyDown}
            placeholder="e.g. Python, React, Docker..."
            className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white
              placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
          />
          <button
            onClick={() => handleAdd()}
            disabled={adding || !input.trim()}
            className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-40
              disabled:cursor-not-allowed text-white text-sm font-medium transition-colors"
          >
            {adding ? "Adding…" : "Add"}
          </button>
        </div>
        {error && <p className="mt-2 text-xs text-red-400">{error}</p>}

        {/* Quick-add suggestions */}
        {suggestions.length > 0 && (
          <div className="mt-4">
            <p className="text-xs text-gray-600 mb-2">
              {input ? "Matching suggestions" : "Popular skills"}
            </p>
            <div className="flex flex-wrap gap-1.5">
              {suggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => handleAdd(s)}
                  className="text-xs px-2.5 py-1 rounded-full bg-gray-800 text-gray-400
                    hover:bg-gray-700 hover:text-white border border-gray-700 hover:border-gray-600 transition-all"
                >
                  + {s}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Skills list */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm font-medium text-gray-300">Your skills</p>
          {skills.length > 0 && (
            <p className="text-xs text-gray-600">Click ✕ to remove</p>
          )}
        </div>

        {loading ? (
          <div className="flex flex-wrap gap-2">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-8 w-20 bg-gray-800 rounded-full animate-pulse" />
            ))}
          </div>
        ) : skills.length === 0 ? (
          <div className="text-center py-10">
            <p className="text-4xl mb-3">🎯</p>
            <p className="text-gray-500 text-sm">No skills added yet.</p>
            <p className="text-gray-600 text-xs mt-1">
              Add your first skill above to start getting personalised job matches.
            </p>
          </div>
        ) : (
          <div className="flex flex-wrap gap-2">
            {skills.map((skill) => (
              <SkillChip
                key={skill.id}
                skill={skill}
                onRemove={handleRemove}
                removing={removingId === skill.id}
              />
            ))}
          </div>
        )}
      </div>

      {/* How it works */}
      <div className="mt-6 p-4 rounded-xl bg-gray-900/50 border border-gray-800">
        <p className="text-xs text-gray-500 font-medium mb-2">How match scoring works</p>
        <div className="space-y-1 text-xs text-gray-600">
          <p>
            <span className="text-blue-400 font-medium">Match (50%)</span>
            {" "}— Skills you have ÷ Skills in job description
          </p>
          <p>
            <span className="text-yellow-400 font-medium">Trust (30%)</span>
            {" "}— Source reliability score (LinkedIn &gt; scrapers)
          </p>
          <p>
            <span className="text-emerald-400 font-medium">Freshness (20%)</span>
            {" "}— How recently the job was posted
          </p>
        </div>
      </div>
    </div>
  );
}
