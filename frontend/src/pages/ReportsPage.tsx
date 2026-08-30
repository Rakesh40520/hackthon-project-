import { useState } from "react";
import { FileText, Download, FileSpreadsheet } from "lucide-react";
import { Card, CardHeader } from "@/components/Card";
import { useProjects } from "@/hooks/useProjects";
import api from "@/lib/api";
import toast from "react-hot-toast";

export default function ReportsPage() {
  const { data: projects } = useProjects();
  const [projectId, setProjectId] = useState("");
  const [busy, setBusy] = useState<"pdf" | "xlsx" | null>(null);

  const exportReport = async (fmt: "pdf" | "xlsx") => {
    if (!projectId) { toast.error("Select a project"); return; }
    setBusy(fmt);
    try {
      const r = await api.post(`/reports/${projectId}`, { format: fmt }, { responseType: "blob" });
      const url = URL.createObjectURL(r.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `procurement-report.${fmt}`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success(`${fmt.toUpperCase()} downloaded`);
    } catch { toast.error("Export failed"); }
    finally { setBusy(null); }
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Reports</h1>
        <p className="text-slate-500 text-sm">Export procurement decision packages</p>
      </div>

      <Card>
        <CardHeader title="Generate Report" subtitle="Executive-ready PDF or detailed Excel" />
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex-1 min-w-[200px]">
            <label className="label">Project</label>
            <select className="input" value={projectId} onChange={(e) => setProjectId(e.target.value)}>
              <option value="">Select…</option>
              {(projects || []).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
          <button className="btn-primary" onClick={() => exportReport("pdf")} disabled={busy === "pdf" || !projectId}>
            <FileText className="w-4 h-4" /> {busy === "pdf" ? "Generating…" : "PDF"}
          </button>
          <button className="btn-secondary" onClick={() => exportReport("xlsx")} disabled={busy === "xlsx" || !projectId}>
            <FileSpreadsheet className="w-4 h-4" /> {busy === "xlsx" ? "Generating…" : "Excel"}
          </button>
        </div>
      </Card>

      <Card>
        <CardHeader title="What's in the report?" />
        <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-slate-600 list-disc pl-5">
          <li>Executive Summary</li>
          <li>Project Overview</li>
          <li>Vendor Overview</li>
          <li>Pricing Comparison (Y1/Y3/Y5)</li>
          <li>Technical Comparison</li>
          <li>Requirement Compliance Matrix</li>
          <li>Risk Analysis (per category and severity)</li>
          <li>Missing Information</li>
          <li>Scoring Methodology &amp; Weights</li>
          <li>Vendor Ranking with Eligibility</li>
          <li>AI Recommendation</li>
          <li>Clarification Questions</li>
          <li>Final Decision Audit Trail</li>
        </ul>
      </Card>
    </div>
  );
}
