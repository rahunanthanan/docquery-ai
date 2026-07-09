"use client";

import { ComingSoon } from "@/components/ComingSoon";
import { RoleGuard } from "@/components/RoleGuard";

export default function AdminUsagePage() {
  return (
    <RoleGuard minRole="admin">
      <ComingSoon area="The usage dashboard" task={12} />
    </RoleGuard>
  );
}
