"use client";

import Link from "next/link";

import { AuthForm } from "@/components/auth/AuthForm";
import { registerFormSchema, type RegisterForm } from "@/lib/schemas/auth";
import { useAuth } from "@/providers/AuthProvider";

export default function RegisterPage() {
  const { register } = useAuth();
  return (
    <AuthForm<RegisterForm>
      title="Create account"
      submitLabel="Register"
      schema={registerFormSchema}
      fields={[
        { name: "fullName", label: "Full name", type: "text", autoComplete: "name" },
        { name: "email", label: "Email", type: "email", autoComplete: "email" },
        {
          name: "password",
          label: "Password (10+ chars, letter + number)",
          type: "password",
          autoComplete: "new-password",
        },
      ]}
      onSubmit={(values) => register(values.email, values.password, values.fullName)}
      footer={
        <>
          Already registered? <Link href="/login">Log in</Link>
        </>
      }
    />
  );
}
