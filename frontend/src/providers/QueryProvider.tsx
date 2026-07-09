"use client";

/** §9: idempotent GETs retry twice; mutations never auto-retry. */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

export function QueryProvider({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { retry: 2, refetchOnWindowFocus: false, staleTime: 30_000 },
          mutations: { retry: 0 },
        },
      }),
  );
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
