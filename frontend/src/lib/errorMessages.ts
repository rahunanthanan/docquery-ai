/**
 * §9: one place mapping API error codes to friendly copy.
 * Unknown codes fall back to the server message (already human-readable).
 */

import { ApiError } from "./api/client";

const MESSAGES: Record<string, string> = {
  INVALID_CREDENTIALS: "That email and password combination doesn't match.",
  ACCOUNT_DISABLED: "This account has been disabled. Contact an administrator.",
  EMAIL_ALREADY_REGISTERED: "An account with this email already exists — try logging in.",
  NOT_AUTHENTICATED: "Your session has ended. Please log in again.",
  TOKEN_EXPIRED: "Your session has ended. Please log in again.",
  PERMISSION_DENIED: "You don't have permission to do that.",
  VALIDATION_FAILED: "Some fields need attention — check the highlighted values.",
  QUOTA_EXCEEDED: "You've reached your plan limit.",
  FILE_TOO_LARGE: "That file is over the 20 MB limit.",
  UNSUPPORTED_FILE_TYPE: "Only PDF, DOCX, plain text and Markdown files are supported.",
  FILE_CONTENT_MISMATCH: "That file's content doesn't match its type — is it renamed?",
  LLM_UNAVAILABLE: "The AI provider is temporarily unavailable. Your question was saved — try again shortly.",
  INTERNAL_ERROR: "Something went wrong on our side. Please try again.",
};

export function friendlyMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return MESSAGES[error.code] ?? error.message;
  }
  return "Something unexpected went wrong. Please try again.";
}
