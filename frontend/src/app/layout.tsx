import type { Metadata } from "next";
import "./globals.css";

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
      <body>{children}</body>
    </html>
  );
}
