"use client";

import { ComingSoon } from "@/components/ComingSoon";
import { RoleGuard } from "@/components/RoleGuard";

export default function AdminUsersPage() {
  return (
    <RoleGuard minRole="admin">
      <ComingSoon area="User management" task={12} />
    </RoleGuard>
  );
}
