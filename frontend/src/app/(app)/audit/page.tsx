"use client";

/** §3.1 /audit: filterable audit log table with CSV export (§8). */

import { useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { RoleGuard } from "@/components/RoleGuard";
import { SkeletonLoader } from "@/components/SkeletonLoader";
import { friendlyMessage } from "@/lib/errorMessages";
import { formatDate } from "@/lib/format";
import type { AuditEvent, AuditFilters } from "@/lib/api/audit";
import { AUDIT_PAGE_SIZE, useAuditLog } from "@/hooks/useAudit";

function exportCsv(items: AuditEvent[]) {
  const header = "id,createdAt,actorEmail,action,entityType,entityId,ip,metadata";
  const escape = (value: string) => `"${value.replaceAll('"', '""')}"`;
  const lines = items.map((e) =>
    [
      e.id,
      e.createdAt,
      escape(e.actorEmail),
      escape(e.action),
      escape(e.entityType),
      e.entityId,
      e.ip ?? "",
      escape(e.metadata ? JSON.stringify(e.metadata) : ""),
    ].join(","),
  );
  const blob = new Blob([[header, ...lines].join("\n")], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "audit-log.csv";
  link.click();
  URL.revokeObjectURL(url);
}

function AuditLog() {
  const [draft, setDraft] = useState<AuditFilters>({});
  const [filters, setFilters] = useState<AuditFilters>({});
  const [page, setPage] = useState(0);
  const { data, isPending, isError, error, refetch } = useAuditLog(filters, page);

  const pageCount = data ? Math.ceil(data.total / AUDIT_PAGE_SIZE) : 0;

  function applyFilters() {
    setPage(0);
    setFilters(draft);
  }

  return (
    <div>
      <div className="page-header">
        <h1>Audit log</h1>
        {data && data.items.length > 0 ? (
          <button className="button button-ghost" onClick={() => exportCsv(data.items)}>
            Export CSV
          </button>
        ) : null}
      </div>

      <div className="filter-bar">
        <input
          placeholder="Actor email"
          value={draft.actor ?? ""}
          onChange={(e) => setDraft((d) => ({ ...d, actor: e.target.value }))}
        />
        <input
          placeholder="Action (e.g. user.login)"
          value={draft.action ?? ""}
          onChange={(e) => setDraft((d) => ({ ...d, action: e.target.value }))}
        />
        <input
          placeholder="Entity (e.g. document)"
          value={draft.entity ?? ""}
          onChange={(e) => setDraft((d) => ({ ...d, entity: e.target.value }))}
        />
        <input
          type="date"
          aria-label="From date"
          value={draft.from ?? ""}
          onChange={(e) => setDraft((d) => ({ ...d, from: e.target.value }))}
        />
        <input
          type="date"
          aria-label="To date"
          value={draft.to ?? ""}
          onChange={(e) => setDraft((d) => ({ ...d, to: e.target.value }))}
        />
        <button className="button" onClick={applyFilters}>
          Filter
        </button>
      </div>

      {isPending ? (
        <SkeletonLoader lines={5} />
      ) : isError ? (
        <EmptyState
          title="Couldn't load the audit log"
          detail={friendlyMessage(error)}
          action={
            <button className="button" onClick={() => void refetch()}>
              Try again
            </button>
          }
        />
      ) : data.items.length === 0 ? (
        <EmptyState title="No events" detail="Nothing matches these filters." />
      ) : (
        <>
          <table className="data-table">
            <thead>
              <tr>
                <th>When</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Entity</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((event) => (
                <tr key={event.id}>
                  <td className="muted">{formatDate(event.createdAt)}</td>
                  <td>{event.actorEmail}</td>
                  <td>
                    <code className="audit-action">{event.action}</code>
                  </td>
                  <td className="muted">{event.entityType}</td>
                  <td className="muted audit-metadata">
                    {event.metadata ? JSON.stringify(event.metadata) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {pageCount > 1 ? (
            <div className="pagination">
              <button
                className="button button-ghost"
                disabled={page === 0}
                onClick={() => setPage((p) => p - 1)}
              >
                Previous
              </button>
              <span className="muted">
                Page {page + 1} of {pageCount} · {data.total} events
              </span>
              <button
                className="button button-ghost"
                disabled={page + 1 >= pageCount}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}

export default function AuditPage() {
  return (
    <RoleGuard minRole="reviewer">
      <AuditLog />
    </RoleGuard>
  );
}
