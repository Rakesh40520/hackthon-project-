import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  FolderKanban,
  Building2,
  ListChecks,
  FileText,
  GitCompareArrows,
  Sparkles,
  BarChart3,
  ScrollText,
  Settings,
  LogOut,
  Bell,
  Search,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import clsx from "clsx";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/projects", label: "Projects", icon: FolderKanban },
  { to: "/vendors", label: "Vendors", icon: Building2 },
  { to: "/requirements", label: "Requirements", icon: ListChecks },
  { to: "/proposals", label: "Proposals", icon: FileText },
  { to: "/reports", label: "Reports", icon: ScrollText },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex bg-slate-50">
      <aside className="w-60 bg-white border-r border-slate-200 flex flex-col">
        <div className="h-16 flex items-center gap-2 px-5 border-b border-slate-200">
          <div className="w-8 h-8 rounded-lg bg-brand-800 flex items-center justify-center text-white font-bold">
            P
          </div>
          <div>
            <div className="font-semibold text-sm">Procurement</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-wider">Intelligence</div>
          </div>
        </div>
        <nav className="flex-1 p-3 space-y-0.5">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition",
                  isActive ? "bg-brand-800 text-white" : "text-slate-600 hover:bg-slate-100"
                )
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-slate-200">
          <Link
            to="/settings"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-600 hover:bg-slate-100"
          >
            <Settings className="w-4 h-4" /> Settings
          </Link>
          <button
            onClick={async () => {
              await logout();
              navigate("/login");
            }}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-600 hover:bg-slate-100"
          >
            <LogOut className="w-4 h-4" /> Logout
          </button>
        </div>
      </aside>
      <main className="flex-1 flex flex-col">
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6">
          <div className="flex items-center gap-3 text-sm text-slate-500">
            <Search className="w-4 h-4" />
            <input
              placeholder="Search projects, vendors, proposals..."
              className="bg-transparent focus:outline-none w-72"
            />
          </div>
          <div className="flex items-center gap-3">
            <button className="p-2 rounded-lg hover:bg-slate-100 relative">
              <Bell className="w-4 h-4 text-slate-500" />
              <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-red-500 rounded-full"></span>
            </button>
            <div className="flex items-center gap-2 pl-3 border-l border-slate-200">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent-400 to-accent-600 text-white text-xs font-semibold flex items-center justify-center">
                {user?.name?.split(" ").map((n) => n[0]).slice(0, 2).join("") || "U"}
              </div>
              <div className="text-sm">
                <div className="font-medium">{user?.name}</div>
                <div className="text-[11px] text-slate-500">{user?.role.replace("_", " ")}</div>
              </div>
            </div>
          </div>
        </header>
        <div className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
