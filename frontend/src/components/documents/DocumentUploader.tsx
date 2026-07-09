"use client";

/**
 * Drag-drop uploader (§3.2): client-side type/size validation before any
 * network call; upload progress shown as a pending state. The backend
 * re-validates everything (§6) — this is UX, not enforcement.
 */

import { useRef, useState, type DragEvent } from "react";

import { friendlyMessage } from "@/lib/errorMessages";
import { ACCEPTED_EXTENSIONS, validateFile } from "@/lib/uploadRules";
import { useUploadDocument } from "@/hooks/useDocuments";
import { useToast } from "@/providers/ToastProvider";

export function DocumentUploader() {
  const upload = useUploadDocument();
  const { toast } = useToast();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(0);

  async function handleFiles(files: FileList | null) {
    if (!files?.length) return;
    for (const file of Array.from(files)) {
      const problem = validateFile(file);
      if (problem !== null) {
        toast(problem);
        continue;
      }
      setUploading((n) => n + 1);
      try {
        await upload.mutateAsync(file);
        toast(`${file.name} uploaded — processing.`, "success");
      } catch (error) {
        toast(friendlyMessage(error));
      } finally {
        setUploading((n) => n - 1);
      }
    }
  }

  function onDrop(event: DragEvent) {
    event.preventDefault();
    setDragActive(false);
    void handleFiles(event.dataTransfer.files);
  }

  return (
    <div
      className={`dropzone ${dragActive ? "dropzone-active" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragActive(true);
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
      }}
      aria-label="Upload documents"
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={ACCEPTED_EXTENSIONS.join(",")}
        style={{ display: "none" }}
        onChange={(e) => {
          void handleFiles(e.target.files);
          e.target.value = "";
        }}
        aria-hidden
      />
      {uploading > 0 ? (
        <p className="muted">Uploading {uploading} file{uploading > 1 ? "s" : ""}…</p>
      ) : (
        <>
          <p>
            <strong>Drop files here</strong> or click to browse
          </p>
          <p className="muted">PDF, DOCX, TXT or Markdown · up to 20 MB each</p>
        </>
      )}
    </div>
  );
}
