import { z } from "zod";

import { apiFetch } from "./client";
import { resolveMime } from "@/lib/uploadRules";

export const documentSchema = z.object({
  id: z.string(),
  filename: z.string(),
  mimeType: z.string(),
  sizeBytes: z.number(),
  status: z.enum(["uploaded", "processing", "ready", "failed"]),
  pageCount: z.number().nullable(),
  errorMessage: z.string().nullable(),
  createdAt: z.string(),
});

export const documentDetailSchema = documentSchema.extend({
  chunkCount: z.number(),
});

export const documentListSchema = z.object({
  items: z.array(documentSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
});

export type ApiDocument = z.infer<typeof documentSchema>;
export type ApiDocumentDetail = z.infer<typeof documentDetailSchema>;
export type DocumentList = z.infer<typeof documentListSchema>;
export type DocStatus = ApiDocument["status"];

export function listDocuments(limit: number, offset: number): Promise<DocumentList> {
  return apiFetch(`/api/v1/documents?limit=${limit}&offset=${offset}`, documentListSchema);
}

export function getDocument(id: string): Promise<ApiDocumentDetail> {
  return apiFetch(`/api/v1/documents/${id}`, documentDetailSchema);
}

export function uploadDocument(file: File): Promise<ApiDocument> {
  const formData = new FormData();
  // browsers often report an empty type for .md/.txt — resolve from extension
  formData.append("file", new File([file], file.name, { type: resolveMime(file) }));
  return apiFetch("/api/v1/documents", documentSchema, { method: "POST", formData });
}

export function deleteDocument(id: string): Promise<void> {
  return apiFetch(`/api/v1/documents/${id}`, z.void(), { method: "DELETE" });
}
