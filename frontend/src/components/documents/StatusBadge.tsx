import type { DocStatus } from "@/lib/api/documents";

const LABELS: Record<DocStatus, string> = {
  uploaded: "Uploaded",
  processing: "Processing…",
  ready: "Ready",
  failed: "Failed",
};

export function StatusBadge({ status }: { status: DocStatus }) {
  return <span className={`badge badge-${status}`}>{LABELS[status]}</span>;
}
