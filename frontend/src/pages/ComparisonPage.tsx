import { useParams } from "react-router-dom";
import { useState } from "react";
import { Trophy, Medal, Award } from "lucide-react";
import { useComparison } from "@/hooks/useProposals";
import { Card, CardHeader } from "@/components/Card";
import { BarChart, Bar, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from "recharts";
import { EmptyState } from "@/components/EmptyState";

export default function ComparisonPage() {
  const { projectId } = useParams();
  const { data, isLoading } = useComparison(projectId);
  const [year, setYear] = useState<"year1" | "year3" | "year5">("year1");

  if (isLoading) return <div className="text-slate-500 text-sm">Loading…</div>;
  if (!data) return <div>Not found.</div>;

  const medalIcons = [Trophy, Medal, Award];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{data.project_name}</h1>
        <p className="text-slate-500 text-sm">Side-by-side vendor comparison</p>
      </div>

      <Card>
        <CardHeader title="Overall Ranking" subtitle="Based on weighted scoring" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {data.ranking.map((r, i) => {
            const Icon = medalIcons[i] || Award;
            return (
              <div key={r.vendor_id} className="flex items-center gap-3 p-4 rounded-lg border border-slate-200">
                <Icon className={`w-6 h-6 ${i === 0 ? "text-yellow-500" : i === 1 ? "text-slate-400" : "text-amber-700"}`} />
                <div className="flex-1">
                  <div className="font-semibold text-sm">{r.vendor_name}</div>
                  <div className="text-xs text-slate-500">{r.eligible ? "Eligible" : "Ineligible"}</div>
                </div>
                <div className="text-2xl font-bold">{Math.round(r.score)}</div>
              </div>
            );
          })}
          {!data.ranking.length && <EmptyState title="No ranked vendors" description="Add proposals to see rankings." />}
        </div>
      </Card>

      <Card>
        <CardHeader
          title="Pricing"
          action={
            <div className="flex gap-1 bg-slate-100 rounded-lg p-1 text-xs">
              {(["year1", "year3", "year5"] as const).map((k) => (
                <button
                  key={k}
                  onClick={() => setYear(k)}
                  className={`px-3 py-1 rounded-md ${year === k ? "bg-white shadow-sm font-medium" : "text-slate-500"}`}
                >
                  {k === "year1" ? "Year 1" : k === "year3" ? "Year 3" : "Year 5"}
                </button>
              ))}
            </div>
          }
        />
        <div className="h-72">
          <ResponsiveContainer>
            <BarChart data={data.vendors.map((v) => ({ name: v.vendor_name, cost: v.pricing?.[year] }))}>
              <CartesianGrid stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="cost" fill="#3b82f6" radius={[6, 6, 0, 0]} name="Total Cost" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <Card>
          <CardHeader title="Requirement Compliance" />
          <div className="space-y-3">
            {data.vendors.map((v) => (
              <div key={v.vendor_id}>
                <div className="flex justify-between text-sm">
                  <span className="font-medium">{v.vendor_name}</span>
                  <span className="text-slate-500">{Math.round(v.compliance_pct)}%</span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden mt-1">
                  <div className="h-full bg-emerald-500" style={{ width: `${v.compliance_pct}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <CardHeader title="Risk Summary" />
          <div className="space-y-3">
            {data.vendors.map((v) => (
              <div key={v.vendor_id} className="border border-slate-100 rounded-lg p-3">
                <div className="font-medium text-sm mb-2">{v.vendor_name}</div>
                <div className="grid grid-cols-4 gap-2 text-center text-xs">
                  {(["LOW", "MEDIUM", "HIGH", "CRITICAL"] as const).map((sev) => (
                    <div key={sev} className="rounded-md p-2 bg-slate-50">
                      <div className="text-lg font-semibold">{v.risk_counts[sev] || 0}</div>
                      <div className="text-slate-500">{sev.charAt(0) + sev.slice(1).toLowerCase()}</div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
