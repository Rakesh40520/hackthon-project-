import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Trophy, CheckCircle2, XCircle, Sparkles, MessageCircle, AlertTriangle } from "lucide-react";
import { Card, CardHeader } from "@/components/Card";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";

export default function RecommendationPage() {
  const { projectId } = useParams();
  const { data, isLoading } = useQuery({
    queryKey: ["recommendations", projectId],
    queryFn: async () => (await api.get(`/recommendations/${projectId}`)).data,
    enabled: !!projectId,
  });
  const { data: project } = useQuery({
    queryKey: ["projects", projectId],
    queryFn: async () => (await api.get(`/projects/${projectId}`)).data,
    enabled: !!projectId,
  });
  const { data: comparison } = useQuery({
    queryKey: ["comparison", projectId],
    queryFn: async () => (await api.get(`/comparison/${projectId}`)).data,
    enabled: !!projectId,
  });

  if (isLoading) return <div className="text-slate-500 text-sm">Loading…</div>;
  if (!data) return <div>Not found.</div>;

  const top = data.find((r: any) => r.recommended) || data[0];

  return (
    <div className="space-y-5">
      <div>
        <Link to={`/projects/${projectId}`} className="text-sm text-slate-500 hover:text-slate-700 flex items-center gap-1">
          <ArrowLeft className="w-3 h-3" /> Back to project
        </Link>
      </div>

      <div>
        <h1 className="text-2xl font-bold text-slate-900">Final Recommendation</h1>
        <p className="text-slate-500 text-sm">AI-generated decision rationale for {project?.name}</p>
      </div>

      {top ? (
        <Card>
          <div className="flex items-center gap-3">
            <Trophy className="w-8 h-8 text-yellow-500" />
            <div>
              <div className="text-xs text-slate-500 uppercase tracking-wide">Recommended Vendor</div>
              <h2 className="text-2xl font-bold text-slate-900">{vendorNameForProposalId(top.proposal_id, comparison)}</h2>
            </div>
            <div className="ml-auto">
              <StatusBadge status={top.decision} />
            </div>
          </div>
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <div className="text-xs text-slate-500 uppercase">Summary</div>
              <div className="mt-1 text-sm">{top.summary}</div>
            </div>
            <div>
              <div className="text-xs text-slate-500 uppercase">Reasoning</div>
              <div className="mt-1 text-sm text-slate-600">{top.reasoning}</div>
            </div>
            <div>
              <div className="text-xs text-slate-500 uppercase">Next Steps</div>
              <ul className="mt-1 text-sm list-disc pl-5 text-slate-600">
                {(top.next_steps || []).map((s: string, i: number) => <li key={i}>{s}</li>)}
              </ul>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-slate-500 uppercase flex items-center gap-1"><CheckCircle2 className="w-3 h-3 text-emerald-600" /> Strengths</div>
              <ul className="mt-1 text-sm list-disc pl-5 text-slate-700 space-y-1">
                {(top.strengths || []).map((s: string, i: number) => <li key={i}>{s}</li>)}
              </ul>
            </div>
            <div>
              <div className="text-xs text-slate-500 uppercase flex items-center gap-1"><AlertTriangle className="w-3 h-3 text-amber-600" /> Risks / Weaknesses</div>
              <ul className="mt-1 text-sm list-disc pl-5 text-slate-700 space-y-1">
                {(top.weaknesses || []).map((s: string, i: number) => <li key={i}>{s}</li>)}
              </ul>
            </div>
          </div>
        </Card>
      ) : (
        <Card><div className="text-center text-slate-500">No recommendation yet — run analysis on at least one proposal.</div></Card>
      )}

      <Card>
        <CardHeader title="All Recommendations" />
        <div className="space-y-2">
          {data.map((r: any) => (
            <div key={r.id} className="border border-slate-100 rounded-lg p-3 flex items-center gap-3">
              <div className="font-semibold text-sm w-48 truncate">{vendorNameForProposalId(r.proposal_id, comparison)}</div>
              <StatusBadge status={r.decision} />
              <div className="text-xs text-slate-500 flex-1">{r.summary}</div>
            </div>
          ))}
          {!data.length && <div className="text-sm text-slate-500">No recommendations yet.</div>}
        </div>
      </Card>

      <div className="text-sm text-slate-500 flex items-center gap-2">
        <MessageCircle className="w-4 h-4" />
        Need more detail? Open the <Link to={`/analysis/${projectId}`} className="text-accent-600 font-medium">AI Copilot</Link>.
      </div>
    </div>
  );
}

function vendorNameForProposalId(proposalId: string, comparison: any): string {
  if (!comparison?.vendors) return "Vendor";
  const v = comparison.vendors.find((x: any) => x.proposal_id === proposalId);
  return v?.vendor_name || "Vendor";
}
