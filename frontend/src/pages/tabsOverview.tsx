import { Card, CardHeader } from "@/components/Card";
import { StatusBadge } from "@/components/StatusBadge";
import { format } from "date-fns";
import { GitCompare, ListChecks, FileUp, Sparkles, ArrowRight, Plus } from "lucide-react";

function Row({ label, value }: { label: string; value: any }) {
  return (
    <div className="flex justify-between py-1 border-b border-slate-50 last:border-0">
      <dt className="text-slate-500">{label}</dt>
      <dd className="font-medium text-slate-800">{value}</dd>
    </div>
  );
}

export function OverviewTab({
  project,
  requirements,
  projectVendors,
  proposals,
  onNavigateTab,
  onOpenAddRequirement,
}: {
  project: any;
  requirements: any;
  projectVendors: any;
  proposals: any;
  onNavigateTab?: (tab: string) => void;
  onOpenAddRequirement?: () => void;
}) {
  return (
    <div className="space-y-6">
      {/* Quick Action Navigation Strip */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl border border-blue-100 bg-gradient-to-br from-blue-50 to-indigo-50/30 flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-blue-600 uppercase tracking-wider">Evaluation</div>
            <div className="text-base font-bold text-slate-900 mt-0.5">Compare Vendors</div>
            <div className="text-xs text-slate-500 mt-1">Side-by-side compliance & pricing matrix</div>
          </div>
          <button
            onClick={() => onNavigateTab?.("comparison")}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-sm transition"
          >
            <GitCompare className="w-3.5 h-3.5" /> Compare
          </button>
        </div>

        <div className="p-4 rounded-xl border border-emerald-100 bg-gradient-to-br from-emerald-50 to-teal-50/30 flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-emerald-600 uppercase tracking-wider">Requirements</div>
            <div className="text-base font-bold text-slate-900 mt-0.5">{requirements?.length || 0} Defined</div>
            <div className="text-xs text-slate-500 mt-1">Technical, security, and commercial criteria</div>
          </div>
          <button
            onClick={onOpenAddRequirement || (() => onNavigateTab?.("requirements"))}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition"
          >
            <Plus className="w-3.5 h-3.5" /> Add
          </button>
        </div>

        <div className="p-4 rounded-xl border border-violet-100 bg-gradient-to-br from-violet-50 to-purple-50/30 flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-violet-600 uppercase tracking-wider">AI Copilot & Recs</div>
            <div className="text-base font-bold text-slate-900 mt-0.5">Recommendations</div>
            <div className="text-xs text-slate-500 mt-1">AI rankings, strengths & weaknesses</div>
          </div>
          <button
            onClick={() => onNavigateTab?.("recommendation")}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-violet-600 hover:bg-violet-700 text-white text-xs font-semibold shadow-sm transition"
          >
            <Sparkles className="w-3.5 h-3.5" /> View
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <Card>
          <CardHeader title="Project Details" />
          <dl className="text-sm space-y-1">
            <Row label="Category" value={project.category || "General Procurement"} />
            <Row label="Budget" value={`${project.currency} ${project.budget ? project.budget.toLocaleString() : "—"}`} />
            <Row label="Deadline" value={project.deadline ? format(new Date(project.deadline), "MMM d, yyyy") : "—"} />
            <Row label="Status" value={<StatusBadge status={project.status} />} />
            <Row label="Requirements" value={`${requirements?.length || 0}`} />
            <Row label="Vendors" value={`${projectVendors?.length || 0}`} />
            <Row label="Proposals" value={`${proposals?.length || 0}`} />
          </dl>
        </Card>

        <Card>
          <CardHeader title="Scoring Weights" subtitle="Configured at project level" />
          <div className="space-y-2.5">
            {[
              ["Price", project.weight_price],
              ["Technical", project.weight_technical],
              ["Security", project.weight_security],
              ["Support", project.weight_support],
              ["Implementation", project.weight_implementation],
              ["Contract", project.weight_contract],
            ].map(([label, val]) => (
              <div key={label as string}>
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-slate-700">{label as string}</span>
                  <span className="text-slate-500 font-semibold">{Math.round((val as number) * 100)}%</span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden mt-1">
                  <div className="h-full bg-brand-600 rounded-full" style={{ width: `${(val as number) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}