import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Proposal, ProposalDetail, Requirement, ComparisonResponse } from "@/types";

export function useProposals(projectId?: string) {
  return useQuery<Proposal[]>({
    queryKey: ["proposals", projectId],
    queryFn: async () => (await api.get("/proposals", { params: { project_id: projectId } })).data,
  });
}

export function useProposal(id?: string) {
  return useQuery<ProposalDetail>({
    queryKey: ["proposal", id],
    queryFn: async () => (await api.get(`/proposals/${id}`)).data,
    enabled: !!id,
    refetchInterval: (q) => {
      const data = q.state.data as ProposalDetail | undefined;
      if (!data) return false;
      if (data.status === "COMPLETED" || data.status === "FAILED") return false;
      return 2500;
    },
  });
}

export function useReanalyze() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (proposalId: string) => (await api.post(`/proposals/${proposalId}/reanalyze`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["proposals"] }),
  });
}

export function useRequirements(projectId?: string) {
  return useQuery<Requirement[]>({
    queryKey: ["requirements", projectId],
    queryFn: async () => (await api.get(`/projects/${projectId}/requirements`)).data,
    enabled: !!projectId,
  });
}

export function useCreateRequirement(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Requirement>) => (await api.post(`/projects/${projectId}/requirements`, data)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["requirements", projectId] }),
  });
}

export function useUpdateRequirement(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Requirement> }) =>
      (await api.patch(`/projects/${projectId}/requirements/${id}`, data)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["requirements", projectId] }),
  });
}

export function useDeleteRequirement(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => (await api.delete(`/projects/${projectId}/requirements/${id}`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["requirements", projectId] }),
  });
}

export function useProjectVendors(projectId?: string) {
  return useQuery<any[]>({
    queryKey: ["project-vendors", projectId],
    queryFn: async () => (await api.get(`/projects/${projectId}/vendors`)).data,
    enabled: !!projectId,
  });
}

export function useAddProjectVendor(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: { vendor_id: string }) =>
      (await api.post(`/projects/${projectId}/vendors`, data)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["project-vendors", projectId] }),
  });
}

export function useUpdateProjectVendor(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ pvId, data }: { pvId: string; data: any }) =>
      (await api.patch(`/projects/${projectId}/vendors/${pvId}`, data)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["project-vendors", projectId] }),
  });
}

export function useUploadProposal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ projectId, vendorId, title, file }: { projectId: string; vendorId: string; title?: string; file: File }) => {
      const form = new FormData();
      form.append("project_id", projectId);
      form.append("vendor_id", vendorId);
      if (title) form.append("title", title);
      form.append("file", file);
      return (await api.post("/proposals/upload", form, { headers: { "Content-Type": "multipart/form-data" } })).data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["proposals"] }),
  });
}

export function useComparison(projectId?: string) {
  return useQuery<ComparisonResponse>({
    queryKey: ["comparison", projectId],
    queryFn: async () => (await api.get(`/comparison/${projectId}`)).data,
    enabled: !!projectId,
  });
}

export function useDashboard() {
  return useQuery<any>({
    queryKey: ["dashboard"],
    queryFn: async () => (await api.get("/dashboard/summary")).data,
  });
}
