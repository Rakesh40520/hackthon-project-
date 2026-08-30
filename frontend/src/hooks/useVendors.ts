import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Vendor } from "@/types";

export function useVendors(q?: string) {
  return useQuery<Vendor[]>({
    queryKey: ["vendors", q],
    queryFn: async () => (await api.get("/vendors", { params: { q } })).data,
  });
}

export function useCreateVendor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Vendor>) => (await api.post("/vendors", data)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["vendors"] }),
  });
}

export function useUpdateVendor(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Vendor>) => (await api.patch(`/vendors/${id}`, data)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["vendors"] }),
  });
}

export function useDeleteVendor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => (await api.delete(`/vendors/${id}`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["vendors"] }),
  });
}
