"use client";

/** §3.1 /documents: upload, list, status, delete — with §9 loading/empty/error states. */

import { useState } from "react";

import { DocumentTable } from "@/components/documents/DocumentTable";
import { DocumentUploader } from "@/components/documents/DocumentUploader";
import { EmptyState } from "@/components/EmptyState";
import { SkeletonLoader } from "@/components/SkeletonLoader";
import { friendlyMessage } from "@/lib/errorMessages";
import { PAGE_SIZE, useDeleteDocument, useDocuments } from "@/hooks/useDocuments";
import { useToast } from "@/providers/ToastProvider";

export default function DocumentsPage() {
  const [page, setPage] = useState(0);
  const { data, isPending, isError, error, refetch } = useDocuments(page);
  const deleteDocument = useDeleteDocument();
  const { toast } = useToast();

  function handleDelete(id: string) {
    if (!window.confirm("Delete this document? Its chunks leave search immediately.")) return;
    deleteDocument.mutate(id, {
      onSuccess: () => toast("Document deleted.", "success"),
      onError: (err) => toast(friendlyMessage(err)),
    });
  }

  const pageCount = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  return (
    <div>
      <div className="page-header">
        <h1>Documents</h1>
      </div>
      <DocumentUploader />

      {isPending ? (
        <SkeletonLoader lines={4} />
      ) : isError ? (
        <EmptyState
          title="Couldn't load your documents"
          detail={friendlyMessage(error)}
          action={
            <button className="button" onClick={() => void refetch()}>
              Try again
            </button>
          }
        />
      ) : data.items.length === 0 ? (
        <EmptyState
          title="No documents yet"
          detail="Upload a PDF, DOCX, text or Markdown file to start asking questions."
        />
      ) : (
        <>
          <DocumentTable
            documents={data.items}
            onDelete={handleDelete}
            deletingId={deleteDocument.isPending ? deleteDocument.variables : null}
          />
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
                Page {page + 1} of {pageCount}
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
