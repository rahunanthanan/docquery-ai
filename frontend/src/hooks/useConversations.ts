"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  askQuestion,
  createConversation,
  getConversation,
  listConversations,
} from "@/lib/api/qa";

export function useConversations() {
  return useQuery({
    queryKey: ["conversations"],
    queryFn: () => listConversations(),
  });
}

export function useConversation(id: string) {
  return useQuery({
    queryKey: ["conversations", "detail", id],
    queryFn: () => getConversation(id),
  });
}

export function useCreateConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (title?: string) => createConversation(title),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["conversations"] }),
  });
}

export function useAskQuestion(conversationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (text: string) => askQuestion(conversationId, text),
    // settled, not just success: a failed LLM call still saved the question
    // (§9), so the refetched history must show it
    onSettled: () =>
      void queryClient.invalidateQueries({
        queryKey: ["conversations", "detail", conversationId],
      }),
  });
}
