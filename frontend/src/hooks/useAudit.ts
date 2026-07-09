"use client";

import { useQuery } from "@tanstack/react-query";

import { listAuditEvents, type AuditFilters } from "@/lib/api/audit";

export const AUDIT_PAGE_SIZE = 25;

export function useAuditLog(filters: AuditFilters, page: number) {
  return useQuery({
    queryKey: ["audit", filters, page],
    queryFn: () => listAuditEvents(filters, AUDIT_PAGE_SIZE, page * AUDIT_PAGE_SIZE),
  });
}
