import { Link, useParams } from "react-router-dom";
import { useState } from "react";
import {
  ArrowLeft,
  FolderKanban,
  Building2,
  ListChecks,
  FileText,
  GitCompare,
  AlertTriangle,
  Sparkles,
  BarChart3,
  Plus,
  X,
} from "lucide-react";
import { useProject } from "@/hooks/useProjects";
import {
  useRequirements,
  useProposals,
  useProjectVendors,
  useCreateRequirement,
} from "@/hooks/useProposals";
import { useVendors } from "@/hooks/useVendors";
import { Card } from "@/components/Card";
import { StatusBadge } from "@/components/StatusBadge";
import clsx from "clsx";
import { format } from "date-fns";
import toast from "react-hot-toast";
import {
  OverviewTab,
  RequirementsTab,
  VendorsTab,
  ProposalsTab,
  ComparisonTab,
  RisksTab,
  CopilotTab,
  RecommendationTab,
} from "./ProjectDetailTabs";

const TABS = [
  { id: "overview", label: "Overview", icon: FolderKanban },
  { id: "requirements", label: "Requirements", icon: ListChecks },
  { id: "vendors", label: "Vendors", icon: Building2 },
  { id: "proposals", label: "Proposals", icon: FileText },
  { id: "comparison", label: "Comparison", icon: GitCompare },
  { id: "risks", label: "Risks", icon: AlertTriangle },
  { id: "copilot", label: "AI Copilot", icon: Sparkles },
  { id: "recommendation", label: "Recommendation", icon: BarChart3 },
];

export default function ProjectDetailPage() {
  const { id } = useParams();
  const { data: project, isLoading } = useProject(id);
  const { data: requirements } = useRequirements(id);
  const { data: projectVendors } = useProjectVendors(id);
  const { data: proposals } = useProposals(id);
  const { data: allVendors } = useVendors();
  const [tab, setTab] = useState("overview");
  const [isAddReqOpen, setIsAddReqOpen] = useState(false);

  if (isLoading) return <div className="text-slate-500 text-sm">Loading...</div>;
  if (!project) return <div>Project not found.</div>;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <Link
          to="/projects"
          className="text-sm text-slate-500 hover:text-slate-700 flex items-center gap-1 transition"
        >
          <ArrowLeft className="w-4 h-4" /> Back to projects
        </Link>
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setIsAddReqOpen(true)}
            className="flex items-center gap-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 font-medium px-3.5 py-2 rounded-lg text-sm transition shadow-sm"
          >
            <Plus className="w-4 h-4 text-brand-700" /> Add Requirement
          </button>
          <button
            onClick={() => setTab("comparison")}
            className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold px-4 py-2 rounded-lg text-sm transition shadow-sm"
          >
            <GitCompare className="w-4 h-4" /> Compare Vendors
          </button>
        </div>
      </div>

      <Card>
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 text-white flex items-center justify-center shadow-sm">
              <FolderKanban className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">{project.name}</h1>
              <div className="text-sm text-slate-500">{project.description || project.category}</div>
            </div>
          </div>
          <div className="flex items-center gap-6 text-sm">
            <StatusBadge status={project.status} />
            <div className="text-right">
              <div className="text-xs text-slate-500">Budget</div>
              <div className="font-semibold">{project.currency} {project.budget ? project.budget.toLocaleString() : "—"}</div>
            </div>
            <div className="text-right">
              <div className="text-xs text-slate-500">Deadline</div>
              <div className="font-semibold">{project.deadline ? format(new Date(project.deadline), "MMM d, yyyy") : "—"}</div>
            </div>
            <div className="text-right">
              <div className="text-xs text-slate-500">Vendors</div>
              <div className="font-semibold">{project.vendor_count || 0}</div>
            </div>
            <div className="text-right">
              <div className="text-xs text-slate-500">Proposals</div>
              <div className="font-semibold">{project.proposal_count || 0}</div>
            </div>
          </div>
        </div>

        <div className="mt-5 border-b border-slate-200 flex gap-1 overflow-x-auto">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={clsx(
                "px-3 py-2 text-sm font-medium border-b-2 flex items-center gap-2 transition whitespace-nowrap",
                tab === t.id
                  ? "border-brand-800 text-brand-800"
                  : "border-transparent text-slate-500 hover:text-slate-700"
              )}
            >
              <t.icon className="w-4 h-4" /> {t.label}
            </button>
          ))}
        </div>

        <div className="mt-5">
          {tab === "overview" && (
            <OverviewTab
              project={project}
              requirements={requirements}
              projectVendors={projectVendors}
              proposals={proposals}
              onNavigateTab={(t: string) => setTab(t)}
              onOpenAddRequirement={() => setIsAddReqOpen(true)}
            />
          )}
          {tab === "requirements" && (
            <RequirementsTab
              projectId={id!}
              requirements={requirements}
              onOpenAddRequirement={() => setIsAddReqOpen(true)}
            />
          )}
          {tab === "vendors" && (
            <VendorsTab
              projectId={id!}
              projectVendors={projectVendors}
              allVendors={allVendors}
            />
          )}
          {tab === "proposals" && (
            <ProposalsTab
              projectId={id!}
              projectVendors={projectVendors}
              proposals={proposals}
            />
          )}
          {tab === "comparison" && <ComparisonTab projectId={id!} />}
          {tab === "risks" && <RisksTab projectId={id!} />}
          {tab === "copilot" && <CopilotTab projectId={id!} />}
          {tab === "recommendation" && <RecommendationTab projectId={id!} />}
        </div>
      </Card>

      {/* Add Requirement Modal Dialog */}
      {isAddReqOpen && (
        <AddRequirementModal
          projectId={id!}
          onClose={() => setIsAddReqOpen(false)}
        />
      )}
    </div>
  );
}

