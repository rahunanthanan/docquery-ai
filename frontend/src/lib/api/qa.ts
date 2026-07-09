import { z } from "zod";

import { apiFetch } from "./client";

export const citationSchema = z.object({
  marker: z.number(),
  documentId: z.string(),
  page: z.number(),
  snippet: z.string(),
  similarity: z.number(),
});

export const answerSchema = z.object({
  id: z.string(),
  content: z.string(),
  modelName: z.string(),
  promptTokens: z.number(),
  completionTokens: z.number(),
  costUsd: z.number(),
  latencyMs: z.number(),
  reviewStatus: z.enum(["pending_review", "approved", "flagged", "rejected"]),
  createdAt: z.string(),
  citations: z.array(citationSchema),
});

export const questionSchema = z.object({
  id: z.string(),
  text: z.string(),
  createdAt: z.string(),
});

export const qaItemSchema = z.object({
  question: questionSchema,
  answer: answerSchema.nullable(),
});

export const conversationSchema = z.object({
  id: z.string(),
  title: z.string(),
  createdAt: z.string(),
});

export const conversationListSchema = z.object({
  items: z.array(conversationSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
});

export const conversationDetailSchema = z.object({
  id: z.string(),
  title: z.string(),
  createdAt: z.string(),
  items: z.array(qaItemSchema),
});

export const askResponseSchema = z.object({
  question: questionSchema,
  answer: answerSchema.nullable(),
  notice: z.string().nullable(),
});

export type Citation = z.infer<typeof citationSchema>;
export type Answer = z.infer<typeof answerSchema>;
export type QAItem = z.infer<typeof qaItemSchema>;
export type Conversation = z.infer<typeof conversationSchema>;
export type ConversationDetail = z.infer<typeof conversationDetailSchema>;
export type AskResponse = z.infer<typeof askResponseSchema>;

export function listConversations(limit = 50, offset = 0) {
  return apiFetch(
    `/api/v1/conversations?limit=${limit}&offset=${offset}`,
    conversationListSchema,
  );
}

export function createConversation(title?: string): Promise<Conversation> {
  return apiFetch("/api/v1/conversations", conversationSchema, {
    method: "POST",
    body: title ? { title } : {},
  });
}

export function getConversation(id: string): Promise<ConversationDetail> {
  return apiFetch(`/api/v1/conversations/${id}`, conversationDetailSchema);
}

export function askQuestion(conversationId: string, text: string): Promise<AskResponse> {
  return apiFetch(
    `/api/v1/conversations/${conversationId}/questions`,
    askResponseSchema,
    { method: "POST", body: { text } },
  );
}
