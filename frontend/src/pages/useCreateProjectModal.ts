import { useState } from "react";
import toast from "react-hot-toast";
import { useCreateProject } from "@/hooks/useProjects";

export function useCreateProjectModal() {
  const [showNew, setShowNew] = useState(false);
  const [form, setForm] = useState({ name: "", description: "", category: "", budget: 0, currency: "USD", status: "DRAFT" as "DRAFT" | "ACTIVE" | "EVALUATION" | "COMPLETED" | "CANCELLED" });
  const create = useCreateProject();

  const submit = async () => {
    try {
      await create.mutateAsync(form);
      toast.success("Project created");
      setShowNew(false);
      setForm({ name: "", description: "", category: "", budget: 0, currency: "USD", status: "DRAFT" });
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Failed to create project");
    }
  };

  return { showNew, setShowNew, form, setForm, create, submit };
}
