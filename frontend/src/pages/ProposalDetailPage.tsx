import { useParams, Link } from "react-router-dom";
import { ArrowLeft, FileText, RotateCw, Sparkles, AlertTriangle, MessageCircle, ListChecks, DollarSign } from "lucide-react";
import { useState } from "react";
import { useProposal, useReanalyze } from "@/hooks/useProposals";
import { Card } from "@/components/Card";
import { ScoreRing } from "@/components/ScoreRing";
import { StatusBadge } from "@/components/StatusBadge";
import { AnalysisProgress } from "@/components/AnalysisProgress";
import toast from "react-hot-toast";
import clsx from "clsx";
import { CopilotPanel } from "./CopilotPanel";
import { Overview, Requirements, Pricing, Risks, Missing } from "./ProposalDetailTabs2";
import api from "@/lib/api";

const TABS = [
  { id: "overview", label: "Overview", icon: FileText },
  { id: "requirements", label: "Requirements", icon: ListChecks },
  { id: "pricing", label: "Pricing", icon: DollarSign },
  { id: "risks", label: "Risks", icon: AlertTriangle },
  { id: "missing", label: "Missing Info", icon: MessageCircle },
  { id: "copilot", label: "AI Copilot", icon: Sparkles },
];

export default function ProposalDetailPage() {
  const { id } = useParams();
  const { data, isLoading } = useProposal(id);
  const reanalyze = useReanalyze();
  const [tab, setTab] = useState("overview");

  if (isLoading) return <div className="text-slate-500 text-sm">Loading…</div>;
  if (!data) return <div>Not found.</div>;

  const onReanalyze = async () => {
    try { await reanalyze.mutateAsync(data.id); toast.success("Re-analysis queued"); }
    catch { toast.error("Failed to queue re-analysis"); }
  };

  const onClarify = async () => {
    try {
      const r = await api.post(`/proposals/${data.id}/clarify`);
      toast.success(`${r.data.length} clarification questions generated`);
    } catch { toast.error("Failed to generate clarifications"); }
  };

  const exporting = async (fmt: "pdf" | "xlsx") => {
    try {
      const r = await api.post(`/reports/${data.project_id}`, { format: fmt }, { responseType: "blob" });
      const url = URL.createObjectURL(r.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `procurement-report.${fmt}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch { toast.error("Export failed"); }
  };

  return (
    <div className="space-y-5">
      <div>
        <Link to={`/projects/${data.project_id}`} className="text-sm text-slate-500 hover:text-slate-700 flex items-center gap-1">
          <ArrowLeft className="w-3 h-3" /> Back to project
        </Link>
      </div>

      <Card>
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <div className="text-xs text-slate-500">Vendor</div>
            <h1 className="text-2xl font-bold text-slate-900">{data.vendor_company || data.vendor_name}</h1>
            <div className="text-sm text-slate-500">{data.title}</div>
            <div className="mt-2 flex items-center gap-2">
              <StatusBadge status={data.status} />
              {data.current_job?.stage_message && <span className="text-xs text-slate-500">{data.current_job.stage_message}</span>}
            </div>
          </div>
          <div className="flex items-center gap-3">
            {data.score ? <ScoreRing value={data.score.total_score} size={84} label="Score" /> : <div className="text-sm text-slate-500">No score</div>}
            <div className="flex flex-col gap-2">
              <button className="btn-secondary" onClick={onReanalyze} disabled={reanalyze.isPending}>
                <RotateCw className="w-4 h-4" /> Re-analyze
              </button>
              <button className="btn-secondary" onClick={onClarify}>Generate Clarifications</button>
            </div>
          </div>
        </div>

        {(data.status === "PROCESSING" || data.status === "QUEUED" || data.status === "UPLOADED" || data.status === "ANALYZING" || data.status === "EXTRACTING" || data.status === "SCORING") && (
          <div className="mt-5"><AnalysisProgress job={data.current_job} /></div>
        )}

        <div className="mt-5 border-b border-slate-200 flex gap-1 overflow-x-auto">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={clsx(
                "px-3 py-2 text-sm font-medium border-b-2 flex items-center gap-2 transition whitespace-nowrap",
                tab === t.id ? "border-brand-800 text-brand-800" : "border-transparent text-slate-500 hover:text-slate-700"
              )}
            >
              <t.icon className="w-4 h-4" /> {t.label}
            </button>
          ))}
        </div>

        <div className="mt-5">
          {tab === "overview" && <Overview data={data} onExport={exporting} />}
          {tab === "requirements" && <Requirements data={data} />}
          {tab === "pricing" && <Pricing data={data} />}
          {tab === "risks" && <Risks data={data} />}
          {tab === "missing" && <Missing data={data} />}
          {tab === "copilot" && <CopilotPanel projectId={data.project_id} vendorId={data.vendor_id} />}
        </div>
      </Card>
    </div>
  );
}
