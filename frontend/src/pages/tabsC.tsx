import { Link } from "react-router-dom";
import { useState } from "react";
import { Card, CardHeader } from "@/components/Card";
import { StatusBadge } from "@/components/StatusBadge";
import { Dropzone } from "@/components/Dropzone";
import { ScoreRing } from "@/components/ScoreRing";
import { format } from "date-fns";
import toast from "react-hot-toast";
import { useUploadProposal } from "@/hooks/useProposals";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { CopilotPanel } from "./CopilotPanel";
import {
  BarChart,
  Bar,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from "recharts";
import {
  Trophy,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  GitCompare,
  ExternalLink,
  ShieldAlert,
  ArrowRight,
} from "lucide-react";

export function ProposalsTab({ projectId, projectVendors, proposals }: any) {
  const upload = useUploadProposal();
  const [vendorId, setVendorId] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const onUpload = async () => {
    if (!file || !vendorId) return;
    try {
      await upload.mutateAsync({ projectId, vendorId, file });
      setFile(null);
      setVendorId("");
      toast.success("Proposal uploaded and analysis started!");
    } catch {
      toast.error("Upload failed");
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <h4 className="font-semibold text-slate-900 text-sm mb-3">
          Upload Vendor Proposal
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <select
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
            value={vendorId}
            onChange={(e) => setVendorId(e.target.value)}
          >
            <option value="">Select vendor...</option>
            {(projectVendors || []).map((pv: any) => (
              <option key={pv.id} value={pv.vendor_id || pv.vendor?.id}>
                {pv.vendor?.company_name || pv.company_name}
              </option>
            ))}
          </select>
          <div className="md:col-span-2">
            <Dropzone
              onFile={setFile}
              selected={file}
              onClear={() => setFile(null)}
            />
          </div>
        </div>
        <div className="mt-3 flex justify-end">
          <button
            className="px-4 py-2 text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 disabled:opacity-50 rounded-lg transition shadow-sm"
            onClick={onUpload}
            disabled={!file || !vendorId || upload.isPending}
          >
            {upload.isPending ? "Uploading & Analyzing..." : "Upload & Analyze"}
          </button>
        </div>
      </Card>

      <Card padded={false} className="border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="text-xs font-semibold text-slate-500 bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="text-left p-3.5">Vendor</th>
              <th className="text-left p-3.5">Proposal Title</th>
              <th className="text-left p-3.5">Status</th>
              <th className="text-left p-3.5">Score</th>
              <th className="text-left p-3.5">Last Updated</th>
              <th className="p-3.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {(proposals || []).map((p: any) => (
              <tr key={p.id} className="hover:bg-slate-50/80 transition">
                <td className="p-3.5">
                  <Link
                    to={`/proposals/${p.id}`}
                    className="font-semibold text-brand-700 hover:text-brand-900 flex items-center gap-1"
                  >
                    {p.vendor_name || p.vendor_company}
                  </Link>
                </td>
                <td className="p-3.5 text-slate-600">{p.title}</td>
                <td className="p-3.5">
                  <StatusBadge status={p.status} />
                </td>
                <td className="p-3.5">
                  {p.score !== undefined && p.score !== null ? (
                    <span className="font-bold text-slate-900 px-2 py-0.5 rounded bg-slate-100">
                      {Math.round(p.score)}/100
                    </span>
                  ) : (
                    "—"
                  )}
                </td>
                <td className="p-3.5 text-slate-500 text-xs">
                  {format(new Date(p.updated_at), "MMM d, HH:mm")}
                </td>
                <td className="p-3.5 text-right">
                  <Link
                    to={`/proposals/${p.id}`}
                    className="text-xs font-semibold text-brand-600 hover:text-brand-800"
                  >
                    View Details &rarr;
                  </Link>
                </td>
              </tr>
            ))}
            {!proposals?.length && (
              <tr>
                <td colSpan={6} className="p-8 text-center text-slate-500">
                  No proposals uploaded yet. Select a vendor and drop a file above.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

export function ComparisonTab({ projectId }: { projectId: string }) {
  const [year, setYear] = useState<"year1" | "year3" | "year5">("year1");
  const { data, isLoading } = useQuery({
    queryKey: ["comparison", projectId],
    queryFn: async () => (await api.get(`/comparison/${projectId}`)).data,
  });

  if (isLoading) return <div className="text-slate-500 text-sm py-4">Loading comparison matrix...</div>;
  if (!data?.vendors?.length) {
    return (
      <Card>
        <div className="text-center text-slate-500 py-8">
          No analyzed proposals found for comparison. Please upload and analyze proposals first.
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
          <GitCompare className="w-5 h-5 text-brand-700" /> Vendor Comparison Matrix
        </h3>
        <Link
          to={`/comparison/${projectId}`}
          className="text-xs font-semibold text-brand-600 hover:text-brand-800 flex items-center gap-1"
        >
          Full Comparison Page <ExternalLink className="w-3.5 h-3.5" />
        </Link>
      </div>

      <Card padded={false} className="border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-xs font-semibold text-slate-600 bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left p-3.5">Vendor</th>
                <th className="text-left p-3.5">Total Score</th>
                <th className="text-left p-3.5">Rank</th>
                <th className="text-left p-3.5">Year 1 Cost</th>
                <th className="text-left p-3.5">3-Year TCO</th>
                <th className="text-left p-3.5">Compliance</th>
                <th className="text-left p-3.5">Critical/High Risks</th>
                <th className="text-left p-3.5">Recommendation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.vendors.map((v: any) => (
                <tr key={v.vendor_id} className="hover:bg-slate-50 transition">
                  <td className="p-3.5 font-bold text-slate-900">{v.vendor_name}</td>
                  <td className="p-3.5">
                    <span className="font-semibold text-slate-800">
                      {v.score ? `${Math.round(v.score.total_score)}/100` : "—"}
                    </span>
                  </td>
                  <td className="p-3.5">
                    {v.score?.rank ? (
                      <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800">
                        #{v.score.rank}
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="p-3.5 font-medium">
                    {v.pricing?.year1_total ? `$${Math.round(v.pricing.year1_total).toLocaleString()}` : "—"}
                  </td>
                  <td className="p-3.5 font-medium text-slate-700">
                    {v.pricing?.year3_total ? `$${Math.round(v.pricing.year3_total).toLocaleString()}` : "—"}
                  </td>
                  <td className="p-3.5">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-emerald-500"
                          style={{ width: `${v.compliance_pct || 0}%` }}
                        />
                      </div>
                      <span className="text-xs text-slate-600 font-medium">
                        {Math.round(v.compliance_pct || 0)}%
                      </span>
                    </div>
                  </td>
                  <td className="p-3.5">
                    <span className="text-xs font-semibold text-red-600">
                      {(v.risk_counts?.CRITICAL || 0) + (v.risk_counts?.HIGH || 0)} Risks
                    </span>
                  </td>
                  <td className="p-3.5">
                    {v.recommendation?.recommended ? (
                      <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-emerald-100 text-emerald-800">
                        RECOMMENDED
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-slate-100 text-slate-600">
                        Alternative
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card>
        <CardHeader
          title="TCO Cost Comparison"
          subtitle="Multi-year expenditure analysis"
          action={
            <div className="flex bg-slate-100 p-1 rounded-lg text-xs">
              {(["year1", "year3", "year5"] as const).map((k) => (
                <button
                  key={k}
                  onClick={() => setYear(k)}
                  className={`px-3 py-1 rounded-md transition ${
                    year === k ? "bg-white shadow-sm font-semibold text-slate-900" : "text-slate-500 hover:text-slate-800"
                  }`}
                >
                  {k === "year1" ? "Year 1" : k === "year3" ? "Year 3" : "Year 5"}
                </button>
              ))}
            </div>
          }
        />
        <div className="h-64">
          <ResponsiveContainer>
            <BarChart data={data.vendors.map((v: any) => ({ name: v.vendor_name, cost: v.pricing?.[year] || 0 }))}>
              <CartesianGrid stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="cost" fill="#3b82f6" radius={[6, 6, 0, 0]} name="Total Cost ($)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
}

export function RisksTab({ projectId }: { projectId: string }) {
  const { data: comparison } = useQuery({
    queryKey: ["comparison", projectId],
    queryFn: async () => (await api.get(`/comparison/${projectId}`)).data,
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-amber-600" /> Contract & Operational Risks
        </h3>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {(comparison?.vendors || []).map((v: any) => (
          <Card key={v.vendor_id} className="border border-slate-200">
            <h4 className="font-bold text-slate-900 text-sm mb-3 pb-2 border-b border-slate-100">
              {v.vendor_name}
            </h4>
            <div className="grid grid-cols-4 gap-2 text-center text-xs mb-3">
              {(["LOW", "MEDIUM", "HIGH", "CRITICAL"] as const).map((sev) => (
                <div key={sev} className="rounded-lg p-2 bg-slate-50 border border-slate-100">
                  <div className="text-base font-bold text-slate-800">{v.risk_counts?.[sev] || 0}</div>
                  <div className="text-[10px] text-slate-500 font-medium">{sev}</div>
                </div>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

export function CopilotTab({ projectId }: { projectId: string }) {
  return (
    <div className="space-y-4">
      <CopilotPanel projectId={projectId} />
    </div>
  );
}

export function RecommendationTab({ projectId }: { projectId: string }) {
  const { data } = useQuery({
    queryKey: ["recommendations", projectId],
    queryFn: async () => (await api.get(`/recommendations/${projectId}`)).data,
  });
  const { data: comparison } = useQuery({
    queryKey: ["comparison", projectId],
    queryFn: async () => (await api.get(`/comparison/${projectId}`)).data,
  });

  const top = (data || []).find((r: any) => r.recommended) || data?.[0];

  return (
    <div className="space-y-5">
      {top ? (
        <Card className="border-2 border-brand-200 bg-gradient-to-br from-brand-50/20 via-white to-white">
          <div className="flex items-center gap-3">
            <Trophy className="w-8 h-8 text-amber-500" />
            <div>
              <div className="text-xs text-brand-700 font-bold uppercase tracking-wider">
                Top Recommended Option
              </div>
              <h2 className="text-2xl font-bold text-slate-900">
                {comparison?.vendors?.find((x: any) => x.proposal_id === top.proposal_id)?.vendor_name || "Recommended Vendor"}
              </h2>
            </div>
            <div className="ml-auto">
              <span className="px-3 py-1 text-xs font-bold rounded-full bg-emerald-100 text-emerald-800">
                Rank #{top.rank || 1}
              </span>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <div className="text-xs text-slate-500 font-semibold uppercase">Executive Summary</div>
              <div className="mt-1 text-sm text-slate-800 font-medium">{top.summary}</div>
            </div>
            <div>
              <div className="text-xs text-slate-500 font-semibold uppercase">Decision Reasoning</div>
              <div className="mt-1 text-sm text-slate-600 leading-relaxed">{top.reasoning}</div>
            </div>
            <div>
              <div className="text-xs text-slate-500 font-semibold uppercase">Next Steps</div>
              <ul className="mt-1 text-sm list-disc pl-5 text-slate-600 space-y-1">
                {(top.next_steps || []).map((s: string, i: number) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-slate-100">
            <div>
              <div className="text-xs text-emerald-700 font-bold uppercase flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Strengths
              </div>
              <ul className="mt-1.5 text-sm list-disc pl-5 text-slate-700 space-y-1">
                {(top.strengths || []).map((s: string, i: number) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
            <div>
              <div className="text-xs text-amber-700 font-bold uppercase flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" /> Risks / Considerations
              </div>
              <ul className="mt-1.5 text-sm list-disc pl-5 text-slate-700 space-y-1">
                {(top.weaknesses || []).map((s: string, i: number) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      ) : (
        <Card>
          <div className="text-center text-slate-500 py-6">
            No recommendations generated yet. Analyze proposals to see AI recommendations.
          </div>
        </Card>
      )}
    </div>
  );
}