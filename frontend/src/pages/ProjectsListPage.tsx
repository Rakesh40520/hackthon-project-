import { Link } from "react-router-dom";
import { useState } from "react";
import { Plus, Search, FolderKanban, Calendar, DollarSign } from "lucide-react";
import { useProjects } from "@/hooks/useProjects";
import { Card } from "@/components/Card";
import { StatusBadge } from "@/components/StatusBadge";
import { EmptyState } from "@/components/EmptyState";
import { format } from "date-fns";
import { useCreateProjectModal } from "./useCreateProjectModal";

export default function ProjectsListPage() {
  const { data: projects, isLoading } = useProjects();
  const [q, setQ] = useState("");
  const { showNew, setShowNew, form, setForm, create, submit } = useCreateProjectModal();
  const filtered = (projects || []).filter((p) => !q || p.name.toLowerCase().includes(q.toLowerCase()));

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Projects</h1>
          <p className="text-slate-500 text-sm">All procurement projects</p>
        </div>
        <button className="btn-primary" onClick={() => setShowNew(true)}>
          <Plus className="w-4 h-4" /> New Project
        </button>
      </div>

      <div className="relative max-w-md">
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input className="input pl-9" placeholder="Search projects..." value={q} onChange={(e) => setQ(e.target.value)} />
      </div>

      {isLoading ? (
        <div className="text-slate-500 text-sm">Loading…</div>
      ) : !filtered.length ? (
        <Card>
          <EmptyState
            title="No projects yet"
            description="Create your first procurement project to start collecting proposals."
            icon={<FolderKanban className="w-6 h-6" />}
          />
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((p) => (
            <Link key={p.id} to={`/projects/${p.id}`} className="block">
              <Card className="hover:shadow-elev transition cursor-pointer h-full">
                <div className="flex items-start justify-between">
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-blue-700 text-white flex items-center justify-center">
                    <FolderKanban className="w-5 h-5" />
                  </div>
                  <StatusBadge status={p.status} />
                </div>
                <h3 className="mt-3 font-semibold text-slate-900 line-clamp-1">{p.name}</h3>
                {p.description ? <p className="mt-1 text-xs text-slate-500 line-clamp-2">{p.description}</p> : null}
                <div className="mt-4 flex items-center gap-4 text-xs text-slate-500">
                  {p.budget ? <span className="flex items-center gap-1"><DollarSign className="w-3 h-3" /> {p.currency} {p.budget.toLocaleString()}</span> : null}
                  {p.deadline ? <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {format(new Date(p.deadline), "MMM d, yyyy")}</span> : null}
                </div>
                <div className="mt-4 grid grid-cols-3 text-center text-xs">
                  <div><div className="text-lg font-semibold text-slate-900">{p.vendor_count || 0}</div><div className="text-slate-500">Vendors</div></div>
                  <div><div className="text-lg font-semibold text-slate-900">{p.proposal_count || 0}</div><div className="text-slate-500">Proposals</div></div>
                  <div><div className="text-lg font-semibold text-slate-900">{p.requirement_count || 0}</div><div className="text-slate-500">Reqs</div></div>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}

      {showNew && (
        <div className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4" onClick={() => setShowNew(false)}>
          <Card className="w-full max-w-md" >
            <div onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">New Project</h3>
            <div className="space-y-3">
              <div><label className="label">Name</label><input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
              <div><label className="label">Category</label><input className="input" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} /></div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="label">Budget</label><input className="input" type="number" value={form.budget} onChange={(e) => setForm({ ...form, budget: Number(e.target.value) })} /></div>
                <div><label className="label">Currency</label><input className="input" value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} /></div>
              </div>
              <div><label className="label">Description</label><textarea className="input" rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
            </div>
            <div className="flex justify-end gap-2 mt-4">
              <button className="btn-secondary" onClick={() => setShowNew(false)}>Cancel</button>
              <button className="btn-primary" onClick={submit} disabled={!form.name || create.isPending}>{create.isPending ? "Creating…" : "Create"}</button>
            </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
