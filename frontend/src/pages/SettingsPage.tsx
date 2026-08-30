import { useState } from "react";
import { Card, CardHeader } from "@/components/Card";
import { useAuth } from "@/hooks/useAuth";
import api from "@/lib/api";
import toast from "react-hot-toast";

export default function SettingsPage() {
  const { user, refresh } = useAuth();
  const [form, setForm] = useState({ name: user?.name || "", company: user?.company || "" });
  const [pwd, setPwd] = useState({ current_password: "", new_password: "" });
  const [saving, setSaving] = useState(false);

  const save = async () => {
    setSaving(true);
    try { await api.patch("/auth/me", form); await refresh(); toast.success("Profile updated"); }
    catch (e: any) { toast.error("Update failed"); }
    finally { setSaving(false); }
  };

  const changePwd = async () => {
    try { await api.post("/auth/change-password", pwd); toast.success("Password changed"); setPwd({ current_password: "", new_password: "" }); }
    catch (e: any) { toast.error(e?.response?.data?.detail || "Failed"); }
  };

  return (
    <div className="space-y-5 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
        <p className="text-slate-500 text-sm">Manage your account</p>
      </div>

      <Card>
        <CardHeader title="Profile" />
        <div className="space-y-3">
          <div><label className="label">Name</label><input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
          <div><label className="label">Company</label><input className="input" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} /></div>
          <div><label className="label">Email</label><input className="input" value={user?.email || ""} disabled /></div>
          <div><label className="label">Role</label><input className="input" value={user?.role || ""} disabled /></div>
          <div className="flex justify-end"><button className="btn-primary" onClick={save} disabled={saving}>{saving ? "Saving…" : "Save"}</button></div>
        </div>
      </Card>

      <Card>
        <CardHeader title="Change Password" />
        <div className="space-y-3">
          <div><label className="label">Current password</label><input className="input" type="password" value={pwd.current_password} onChange={(e) => setPwd({ ...pwd, current_password: e.target.value })} /></div>
          <div><label className="label">New password</label><input className="input" type="password" value={pwd.new_password} onChange={(e) => setPwd({ ...pwd, new_password: e.target.value })} /></div>
          <div className="flex justify-end"><button className="btn-primary" onClick={changePwd} disabled={!pwd.current_password || !pwd.new_password}>Change password</button></div>
        </div>
      </Card>
    </div>
  );
}
