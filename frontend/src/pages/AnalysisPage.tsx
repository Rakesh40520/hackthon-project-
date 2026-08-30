import { useParams, Link } from "react-router-dom";
import { useState } from "react";
import { ArrowLeft, Sparkles, MessageCircle } from "lucide-react";
import { Card, CardHeader } from "@/components/Card";
import { useProject } from "@/hooks/useProjects";
import { useProposals } from "@/hooks/useProposals";
import { CopilotPanel } from "./CopilotPanel";

export default function AnalysisPage() {
  const { projectId } = useParams();
  const { data: project } = useProject(projectId);
  const { data: proposals } = useProposals(projectId);
  const [vendorId, setVendorId] = useState<string | undefined>(undefined);

  if (!project) return <div className="text-slate-500 text-sm">Loading…</div>;

  return (
    <div className="space-y-5">
      <div>
        <Link to={`/projects/${projectId}`} className="text-sm text-slate-500 hover:text-slate-700 flex items-center gap-1">
          <ArrowLeft className="w-3 h-3" /> Back to project
        </Link>
      </div>
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-accent-600" /> AI Analysis — {project.name}
        </h1>
        <p className="text-slate-500 text-sm">Ask anything about the proposals in this project.</p>
      </div>

      <Card>
        <CardHeader title="Scope" subtitle="Optional: focus on a single vendor" />
        <select className="input max-w-sm" value={vendorId || ""} onChange={(e) => setVendorId(e.target.value || undefined)}>
          <option value="">All vendors</option>
          {(proposals || []).map((p) => (
            <option key={p.id} value={p.vendor_id}>{p.vendor_name || p.vendor_company}</option>
          ))}
        </select>
      </Card>

      <CopilotPanel projectId={projectId!} vendorId={vendorId} />
    </div>
  );
}
