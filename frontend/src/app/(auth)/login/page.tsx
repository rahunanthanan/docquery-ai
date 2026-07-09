"use client";

import Link from "next/link";

import { AuthForm } from "@/components/auth/AuthForm";
import { loginFormSchema, type LoginForm } from "@/lib/schemas/auth";
import { useAuth } from "@/providers/AuthProvider";

export default function LoginPage() {
  const { login } = useAuth();
  return (
    <AuthForm<LoginForm>
      title="Log in"
      submitLabel="Log in"
      schema={loginFormSchema}
      fields={[
        { name: "email", label: "Email", type: "email", autoComplete: "email" },
        {
          name: "password",
          label: "Password",
          type: "password",
          autoComplete: "current-password",
        },
      ]}
      onSubmit={(values) => login(values.email, values.password)}
      footer={
        <>
          No account yet? <Link href="/register">Register</Link>
        </>
      }
    />
  );
}
