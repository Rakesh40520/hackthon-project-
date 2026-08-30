import { Card, CardHeader } from "@/components/Card";
import { useDashboard } from "@/hooks/useProposals";
import {
  BarChart, Bar, ResponsiveContainer, XAxis, YAxis, Tooltip,
  PieChart, Pie, Cell, CartesianGrid, LineChart, Line,
} from "recharts";
import {
  FolderKanban, Users, FileText, AlertTriangle, Clock,
  DollarSign, TrendingUp, Sparkles, ArrowRight, ShieldAlert, CheckCircle2,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useProjects } from "@/hooks/useProjects";

const RISK_COLORS: Record<string, string> = {
  LOW: "#10b981", MEDIUM: "#f59e0b", HIGH: "#ef4444", CRITICAL: "#991b1b",
};

export default function DashboardPage() {
  const { data, isLoading } = useDashboard();
  if (isLoading) return <div className="text-slate-500 text-sm">Loading dashboard...</div>;
  const cards = data?.cards || {};

  const kpis = [
    { label: "Active Projects", value: cards.active_projects, icon: FolderKanban, color: "from-blue-500 to-blue-600" },
    { label: "Vendors Evaluated", value: cards.vendors_evaluated, icon: Users, color: "from-emerald-500 to-emerald-600" },
    { label: "Proposals Analyzed", value: cards.proposals_analyzed, icon: FileText, color: "from-violet-500 to-violet-600" },
    { label: "Potential Savings", value: `$${Math.round(cards.potential_savings || 0).toLocaleString()}`, icon: DollarSign, color: "from-amber-500 to-amber-600" },
    { label: "High-Risk Vendors", value: cards.high_risk_vendors, icon: AlertTriangle, color: "from-red-500 to-red-600" },
    { label: "Pending Reviews", value: cards.pending_reviews, icon: Clock, color: "from-slate-500 to-slate-600" },
  ];

  return (
    <div className="space-y-6">
      {/* Problem & Solution Mission Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-brand-900 to-slate-900 p-6 text-white shadow-lg border border-slate-800">
        <div className="relative z-10 max-w-4xl space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full bg-brand-500/20 px-3 py-1 text-xs font-semibold text-brand-300 border border-brand-500/30">
            <Sparkles className="w-3.5 h-3.5" /> AI-Powered Procurement Intelligence
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
            Procurement Teams Struggled to Compare Vendor Proposals
          </h2>
          <p className="text-sm text-slate-300 leading-relaxed">
            <strong className="text-white">Problem:</strong> Companies received proposals from multiple vendors with different pricing structures, terms, features, and conditions. Comparing them manually was time-consuming and made it easy to overlook critical risks and differences.
          </p>
          <div className="pt-1 flex flex-wrap items-center gap-4 text-xs text-slate-300">
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-emerald-400" /> Commercial & Technical Extraction</span>
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-emerald-400" /> Requirement Compliance Matrix</span>
            <span className="flex items-center gap-1.5"><ShieldAlert className="w-4 h-4 text-amber-400" /> Risk & Missing Info Detection</span>
            <span className="flex items-center gap-1.5"><Sparkles className="w-4 h-4 text-blue-400" /> Objective AI Recommendations</span>
          </div>
          <div className="pt-2 flex items-center gap-3">
            <Link
              to="/projects"
              className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-xs font-semibold text-white hover:bg-brand-500 transition shadow-sm"
            >
              Explore Projects <ArrowRight className="w-3.5 h-3.5" />
            </Link>
            <Link
              to="/proposals"
              className="inline-flex items-center gap-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 px-4 py-2 text-xs font-medium text-slate-200 transition border border-slate-700"
            >
              Analyze Proposals
            </Link>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-slate-500 text-sm">Procurement intelligence overview & vendor analytics</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {kpis.map((k) => (
          <Card key={k.label} className="relative overflow-hidden">
            <div className={`absolute -top-6 -right-6 w-20 h-20 rounded-full bg-gradient-to-br ${k.color} opacity-10`} />
            <div className={`w-9 h-9 rounded-lg bg-gradient-to-br ${k.color} text-white flex items-center justify-center mb-3`}>
              <k.icon className="w-4 h-4" />
            </div>
            <div className="text-2xl font-bold text-slate-900">{k.value}</div>
            <div className="text-xs text-slate-500 mt-1">{k.label}</div>
          </Card>
        ))}
      </div>
      <DashboardCharts />
    </div>
  );
}

function DashboardCharts() {
  const { data } = useDashboard();
  const { data: projects } = useProjects();
  const risk = data?.risk_distribution || {};
  const vendor_scores = (data?.vendor_scores || []).slice(0, 8);
  const cost = data?.cost_comparison || [];
  const compliance = data?.compliance || [];
  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader title="Vendor Scores" subtitle="Top evaluated proposals" icon={<TrendingUp className="w-4 h-4" />} />
          <div className="h-64">
            <ResponsiveContainer>
              <BarChart data={vendor_scores}>
                <CartesianGrid stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="vendor_name" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} domain={[0, 100]} />
                <Tooltip />
                <Bar dataKey="score" fill="#3b82f6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card>
          <CardHeader title="Cost Comparison" subtitle="Total cost over time" />
          <div className="h-64">
            <ResponsiveContainer>
              <LineChart data={cost}>
                <CartesianGrid stroke="#f1f5f9" />
                <XAxis dataKey="vendor_id" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip />
                <Line type="monotone" dataKey="year1" stroke="#3b82f6" strokeWidth={2} name="Year 1" />
                <Line type="monotone" dataKey="year3" stroke="#10b981" strokeWidth={2} name="Year 3" />
                <Line type="monotone" dataKey="year5" stroke="#f59e0b" strokeWidth={2} name="Year 5" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card>
          <CardHeader title="Risk Distribution" subtitle="Identified vendor risks" />
          <div className="h-64">
            <ResponsiveContainer>
              <PieChart>
                <Pie
                  data={[
                    { name: "Low", value: risk.LOW || 0 },
                    { name: "Medium", value: risk.MEDIUM || 0 },
                    { name: "High", value: risk.HIGH || 0 },
                    { name: "Critical", value: risk.CRITICAL || 0 },
                  ]}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={45}
                  outerRadius={80}
                  paddingAngle={4}
                >
                  {[RISK_COLORS.LOW, RISK_COLORS.MEDIUM, RISK_COLORS.HIGH, RISK_COLORS.CRITICAL].map((c, i) => (
                    <Cell key={i} fill={c} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader title="Recent Projects" icon={<FolderKanban className="w-4 h-4" />} />
          <div className="space-y-2">
            {(projects || []).slice(0, 5).map((p) => (
              <Link key={p.id} to={`/projects/${p.id}`} className="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 border border-slate-100 transition">
                <div>
                  <div className="font-medium text-sm text-slate-800">{p.name}</div>
                  <div className="text-xs text-slate-500">
                    {p.category} • {p.vendor_count || 0} vendors • {p.proposal_count || 0} proposals
                  </div>
                </div>
                <div className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium">{p.status}</div>
              </Link>
            ))}
            {!projects?.length && <div className="text-sm text-slate-500">No projects yet.</div>}
          </div>
        </Card>
        <Card>
          <CardHeader title="Compliance %" subtitle="Per vendor against requirements" icon={<Sparkles className="w-4 h-4" />} />
          <div className="space-y-3">
            {(compliance || []).slice(0, 6).map((c: any) => (
              <div key={c.vendor_id} className="flex items-center gap-3">
                <div className="text-xs w-32 truncate text-slate-700">{c.vendor_name}</div>
                <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-500" style={{ width: `${c.compliance}%` }} />
                </div>
                <div className="text-xs text-slate-500 w-10 text-right">{Math.round(c.compliance)}%</div>
              </div>
            ))}
            {!compliance.length && <div className="text-sm text-slate-500">No data.</div>}
          </div>
        </Card>
      </div>
    </>
  );
}