"use client";

/**
 * Authenticated shell: redirects anonymous visitors to /login and shows
 * navigation filtered by the §2 role hierarchy.
 */

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { SkeletonLoader } from "@/components/SkeletonLoader";
import type { Role } from "@/lib/api/types";
import { useAuth } from "@/providers/AuthProvider";

const ROLE_LEVEL: Record<Role, number> = { user: 0, reviewer: 1, admin: 2 };

const NAV_ITEMS: { href: string; label: string; minRole: Role }[] = [
  { href: "/documents", label: "Documents", minRole: "user" },
  { href: "/chat", label: "Chat", minRole: "user" },
  { href: "/review", label: "Review", minRole: "reviewer" },
  { href: "/audit", label: "Audit", minRole: "reviewer" },
  { href: "/admin/users", label: "Users", minRole: "admin" },
  { href: "/admin/usage", label: "Usage", minRole: "admin" },
];

export default function AppLayout({ children }: { children: ReactNode }) {
  const { user, status, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (status === "anonymous") router.replace("/login");
  }, [status, router]);

  if (status !== "authenticated" || user === null) {
    return (
      <main className="center-card">
        <SkeletonLoader lines={3} />
      </main>
    );
  }

  const items = NAV_ITEMS.filter(
    (item) => ROLE_LEVEL[user.role] >= ROLE_LEVEL[item.minRole],
  );

  return (
    <div className="app-shell">
      <header className="app-nav">
        <Link href="/documents" className="brand">
          DocQuery AI
        </Link>
        <nav>
          {items.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={pathname.startsWith(item.href) ? "active" : ""}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="nav-user">
          <span className="muted">
            {user.fullName} · {user.role}
          </span>
          <button className="button button-ghost" onClick={() => void logout()}>
            Log out
          </button>
        </div>
      </header>
      <main className="app-main">{children}</main>
    </div>
  );
}
