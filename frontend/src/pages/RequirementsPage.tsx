import { Link, useParams } from "react-router-dom";
import { useState } from "react";
import { Card } from "@/components/Card";
import { StatusBadge } from "@/components/StatusBadge";
import { EmptyState } from "@/components/EmptyState";
import { useProjects } from "@/hooks/useProjects";
import { useRequirements } from "@/hooks/useProposals";
import { ListChecks } from "lucide-react";

export default function RequirementsPage() {
  const { data: projects } = useProjects();
  const [projectId, setProjectId] = useState<string>("");
  const active = projectId || projects?.[0]?.id || "";
  const { data: requirements } = useRequirements(active);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Requirements</h1>
        <p className="text-slate-500 text-sm">Define what you need from vendors</p>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-sm text-slate-500">Project:</span>
        <select className="input max-w-sm" value={active} onChange={(e) => setProjectId(e.target.value)}>
          <option value="">Select…</option>
          {(projects || []).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </div>
      {!active ? (
        <Card><EmptyState title="Select a project" icon={<ListChecks className="w-6 h-6" />} /></Card>
      ) : !requirements?.length ? (
        <Card><EmptyState title="No requirements" description="Add requirements in the project page." /></Card>
      ) : (
        <Card padded={false}>
          <table className="w-full text-sm">
            <thead className="text-xs text-slate-500 border-b border-slate-200">
              <tr>
                <th className="text-left p-3">Name</th>
                <th className="text-left p-3">Category</th>
                <th className="text-left p-3">Priority</th>
                <th className="text-left p-3">Weight</th>
                <th className="text-left p-3">Mandatory</th>
              </tr>
            </thead>
            <tbody>
              {requirements.map((r) => (
                <tr key={r.id} className="border-b border-slate-100">
                  <td className="p-3"><div className="font-medium">{r.name}</div>{r.description ? <div className="text-xs text-slate-500">{r.description}</div> : null}</td>
                  <td className="p-3 text-slate-600">{r.category}</td>
                  <td className="p-3"><StatusBadge status={r.priority} /></td>
                  <td className="p-3">{r.weight}</td>
                  <td className="p-3">{r.mandatory ? <span className="badge badge-red">Yes</span> : <span className="badge badge-gray">No</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
      <div className="text-sm text-slate-500">
        <Link to={`/projects/${active}`} className="text-accent-600 font-medium">Manage in project →</Link>
      </div>
    </div>
  );
}
