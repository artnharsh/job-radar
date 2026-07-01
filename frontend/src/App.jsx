import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import Sources from "./pages/Sources";

// Placeholder pages for Days 4-6
const Dashboard    = () => <div className="p-8 text-gray-400">Dashboard — Day 6</div>;
const Jobs         = () => <div className="p-8 text-gray-400">Jobs — Day 4</div>;
const Applications = () => <div className="p-8 text-gray-400">Applications — Day 6</div>;
const Profile      = () => <div className="p-8 text-gray-400">Profile — Day 5</div>;

const NAV = [
  { to: "/",            label: "Dashboard"    },
  { to: "/jobs",        label: "Jobs"         },
  { to: "/sources",     label: "Sources"      },
  { to: "/applications",label: "Applications" },
  { to: "/profile",     label: "Profile"      },
];

function Navbar() {
  return (
    <nav className="border-b border-gray-800 bg-gray-950 sticky top-0 z-10">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <span className="font-bold text-white tracking-tight">
          JobRadar <span className="text-blue-500">AI</span>
        </span>
        <div className="flex items-center gap-1">
          {NAV.map(link => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === "/"}
              className={({ isActive }) =>
                `text-sm px-3 py-1.5 rounded-lg transition-colors ${
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
          <Route path="/sources"      element={<Sources />}      />
          <Route path="/applications" element={<Applications />} />
          <Route path="/profile"      element={<Profile />}      />
        </Routes>
      </div>
    </BrowserRouter>
  );
}