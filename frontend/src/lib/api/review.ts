import { z } from "zod";

import { apiFetch } from "./client";
import { citationSchema } from "./qa";

export const answerStatusSchema = z.enum([
  "pending_review",
  "approved",
  "flagged",
  "rejected",
]);

export const queueItemSchema = z.object({
  answerId: z.string(),
  questionId: z.string(),
  questionText: z.string(),
  content: z.string(),
  modelName: z.string(),
  reviewStatus: answerStatusSchema,
  askerEmail: z.string(),
  createdAt: z.string(),
  allowedDecisions: z.array(answerStatusSchema),
});

export const queueSchema = z.object({
  items: z.array(queueItemSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
});

export const reviewDetailSchema = queueItemSchema.extend({
  citations: z.array(citationSchema),
});

export const decisionOutSchema = z.object({
  id: z.string(),
  answerId: z.string(),
  decision: answerStatusSchema,
  comment: z.string().nullable(),
  reviewStatus: answerStatusSchema,
  createdAt: z.string(),
});

export type AnswerStatus = z.infer<typeof answerStatusSchema>;
export type QueueItem = z.infer<typeof queueItemSchema>;
export type ReviewDetail = z.infer<typeof reviewDetailSchema>;

export type QueueFilter = "pending_review" | "flagged" | "all";

export function getQueue(filter: QueueFilter, limit = 50, offset = 0) {
  const status = filter === "all" ? "" : `&status=${filter}`;
  return apiFetch(`/api/v1/review/queue?limit=${limit}&offset=${offset}${status}`, queueSchema);
}

export function getReviewDetail(answerId: string): Promise<ReviewDetail> {
  return apiFetch(`/api/v1/review/${answerId}`, reviewDetailSchema);
}

export function submitDecision(
  answerId: string,
  decision: AnswerStatus,
  comment: string | null,
) {
  return apiFetch(`/api/v1/review/${answerId}/decision`, decisionOutSchema, {
    method: "POST",
    body: { decision, comment },
  });
}
