import Link from "next/link";

import type { Citation } from "@/lib/api/qa";

/** §3.2: clicking a citation chip opens the source snippet + page number. */
export function CitationCard({ citation }: { citation: Citation }) {
  return (
    <div className="citation-card">
      <div className="citation-meta">
        <span className="chip chip-static">[{citation.marker}]</span>
        <span className="muted">
          Page {citation.page} · similarity {citation.similarity.toFixed(2)}
        </span>
        <Link href={`/documents/${citation.documentId}`} className="citation-link">
          Open document
        </Link>
      </div>
      <blockquote>{citation.snippet}</blockquote>
    </div>
  );
}
