import { z } from "zod";

import { apiFetch } from "./client";
import { userSchema, type Role } from "./types";

export const adminUserSchema = userSchema.extend({ createdAt: z.string() });

export const adminUserListSchema = z.object({
  items: z.array(adminUserSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
});

export const usageRowSchema = z.object({
  key: z.string(),
  answers: z.number(),
  promptTokens: z.number(),
  completionTokens: z.number(),
  costUsd: z.number(),
  avgLatencyMs: z.number(),
});

export const usageSchema = z.object({
  groupBy: z.enum(["day", "user"]),
  rows: z.array(usageRowSchema),
  totals: z.object({
    answers: z.number(),
    promptTokens: z.number(),
    completionTokens: z.number(),
    costUsd: z.number(),
  }),
});

export type AdminUser = z.infer<typeof adminUserSchema>;
export type Usage = z.infer<typeof usageSchema>;
export type UsageGroupBy = Usage["groupBy"];

export function listUsers(limit = 100, offset = 0) {
  return apiFetch(`/api/v1/admin/users?limit=${limit}&offset=${offset}`, adminUserListSchema);
}

export function patchUser(
  id: string,
  changes: { role?: Role; isActive?: boolean },
): Promise<AdminUser> {
  return apiFetch(`/api/v1/admin/users/${id}`, adminUserSchema, {
    method: "PATCH",
    body: changes,
  });
}

export function getUsage(groupBy: UsageGroupBy): Promise<Usage> {
  return apiFetch(`/api/v1/admin/usage?groupBy=${groupBy}`, usageSchema);
}
