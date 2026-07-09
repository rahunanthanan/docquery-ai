"use client";

/** §3.1 /review: queue with pending / flagged / all filters. */

import Link from "next/link";
import { useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { RoleGuard } from "@/components/RoleGuard";
import { SkeletonLoader } from "@/components/SkeletonLoader";
import { friendlyMessage } from "@/lib/errorMessages";
import { formatDate } from "@/lib/format";
import type { QueueFilter } from "@/lib/api/review";
import { useReviewQueue } from "@/hooks/useReview";

const FILTERS: { value: QueueFilter; label: string }[] = [
  { value: "pending_review", label: "Pending" },
  { value: "flagged", label: "Flagged" },
  { value: "all", label: "All" },
];

const STATUS_LABELS: Record<string, string> = {
  pending_review: "Pending review",
  approved: "Approved",
  flagged: "Flagged",
  rejected: "Rejected",
};

function Queue() {
  const [filter, setFilter] = useState<QueueFilter>("pending_review");
  const { data, isPending, isError, error, refetch } = useReviewQueue(filter);

  return (
    <div>
      <div className="page-header">
        <h1>Review queue</h1>
      </div>
      <div className="filter-tabs" role="tablist">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            role="tab"
            aria-selected={filter === f.value}
            className={`tab ${filter === f.value ? "tab-active" : ""}`}
            onClick={() => setFilter(f.value)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {isPending ? (
        <SkeletonLoader lines={4} />
      ) : isError ? (
        <EmptyState
          title="Couldn't load the queue"
          detail={friendlyMessage(error)}
          action={
            <button className="button" onClick={() => void refetch()}>
              Try again
            </button>
          }
        />
      ) : data.items.length === 0 ? (
        <EmptyState title="Queue is clear" detail="No answers match this filter." />
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Question</th>
              <th>Asked by</th>
              <th>Status</th>
              <th>Created</th>
              <th aria-label="Actions" />
            </tr>
          </thead>
          <tbody>
            {data.items.map((item) => (
              <tr key={item.answerId}>
                <td>
                  <Link href={`/review/${item.answerId}`}>{item.questionText}</Link>
                </td>
                <td className="muted">{item.askerEmail}</td>
                <td>
                  <span className={`badge answer-badge-${item.reviewStatus}`}>
                    {STATUS_LABELS[item.reviewStatus]}
                  </span>
                </td>
                <td className="muted">{formatDate(item.createdAt)}</td>
                <td>
                  <Link className="button button-ghost" href={`/review/${item.answerId}`}>
                    Review
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default function ReviewPage() {
  return (
    <RoleGuard minRole="reviewer">
      <Queue />
    </RoleGuard>
  );
}
