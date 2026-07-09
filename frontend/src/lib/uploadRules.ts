/** §6 mirror: client-side upload validation (UX only — backend re-checks). */

export const MAX_UPLOAD_BYTES = 20 * 1024 * 1024;

const EXTENSION_MIME: Record<string, string> = {
  pdf: "application/pdf",
  docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  txt: "text/plain",
  md: "text/markdown",
};

export const ACCEPTED_EXTENSIONS = Object.keys(EXTENSION_MIME).map((e) => `.${e}`);

function extensionOf(name: string): string {
  return name.includes(".") ? name.split(".").pop()!.toLowerCase() : "";
}

export function resolveMime(file: File): string {
  return EXTENSION_MIME[extensionOf(file.name)] ?? file.type;
}

/** Returns an error message, or null when the file is acceptable. */
export function validateFile(file: File): string | null {
  if (!(extensionOf(file.name) in EXTENSION_MIME)) {
    return `${file.name}: only PDF, DOCX, TXT and Markdown files are supported.`;
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    return `${file.name}: files must be 20 MB or smaller.`;
  }
  if (file.size === 0) {
    return `${file.name}: this file is empty.`;
  }
  return null;
}
