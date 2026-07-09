"use client";

/**
 * §2 role hierarchy mirror: user < reviewer < admin.
 * Cosmetic only — the backend enforces every permission server-side.
 */

import type { ReactNode } from "react";

import { EmptyState } from "@/components/EmptyState";
import type { Role } from "@/lib/api/types";
import { useAuth } from "@/providers/AuthProvider";

const ROLE_LEVEL: Record<Role, number> = { user: 0, reviewer: 1, admin: 2 };

interface Props {
  minRole: Role;
  children: ReactNode;
  fallback?: ReactNode;
}

export function RoleGuard({ minRole, children, fallback }: Props) {
  const { user } = useAuth();
  if (user === null) return null; // app layout redirects anonymous users
  if (ROLE_LEVEL[user.role] < ROLE_LEVEL[minRole]) {
    return (
      fallback ?? (
        <EmptyState
          title="No access"
          detail={`This area needs the ${minRole} role.`}
        />
      )
    );
  }
  return <>{children}</>;
}
