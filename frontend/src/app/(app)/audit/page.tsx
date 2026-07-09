"use client";

import { ComingSoon } from "@/components/ComingSoon";
import { RoleGuard } from "@/components/RoleGuard";

export default function AuditPage() {
  return (
    <RoleGuard minRole="reviewer">
      <ComingSoon area="The audit log" task={12} />
    </RoleGuard>
  );
}
