import { z } from "zod";

import { apiFetch } from "./client";

export const auditEventSchema = z.object({
  id: z.number(),
  actorEmail: z.string(),
  action: z.string(),
  entityType: z.string(),
  entityId: z.string(),
  metadata: z.record(z.string(), z.unknown()).nullable(),
  ip: z.string().nullable(),
  createdAt: z.string(),
});

export const auditListSchema = z.object({
  items: z.array(auditEventSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
});

export type AuditEvent = z.infer<typeof auditEventSchema>;

export interface AuditFilters {
  entity?: string;
  actor?: string;
  action?: string;
  from?: string;
  to?: string;
}

export function listAuditEvents(filters: AuditFilters, limit = 25, offset = 0) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  for (const [key, value] of Object.entries(filters)) {
    if (value) params.set(key, value);
  }
  return apiFetch(`/api/v1/audit?${params.toString()}`, auditListSchema);
}
