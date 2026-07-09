"use client";

import { useState, type ReactNode } from "react";

import { CitationCard } from "@/components/chat/CitationCard";
import type { Answer } from "@/lib/api/qa";

export function QuestionBubble({ text }: { text: string }) {
  return <div className="bubble bubble-question">{text}</div>;
}

export function NoticeBubble({ children }: { children: ReactNode }) {
  return <div className="bubble bubble-notice muted">{children}</div>;
}

const STATUS_LABELS: Record<Answer["reviewStatus"], string> = {
  pending_review: "Pending review",
  approved: "Approved",
  flagged: "Flagged",
  rejected: "Rejected",
};

/** Answer text with numbered citation chips (§3.2). */
export function AnswerBubble({ answer }: { answer: Answer }) {
  const [openMarker, setOpenMarker] = useState<number | null>(null);
  const byMarker = new Map(answer.citations.map((c) => [c.marker, c]));
  const open = openMarker !== null ? byMarker.get(openMarker) : undefined;

  const parts: ReactNode[] = [];
  const pattern = /\[(\d+)\]/g;
  let cursor = 0;
  let match: RegExpExecArray | null;
  while ((match = pattern.exec(answer.content)) !== null) {
    const marker = Number(match[1]);
    if (match.index > cursor) parts.push(answer.content.slice(cursor, match.index));
    if (byMarker.has(marker)) {
      parts.push(
        <button
          key={`${match.index}-${marker}`}
          className={`chip ${openMarker === marker ? "chip-open" : ""}`}
          onClick={() => setOpenMarker(openMarker === marker ? null : marker)}
          aria-label={`Citation ${marker}`}
        >
          [{marker}]
        </button>,
      );
    } else {
      parts.push(match[0]); // marker without a stored citation stays plain text
    }
    cursor = match.index + match[0].length;
  }
  if (cursor < answer.content.length) parts.push(answer.content.slice(cursor));

  return (
    <div className="bubble bubble-answer">
      <p className="answer-content">{parts}</p>
      {open ? <CitationCard citation={open} /> : null}
      <div className="answer-meta muted">
        <span className={`badge answer-badge-${answer.reviewStatus}`}>
          {STATUS_LABELS[answer.reviewStatus]}
        </span>
        <span>{answer.modelName}</span>
      </div>
    </div>
  );
}
