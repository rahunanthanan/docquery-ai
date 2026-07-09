"use client";

/** §3.1 /documents/[id]: metadata, chunk count, processing status. */

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { EmptyState } from "@/components/EmptyState";
import { SkeletonLoader } from "@/components/SkeletonLoader";
import { StatusBadge } from "@/components/documents/StatusBadge";
import { friendlyMessage } from "@/lib/errorMessages";
import { formatBytes, formatDate } from "@/lib/format";
import { useDeleteDocument, useDocument } from "@/hooks/useDocuments";
import { useToast } from "@/providers/ToastProvider";

export default function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { toast } = useToast();
  const { data, isPending, isError, error } = useDocument(id);
  const deleteDocument = useDeleteDocument();

  if (isPending) return <SkeletonLoader lines={5} />;
  if (isError) {
    return (
      <EmptyState
        title="Couldn't load this document"
        detail={friendlyMessage(error)}
        action={
          <Link className="button" href="/documents">
            Back to documents
          </Link>
        }
      />
    );
  }

  function handleDelete() {
    if (!window.confirm("Delete this document? Its chunks leave search immediately.")) return;
    deleteDocument.mutate(id, {
      onSuccess: () => {
        toast("Document deleted.", "success");
        router.push("/documents");
      },
      onError: (err) => toast(friendlyMessage(err)),
    });
  }

  return (
    <div>
      <p>
        <Link href="/documents" className="muted">
          ← Documents
        </Link>
      </p>
      <div className="page-header">
        <h1>{data.filename}</h1>
        <StatusBadge status={data.status} />
      </div>

      {data.status === "failed" && data.errorMessage ? (
        <p className="form-error">{data.errorMessage}</p>
      ) : null}

      <dl className="detail-grid">
        <dt>Type</dt>
        <dd>{data.mimeType}</dd>
        <dt>Size</dt>
        <dd>{formatBytes(data.sizeBytes)}</dd>
        <dt>Pages</dt>
        <dd>{data.pageCount ?? "—"}</dd>
        <dt>Chunks indexed</dt>
        <dd>{data.chunkCount}</dd>
        <dt>Uploaded</dt>
        <dd>{formatDate(data.createdAt)}</dd>
      </dl>

      <button
        className="button button-ghost"
        onClick={handleDelete}
        disabled={deleteDocument.isPending}
      >
        {deleteDocument.isPending ? "Deleting…" : "Delete document"}
      </button>
    </div>
  );
}
