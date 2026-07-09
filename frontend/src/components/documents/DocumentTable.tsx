"use client";

import Link from "next/link";

import { StatusBadge } from "@/components/documents/StatusBadge";
import type { ApiDocument } from "@/lib/api/documents";
import { formatBytes, formatDate } from "@/lib/format";

interface Props {
  documents: ApiDocument[];
  onDelete: (id: string) => void;
  deletingId?: string | null;
}

export function DocumentTable({ documents, onDelete, deletingId }: Props) {
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Status</th>
          <th>Size</th>
          <th>Uploaded</th>
          <th aria-label="Actions" />
        </tr>
      </thead>
      <tbody>
        {documents.map((document) => (
          <tr key={document.id}>
            <td>
              <Link href={`/documents/${document.id}`}>{document.filename}</Link>
            </td>
            <td>
              <StatusBadge status={document.status} />
            </td>
            <td>{formatBytes(document.sizeBytes)}</td>
            <td className="muted">{formatDate(document.createdAt)}</td>
            <td>
              <button
                className="button button-ghost"
                onClick={() => onDelete(document.id)}
                disabled={deletingId === document.id}
              >
                {deletingId === document.id ? "Deleting…" : "Delete"}
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
