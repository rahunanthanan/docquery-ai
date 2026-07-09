"use client";

/**
 * Shared login/register form: zod-validated fields with inline errors,
 * submit disabled while invalid or pending (§6, §9).
 */

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import type { ZodType } from "zod";

import { friendlyMessage } from "@/lib/errorMessages";
import { useToast } from "@/providers/ToastProvider";

export interface FieldSpec {
  name: string;
  label: string;
  type: "text" | "email" | "password";
  autoComplete?: string;
}

interface Props<T extends Record<string, string>> {
  title: string;
  submitLabel: string;
  fields: FieldSpec[];
  schema: ZodType<T>;
  onSubmit: (values: T) => Promise<void>;
  footer: React.ReactNode;
}

export function AuthForm<T extends Record<string, string>>({
  title,
  submitLabel,
  fields,
  schema,
  onSubmit,
  footer,
}: Props<T>) {
  const router = useRouter();
  const { toast } = useToast();
  const [values, setValues] = useState<Record<string, string>>(
    Object.fromEntries(fields.map((f) => [f.name, ""])),
  );
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [pending, setPending] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const parsed = schema.safeParse(values);
  const fieldErrors: Record<string, string> = {};
  if (!parsed.success) {
    for (const issue of parsed.error.issues) {
      const key = String(issue.path[0]);
      if (!(key in fieldErrors)) fieldErrors[key] = issue.message;
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!parsed.success || pending) return;
    setPending(true);
    setFormError(null);
    try {
      await onSubmit(parsed.data);
      router.push("/documents");
    } catch (error) {
      const message = friendlyMessage(error);
      setFormError(message);
      toast(message);
      setPending(false);
    }
  }

  return (
    <main className="center-card">
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <h1>{title}</h1>
        {fields.map((field) => (
          <label key={field.name} className="field">
            <span>{field.label}</span>
            <input
              name={field.name}
              type={field.type}
              autoComplete={field.autoComplete}
              value={values[field.name]}
              onChange={(e) =>
                setValues((v) => ({ ...v, [field.name]: e.target.value }))
              }
              onBlur={() => setTouched((t) => ({ ...t, [field.name]: true }))}
            />
            {touched[field.name] && fieldErrors[field.name] ? (
              <span className="field-error" role="alert">
                {fieldErrors[field.name]}
              </span>
            ) : null}
          </label>
        ))}
        {formError ? (
          <p className="form-error" role="alert">
            {formError}
          </p>
        ) : null}
        <button
          className="button"
          type="submit"
          disabled={!parsed.success || pending}
        >
          {pending ? "Please wait…" : submitLabel}
        </button>
        <div className="muted auth-footer">{footer}</div>
      </form>
    </main>
  );
}
