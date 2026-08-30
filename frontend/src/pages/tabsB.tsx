import { useState } from "react";
import { Plus } from "lucide-react";
import { Card } from "@/components/Card";
import { StatusBadge } from "@/components/StatusBadge";
import toast from "react-hot-toast";
import { useAddProjectVendor } from "@/hooks/useProposals";

export function VendorsTab({ projectId, projectVendors, allVendors }: any) {
  const add = useAddProjectVendor(projectId);
  const [vendorId, setVendorId] = useState("");
  const onAdd = async () => {
    if (!vendorId) return;
    try { await add.mutateAsync({ vendor_id: vendorId }); setVendorId(""); toast.success("Vendor added"); }
    catch { toast.error("Could not add vendor"); }
  };
  const available = (allVendors || []).filter((v: any) => !(projectVendors || []).some((pv: any) => pv.vendor_id === v.id));
  return (
    <div className="space-y-4">
      <Card>
        <h4 className="font-semibold mb-3">Add Vendor to Project</h4>
        <div className="flex gap-2">
          <select className="input" value={vendorId} onChange={(e) => setVendorId(e.target.value)}>
            <option value="">Select vendor…</option>
            {available.map((v: any) => <option key={v.id} value={v.id}>{v.company_name}</option>)}
          </select>
          <button className="btn-primary" onClick={onAdd} disabled={!vendorId}><Plus className="w-4 h-4" /> Add</button>
        </div>
      </Card>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {(projectVendors || []).map((pv: any) => (
          <Card key={pv.id} className="flex items-center justify-between">
            <div>
              <div className="font-semibold">{pv.vendor?.company_name || pv.company_name}</div>
              <div className="text-xs text-slate-500">{pv.vendor?.industry || pv.industry}</div>
            </div>
            <StatusBadge status={pv.status} />
          </Card>
        ))}
        {!projectVendors?.length && <Card><div className="text-center text-slate-500 py-6">No vendors added yet.</div></Card>}
      </div>
    </div>
  );
}
