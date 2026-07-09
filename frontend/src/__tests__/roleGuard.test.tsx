/** §2 role hierarchy mirrored client-side (cosmetic; backend enforces). */

import { render, screen } from "@testing-library/react";

import { RoleGuard } from "@/components/RoleGuard";
import type { ApiUser } from "@/lib/api/types";

const mockUseAuth = jest.fn();
jest.mock("@/providers/AuthProvider", () => ({
  useAuth: () => mockUseAuth(),
}));

function userWithRole(role: ApiUser["role"]): ApiUser {
  return { id: "u1", email: "x@y.z", fullName: "X", role, isActive: true };
}

test.each([
  ["user", "reviewer", false],
  ["user", "admin", false],
  ["reviewer", "reviewer", true],
  ["reviewer", "admin", false],
  ["admin", "reviewer", true],
  ["admin", "admin", true],
] as const)("role %s vs minRole %s → allowed=%s", (role, minRole, allowed) => {
  mockUseAuth.mockReturnValue({ user: userWithRole(role) });
  render(
    <RoleGuard minRole={minRole}>
      <p>secret content</p>
    </RoleGuard>,
  );
  if (allowed) {
    expect(screen.getByText("secret content")).toBeInTheDocument();
  } else {
    expect(screen.queryByText("secret content")).not.toBeInTheDocument();
    expect(screen.getByText("No access")).toBeInTheDocument();
  }
});

test("renders nothing while there is no user", () => {
  mockUseAuth.mockReturnValue({ user: null });
  const { container } = render(
    <RoleGuard minRole="user">
      <p>secret content</p>
    </RoleGuard>,
  );
  expect(container).toBeEmptyDOMElement();
});
