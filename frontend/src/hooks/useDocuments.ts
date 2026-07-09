"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  deleteDocument,
  getDocument,
  listDocuments,
  uploadDocument,
  type ApiDocument,
} from "@/lib/api/documents";

const PAGE_SIZE = 20;

const isSettling = (status: ApiDocument["status"]) =>
  status === "uploaded" || status === "processing";

export function useDocuments(page: number) {
  return useQuery({
    queryKey: ["documents", page],
    queryFn: () => listDocuments(PAGE_SIZE, page * PAGE_SIZE),
    // poll while ingestion is still moving documents through the lifecycle
    refetchInterval: (query) =>
      query.state.data?.items.some((d) => isSettling(d.status)) ? 2000 : false,
  });
}

export function useDocument(id: string) {
  return useQuery({
    queryKey: ["documents", "detail", id],
    queryFn: () => getDocument(id),
    refetchInterval: (query) =>
      query.state.data && isSettling(query.state.data.status) ? 2000 : false,
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: uploadDocument,
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });
}

export { PAGE_SIZE };
