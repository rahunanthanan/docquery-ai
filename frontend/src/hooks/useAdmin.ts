"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getUsage, listUsers, patchUser, type UsageGroupBy } from "@/lib/api/admin";
import type { Role } from "@/lib/api/types";

export function useAdminUsers() {
  return useQuery({ queryKey: ["admin", "users"], queryFn: () => listUsers() });
}

export function usePatchUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { id: string; role?: Role; isActive?: boolean }) =>
      patchUser(input.id, { role: input.role, isActive: input.isActive }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin", "users"] }),
  });
}

export function useUsage(groupBy: UsageGroupBy) {
  return useQuery({
    queryKey: ["admin", "usage", groupBy],
    queryFn: () => getUsage(groupBy),
  });
}
