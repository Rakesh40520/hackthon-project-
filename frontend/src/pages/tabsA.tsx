import { useState } from "react";
import { Plus, Trash2, ShieldAlert, CheckCircle2, ListFilter } from "lucide-react";
import { Card } from "@/components/Card";
import { StatusBadge } from "@/components/StatusBadge";
import toast from "react-hot-toast";
import { useCreateRequirement, useDeleteRequirement } from "@/hooks/useProposals";

export function RequirementsTab({
  projectId,
  requirements,
  onOpenAddRequirement,
}: {
  projectId: string;
  requirements?: any[];
  onOpenAddRequirement?: () => void;
}) {
  const create = useCreateRequirement(projectId);
  const del = useDeleteRequirement(projectId);
  const [filterCategory, setFilterCategory] = useState<string>("ALL");
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

  const onAdd = async () => {
    if (!form.name.trim()) return;
    try {
      await create.mutateAsync(form);
      setForm({
        name: "",
        description: "",
        category: "TECHNICAL",
        priority: "MEDIUM",
        weight: 1,
        mandatory: false,
      });
      toast.success("Requirement added successfully");
    } catch {
      toast.error("Failed to add requirement");
    }
  };

  const filtered = (requirements || []).filter((r: any) =>
    filterCategory === "ALL" ? true : r.category === filterCategory
  );

  return (
    <div className="space-y-5">
      {/* Add Requirement Quick Panel */}
      <Card className="border border-brand-100 bg-slate-50/50">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <h4 className="font-semibold text-slate-900 text-sm">
              Quick Add Requirement
            </h4>
            <span className="text-xs text-slate-500">
              Define criteria for AI automated proposal evaluation
            </span>
          </div>
          {onOpenAddRequirement && (
            <button
              onClick={onOpenAddRequirement}
              className="text-xs text-brand-600 hover:text-brand-700 font-medium"
            >
              Open Detailed Form &rarr;
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-6 gap-2.5">
          <input
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500 md:col-span-2 bg-white"
            placeholder="Requirement Name (e.g. 99.99% Uptime SLA)"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                onAdd();
              }
            }}
          />
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
          <input
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
            placeholder="Description / Keywords (optional)"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
          <button
            className="flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-semibold text-sm transition shadow-sm"
            onClick={onAdd}
            disabled={!form.name.trim() || create.isPending}
          >
            <Plus className="w-4 h-4" />
            {create.isPending ? "Adding..." : "Add"}
          </button>
        </div>

        <div className="mt-2.5 flex items-center gap-5 text-xs text-slate-700">
          <label className="flex items-center gap-2 cursor-pointer font-medium">
            <input
              type="checkbox"
              className="w-3.5 h-3.5 text-brand-600 rounded border-slate-300 focus:ring-brand-500"
              checked={form.mandatory}
              onChange={(e) =>
                setForm({ ...form, mandatory: e.target.checked })
              }
            />
            <span className="flex items-center gap-1">
              <ShieldAlert className="w-3.5 h-3.5 text-red-500" /> Mandatory
              Criteria
            </span>
          </label>
          <div className="flex items-center gap-1.5">
            <span>Weight:</span>
            <input
              className="w-16 px-2 py-0.5 text-xs rounded border border-slate-300 bg-white focus:outline-none focus:ring-1 focus:ring-brand-500"
              type="number"
              step="0.1"
              min="0.1"
              max="5.0"
              value={form.weight}
              onChange={(e) =>
                setForm({ ...form, weight: Number(e.target.value) })
              }
            />
          </div>
        </div>
      </Card>

      {/* Requirements Table */}
      <Card padded={false} className="overflow-hidden border border-slate-200">
        <div className="p-4 bg-slate-50/70 border-b border-slate-200 flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-slate-900 text-sm">
              Project Requirements ({requirements?.length || 0})
            </h3>
          </div>
          <div className="flex items-center gap-2">
            <ListFilter className="w-3.5 h-3.5 text-slate-400" />
            <select
              className="text-xs px-2.5 py-1 rounded-md border border-slate-300 bg-white focus:outline-none focus:ring-1 focus:ring-brand-500"
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
            >
              <option value="ALL">All Categories</option>
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
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-xs font-semibold text-slate-500 bg-slate-50/50 border-b border-slate-200">
              <tr>
                <th className="text-left p-3.5">Requirement Name</th>
                <th className="text-left p-3.5">Category</th>
                <th className="text-left p-3.5">Priority</th>
                <th className="text-left p-3.5">Weight</th>
                <th className="text-left p-3.5">Mandatory</th>
                <th className="p-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((r: any) => (
                <tr key={r.id} className="hover:bg-slate-50/80 transition">
                  <td className="p-3.5">
                    <div className="font-medium text-slate-900">{r.name}</div>
                    {r.description ? (
                      <div className="text-xs text-slate-500 mt-0.5">
                        {r.description}
                      </div>
                    ) : null}
                  </td>
                  <td className="p-3.5 text-slate-600">
                    <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-slate-100 text-slate-700">
                      {r.category}
                    </span>
                  </td>
                  <td className="p-3.5">
                    <StatusBadge status={r.priority} />
                  </td>
                  <td className="p-3.5 text-slate-600 text-xs font-medium">
                    {r.weight || 1.0}x
                  </td>
                  <td className="p-3.5">
                    {r.mandatory ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-semibold rounded-full bg-red-50 text-red-700 border border-red-200">
                        <ShieldAlert className="w-3 h-3" /> Required
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full bg-slate-100 text-slate-600">
                        Optional
                      </span>
                    )}
                  </td>
                  <td className="p-3.5 text-right">
                    <button
                      className="text-red-500 hover:text-red-700 p-1 rounded hover:bg-red-50 transition"
                      title="Delete Requirement"
                      onClick={() => {
                        if (
                          confirm(
                            `Are you sure you want to delete requirement "${r.name}"?`
                          )
                        ) {
                          del.mutate(r.id);
                        }
                      }}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
              {!filtered.length && (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-500 text-sm">
                    No requirements found in this category. Click <strong>"Add"</strong> above to create one.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}