"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getQueue,
  getReviewDetail,
  submitDecision,
  type AnswerStatus,
  type QueueFilter,
} from "@/lib/api/review";

export function useReviewQueue(filter: QueueFilter) {
  return useQuery({
    queryKey: ["review", "queue", filter],
    queryFn: () => getQueue(filter),
  });
}

export function useReviewDetail(answerId: string) {
  return useQuery({
    queryKey: ["review", "detail", answerId],
    queryFn: () => getReviewDetail(answerId),
  });
}

export function useSubmitDecision(answerId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { decision: AnswerStatus; comment: string | null }) =>
      submitDecision(answerId, input.decision, input.comment),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["review"] });
      // the asker's conversation view changes too (§7 rejected masking)
      void queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}
