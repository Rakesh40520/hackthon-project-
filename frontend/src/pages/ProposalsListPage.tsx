import { Link } from "react-router-dom";
import { useState } from "react";
import { Search, FileText, ArrowRight, ExternalLink } from "lucide-react";
import { Card } from "@/components/Card";
import { StatusBadge } from "@/components/StatusBadge";
import { EmptyState } from "@/components/EmptyState";
import { useProposals } from "@/hooks/useProposals";
import { format } from "date-fns";

export default function ProposalsListPage() {
  const [q, setQ] = useState("");
  const { data, isLoading } = useProposals();
  const filtered = (data || []).filter(
    (p) =>
      !q ||
      p.title.toLowerCase().includes(q.toLowerCase()) ||
      (p.vendor_name || "").toLowerCase().includes(q.toLowerCase()) ||
      (p.vendor_company || "").toLowerCase().includes(q.toLowerCase())
  );

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Proposals</h1>
        <p className="text-slate-500 text-sm">
          All uploaded and analyzed vendor proposals
        </p>
      </div>

      <div className="relative max-w-md">
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
          placeholder="Search proposals by title or vendor name..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>

      {isLoading ? (
        <div className="text-slate-500 text-sm py-4">Loading proposals...</div>
      ) : !filtered.length ? (
        <Card>
          <EmptyState
            title="No proposals found"
            description="Upload proposals from any active procurement project page."
            icon={<FileText className="w-6 h-6" />}
          />
        </Card>
      ) : (
        <Card padded={false} className="border border-slate-200 overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs font-semibold text-slate-500 bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left p-3.5">Vendor</th>
                  <th className="text-left p-3.5">Proposal Title</th>
                  <th className="text-left p-3.5">Evaluation Status</th>
                  <th className="text-left p-3.5">AI Score</th>
                  <th className="text-left p-3.5">Last Updated</th>
                  <th className="p-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/80 transition">
                    <td className="p-3.5">
                      <Link
                        to={`/proposals/${p.id}`}
                        className="font-bold text-slate-900 hover:text-brand-700 transition"
                      >
                        {p.vendor_name || p.vendor_company || "Vendor"}
                      </Link>
                    </td>
                    <td className="p-3.5 text-slate-600 font-medium">
                      {p.title}
                    </td>
                    <td className="p-3.5">
                      <StatusBadge status={p.status} />
                    </td>
                    <td className="p-3.5">
                      {p.score !== undefined && p.score !== null ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
                          {Math.round(p.score)}/100
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400">Pending</span>
                      )}
                    </td>
                    <td className="p-3.5 text-slate-500 text-xs">
                      {p.updated_at ? format(new Date(p.updated_at), "MMM d, HH:mm") : "—"}
                    </td>
                    <td className="p-3.5 text-right">
                      <Link
                        to={`/proposals/${p.id}`}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-brand-600 hover:text-brand-800"
                      >
                        View Analysis <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}