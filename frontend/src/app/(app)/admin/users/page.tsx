"use client";

/** §3.1 /admin/users: role and active-status management. */

import { EmptyState } from "@/components/EmptyState";
import { RoleGuard } from "@/components/RoleGuard";
import { SkeletonLoader } from "@/components/SkeletonLoader";
import { friendlyMessage } from "@/lib/errorMessages";
import { formatDate } from "@/lib/format";
import type { Role } from "@/lib/api/types";
import { useAdminUsers, usePatchUser } from "@/hooks/useAdmin";
import { useAuth } from "@/providers/AuthProvider";
import { useToast } from "@/providers/ToastProvider";

const ROLES: Role[] = ["user", "reviewer", "admin"];

function UserManagement() {
  const { user: me } = useAuth();
  const { toast } = useToast();
  const { data, isPending, isError, error, refetch } = useAdminUsers();
  const patch = usePatchUser();

  function change(id: string, changes: { role?: Role; isActive?: boolean }) {
    patch.mutate(
      { id, ...changes },
      {
        onSuccess: (updated) =>
          toast(`${updated.email} updated.`, "success"),
        onError: (err) => toast(friendlyMessage(err)),
      },
    );
  }

  if (isPending) return <SkeletonLoader lines={4} />;
  if (isError) {
    return (
      <EmptyState
        title="Couldn't load users"
        detail={friendlyMessage(error)}
        action={
          <button className="button" onClick={() => void refetch()}>
            Try again
          </button>
        }
      />
    );
  }

  return (
    <div>
      <div className="page-header">
        <h1>Users</h1>
        <span className="muted">{data.total} accounts</span>
      </div>
      <table className="data-table">
        <thead>
          <tr>
            <th>Email</th>
            <th>Name</th>
            <th>Role</th>
            <th>Status</th>
            <th>Joined</th>
          </tr>
        </thead>
        <tbody>
          {data.items.map((account) => {
            const isSelf = account.id === me?.id;
            return (
              <tr key={account.id}>
                <td>
                  {account.email}
                  {isSelf ? <span className="muted"> (you)</span> : null}
                </td>
                <td>{account.fullName}</td>
                <td>
                  <select
                    value={account.role}
                    disabled={isSelf || patch.isPending}
                    aria-label={`Role for ${account.email}`}
                    onChange={(e) => change(account.id, { role: e.target.value as Role })}
                  >
                    {ROLES.map((role) => (
                      <option key={role} value={role}>
                        {role}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <button
                    className="button button-ghost"
                    disabled={isSelf || patch.isPending}
                    onClick={() => change(account.id, { isActive: !account.isActive })}
                  >
                    {account.isActive ? "Deactivate" : "Reactivate"}
                  </button>
                </td>
                <td className="muted">{formatDate(account.createdAt)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default function AdminUsersPage() {
  return (
    <RoleGuard minRole="admin">
      <UserManagement />
    </RoleGuard>
  );
}
