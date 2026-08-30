import { useState } from "react";
import { Plus, Search, Building2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Card } from "@/components/Card";
import { StatusBadge } from "@/components/StatusBadge";
import { EmptyState } from "@/components/EmptyState";
import { useVendors, useCreateVendor } from "@/hooks/useVendors";
import toast from "react-hot-toast";

export default function VendorsPage() {
  const [q, setQ] = useState("");
  const navigate = useNavigate();
  const { data, isLoading } = useVendors(q);
  const create = useCreateVendor();
  const [showNew, setShowNew] = useState(false);
  const [form, setForm] = useState({ company_name: "", contact_name: "", email: "", industry: "", description: "" });

  const onCreate = async () => {
    try { await create.mutateAsync(form); toast.success("Vendor created"); setShowNew(false); setForm({ company_name: "", contact_name: "", email: "", industry: "", description: "" }); }
    catch { toast.error("Failed to create vendor"); }
  };

  const handleVendorClick = (vendorId: number) => {
    navigate(`/proposals?vendor=${vendorId}`);
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Vendors</h1>
          <p className="text-slate-500 text-sm">Global vendor directory</p>
        </div>
        <button className="btn-primary" onClick={() => setShowNew(true)}><Plus className="w-4 h-4" /> New Vendor</button>
      </div>
      <div className="relative max-w-md">
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input className="input pl-9" placeholder="Search vendors…" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      {isLoading ? <div className="text-slate-500 text-sm">Loading…</div> : !data?.length ? (
        <Card><EmptyState title="No vendors yet" description="Add your first vendor to start." icon={<Building2 className="w-6 h-6" />} /></Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.map((v) => (
            <Card
              key={v.id}
              className="hover:shadow-elev transition cursor-pointer"
              onClick={() => handleVendorClick(v.id)}
            >
              <div className="flex items-start justify-between">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-700 text-white flex items-center justify-center">
                  <Building2 className="w-5 h-5" />
                </div>
                <StatusBadge status={v.status} />
              </div>
              <h3 className="mt-3 font-semibold text-slate-900">{v.company_name}</h3>
              {v.industry ? <div className="text-xs text-slate-500">{v.industry}</div> : null}
              {v.description ? <p className="mt-2 text-xs text-slate-600 line-clamp-2">{v.description}</p> : null}
              {v.email ? <div className="mt-2 text-xs text-slate-500">{v.email}</div> : null}
            </Card>
          ))}
        </div>
      )}

      {showNew && (
        <div className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4" onClick={() => setShowNew(false)}>
          <Card className="w-full max-w-md" >
            <div onClick={(e) => e.stopPropagation()}>
              <h3 className="text-lg font-semibold mb-4">New Vendor</h3>
              <div className="space-y-3">
                <div><label className="label">Company Name</label><input className="input" value={form.company_name} onChange={(e) => setForm({ ...form, company_name: e.target.value })} /></div>
                <div><label className="label">Contact Name</label><input className="input" value={form.contact_name} onChange={(e) => setForm({ ...form, contact_name: e.target.value })} /></div>
                <div><label className="label">Email</label><input className="input" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></div>
                <div><label className="label">Industry</label><input className="input" value={form.industry} onChange={(e) => setForm({ ...form, industry: e.target.value })} /></div>
                <div><label className="label">Description</label><textarea className="input" rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
              </div>
              <div className="flex justify-end gap-2 mt-4">
                <button className="btn-secondary" onClick={() => setShowNew(false)}>Cancel</button>
                <button className="btn-primary" onClick={onCreate} disabled={!form.company_name || create.isPending}>{create.isPending ? "Creating…" : "Create"}</button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