function AddRequirementModal({
  projectId,
  onClose,
}: {
  projectId: string;
  onClose: () => void;
}) {
  const create = useCreateRequirement(projectId);
  const [form, setForm] = useState<{
    name: string;
    description: string;
    category: string;
    priority: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
    weight: number;
    mandatory: boolean;
  }>({
    name: "",
    description: "",
    category: "TECHNICAL",
    priority: "MEDIUM",
    weight: 1,
    mandatory: false,
  });

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) {
      toast.error("Please enter a requirement name");
      return;
    }
    try {
      await create.mutateAsync(form);
      toast.success("Requirement added successfully!");
      onClose();
    } catch {
      toast.error("Failed to add requirement");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl border border-slate-200 animate-in fade-in zoom-in duration-150">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-brand-50 text-brand-700 flex items-center justify-center">
              <ListChecks className="w-4 h-4" />
            </div>
            <h3 className="font-semibold text-slate-900 text-lg">
              Add New Requirement
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 rounded-lg p-1 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={onSubmit} className="mt-4 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Requirement Name *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. 99.99% Uptime SLA or SOC 2 Type II Compliance"
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Description / Evaluation Criteria
            </label>
            <textarea
              rows={2}
              placeholder="Provide context or specific criteria for the AI evaluation..."
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Category
              </label>
              <select
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
              >
                {[
                  "TECHNICAL",
                  "COMMERCIAL",
                  "BUSINESS",
                  "SECURITY",
                  "SUPPORT",
                  "COMPLIANCE",
                ].map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Priority
              </label>
              <select
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
                value={form.priority}
                onChange={(e) =>
                  setForm({
                    ...form,
                    priority: e.target.value as
                      | "LOW"
                      | "MEDIUM"
                      | "HIGH"
                      | "CRITICAL",
                  })
                }
              >
                {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 items-center pt-1">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Weight (0.1 - 5.0)
              </label>
              <input
                type="number"
                step="0.1"
                min="0.1"
                max="5.0"
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
                value={form.weight}
                onChange={(e) =>
                  setForm({ ...form, weight: Number(e.target.value) })
                }
              />
            </div>
            <div className="pt-5">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  className="w-4 h-4 text-brand-600 rounded border-slate-300 focus:ring-brand-500"
                  checked={form.mandatory}
                  onChange={(e) =>
                    setForm({ ...form, mandatory: e.target.checked })
                  }
                />
                <span className="text-xs font-semibold text-slate-800">
                  Mandatory (Failing disqualifies vendor)
                </span>
              </label>
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={create.isPending}
              className="px-4 py-2 text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-lg transition shadow-sm flex items-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              {create.isPending ? "Adding..." : "Add Requirement"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}