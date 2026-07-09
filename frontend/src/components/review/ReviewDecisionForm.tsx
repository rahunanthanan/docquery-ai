"use client";

/**
 * §3.2 ReviewDecisionForm: the offered buttons come from allowedDecisions
 * (§6 — the UI renders only what the API allows); comment mandatory
 * (10–1,000 chars) for flag/reject.
 */

import { useState } from "react";

import type { AnswerStatus } from "@/lib/api/review";

const DECISION_LABELS: Partial<Record<AnswerStatus, string>> = {
  approved: "Approve",
  flagged: "Flag",
  rejected: "Reject",
};

interface Props {
  allowedDecisions: AnswerStatus[];
  pending: boolean;
  onSubmit: (decision: AnswerStatus, comment: string | null) => void;
}

export function ReviewDecisionForm({ allowedDecisions, pending, onSubmit }: Props) {
  const [decision, setDecision] = useState<AnswerStatus | null>(null);
  const [comment, setComment] = useState("");
  const [touched, setTouched] = useState(false);

  if (allowedDecisions.length === 0) {
    return (
      <p className="muted">
        This answer is in a terminal state — no further decisions are possible.
      </p>
    );
  }

  const trimmed = comment.trim();
  const commentRequired = decision !== null && decision !== "approved";
  const commentGiven = trimmed.length > 0;
  const commentError = (() => {
    if (commentRequired && !commentGiven) {
      return "A comment (10–1,000 characters) is required when flagging or rejecting.";
    }
    if (commentGiven && (trimmed.length < 10 || trimmed.length > 1000)) {
      return "Comment must be between 10 and 1,000 characters.";
    }
    return null;
  })();
  const valid = decision !== null && commentError === null;

  return (
    <form
      className="decision-form"
      onSubmit={(e) => {
        e.preventDefault();
        setTouched(true);
        if (!valid || pending || decision === null) return;
        onSubmit(decision, commentGiven ? trimmed : null);
      }}
    >
      <h2>Decision</h2>
      <div className="decision-buttons" role="radiogroup" aria-label="Decision">
        {allowedDecisions.map((option) => (
          <button
            key={option}
            type="button"
            role="radio"
            aria-checked={decision === option}
            className={`button decision-${option} ${decision === option ? "decision-selected" : "button-ghost"}`}
            onClick={() => setDecision(option)}
          >
            {DECISION_LABELS[option] ?? option}
          </button>
        ))}
      </div>
      <label className="field">
        <span>
          Comment{" "}
          {decision === "approved" || decision === null ? "(optional)" : "(required)"}
        </span>
        <textarea
          rows={3}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          onBlur={() => setTouched(true)}
          placeholder="Explain the decision for the audit trail…"
        />
        {touched && commentError ? (
          <span className="field-error" role="alert">
            {commentError}
          </span>
        ) : null}
      </label>
      <button className="button" type="submit" disabled={!valid || pending}>
        {pending ? "Submitting…" : "Submit decision"}
      </button>
    </form>
  );
}
