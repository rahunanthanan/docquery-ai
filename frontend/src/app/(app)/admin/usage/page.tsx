"use client";

/** §3.1 /admin/usage: token & cost dashboard, grouped by day or user. */

import { useState } from "react";

import { UsageChart } from "@/components/admin/UsageChart";
import { EmptyState } from "@/components/EmptyState";
import { RoleGuard } from "@/components/RoleGuard";
import { SkeletonLoader } from "@/components/SkeletonLoader";
import { friendlyMessage } from "@/lib/errorMessages";
import type { UsageGroupBy } from "@/lib/api/admin";
import { useUsage } from "@/hooks/useAdmin";

function UsageDashboard() {
  const [groupBy, setGroupBy] = useState<UsageGroupBy>("day");
  const { data, isPending, isError, error, refetch } = useUsage(groupBy);

  return (
    <div>
      <div className="page-header">
        <h1>Usage &amp; cost</h1>
      </div>
      <div className="filter-tabs" role="tablist">
        {(["day", "user"] as const).map((option) => (
          <button
            key={option}
            role="tab"
            aria-selected={groupBy === option}
            className={`tab ${groupBy === option ? "tab-active" : ""}`}
            onClick={() => setGroupBy(option)}
          >
            By {option}
          </button>
        ))}
      </div>

      {isPending ? (
        <SkeletonLoader lines={5} />
      ) : isError ? (
        <EmptyState
          title="Couldn't load usage stats"
          detail={friendlyMessage(error)}
          action={
            <button className="button" onClick={() => void refetch()}>
              Try again
            </button>
          }
        />
      ) : data.rows.length === 0 ? (
        <EmptyState title="No usage yet" detail="Stats appear once questions are asked." />
      ) : (
        <>
          <div className="stat-tiles">
            <div className="stat-tile">
              <span className="stat-value">{data.totals.answers}</span>
              <span className="muted">Answers</span>
            </div>
            <div className="stat-tile">
              <span className="stat-value">
                {(data.totals.promptTokens + data.totals.completionTokens).toLocaleString()}
              </span>
              <span className="muted">Total tokens</span>
            </div>
            <div className="stat-tile">
              <span className="stat-value">${data.totals.costUsd.toFixed(4)}</span>
              <span className="muted">Cost (USD)</span>
            </div>
          </div>

          <UsageChart usage={data} />

          <table className="data-table usage-table">
            <thead>
              <tr>
                <th>{groupBy === "day" ? "Day" : "User"}</th>
                <th>Answers</th>
                <th>Prompt tokens</th>
                <th>Completion tokens</th>
                <th>Cost (USD)</th>
                <th>Avg latency</th>
              </tr>
            </thead>
            <tbody>
              {data.rows.map((row) => (
                <tr key={row.key}>
                  <td>{row.key}</td>
                  <td>{row.answers}</td>
                  <td>{row.promptTokens.toLocaleString()}</td>
                  <td>{row.completionTokens.toLocaleString()}</td>
                  <td>${row.costUsd.toFixed(4)}</td>
                  <td className="muted">{row.avgLatencyMs} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}

export default function AdminUsagePage() {
  return (
    <RoleGuard minRole="admin">
      <UsageDashboard />
    </RoleGuard>
  );
}
