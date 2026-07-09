"use client";

import { ComingSoon } from "@/components/ComingSoon";
import { RoleGuard } from "@/components/RoleGuard";

export default function ReviewPage() {
  return (
    <RoleGuard minRole="reviewer">
      <ComingSoon area="The review queue" task={12} />
    </RoleGuard>
  );
}
