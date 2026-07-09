import type { Metadata } from "next";
import "./globals.css";

import { ErrorBoundary } from "@/components/ErrorBoundary";
import { AuthProvider } from "@/providers/AuthProvider";
import { QueryProvider } from "@/providers/QueryProvider";
import { ToastProvider } from "@/providers/ToastProvider";

export const metadata: Metadata = {
  title: "DocQuery AI",
  description:
    "Production-style RAG document Q&A assistant with human review and audit trail.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <ErrorBoundary>
          <QueryProvider>
            <ToastProvider>
              <AuthProvider>{children}</AuthProvider>
            </ToastProvider>
          </QueryProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
