/**
 * App.jsx — updated Day 5.
 * Added: Jobs, Skills (was Profile), Watchlist pages + nav items.
 */

import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import Sources   from "./pages/Sources";
import Jobs      from "./pages/Jobs";
import Skills    from "./pages/Skills";
import Watchlist from "./pages/Watchlist";

// Placeholder for Day 6
const Dashboard    = () => (
  <div className="p-8 text-center">
    <p className="text-4xl mb-4">📊</p>
    <p className="text-gray-400 text-lg">Dashboard — Coming in Day 6</p>
    <p className="text-gray-600 text-sm mt-1">Daily digest, application tracker</p>
  </div>
);
const Applications = () => (
  <div className="p-8 text-center">
    <p className="text-4xl mb-4">📋</p>
    <p className="text-gray-400 text-lg">Applications — Coming in Day 6</p>
  </div>
);

const NAV = [
  { to: "/",             label: "Dashboard",    end: true  },
  { to: "/jobs",         label: "Jobs"                     },
  { to: "/skills",       label: "Skills"                   },
  { to: "/watchlist",    label: "Watchlist"                },
  { to: "/sources",      label: "Sources"                  },
  { to: "/applications", label: "Applications"             },
];

function Navbar() {
  return (
    <nav className="border-b border-gray-800 bg-gray-950 sticky top-0 z-10">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <span className="font-bold text-white tracking-tight">
          JobRadar <span className="text-blue-500">AI</span>
        </span>
        <div className="flex items-center gap-1 overflow-x-auto">
          {NAV.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) =>
                `text-sm px-3 py-1.5 rounded-lg transition-colors whitespace-nowrap ${
                  isActive
                    ? "bg-blue-600/20 text-blue-400"
                    : "text-gray-400 hover:text-white hover:bg-gray-800"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950">
        <Navbar />
        <Routes>
          <Route path="/"             element={<Dashboard />}    />
          <Route path="/jobs"         element={<Jobs />}         />
          <Route path="/skills"       element={<Skills />}       />
          <Route path="/watchlist"    element={<Watchlist />}    />
          <Route path="/sources"      element={<Sources />}      />
          <Route path="/applications" element={<Applications />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
