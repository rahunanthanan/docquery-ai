"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { SkeletonLoader } from "@/components/SkeletonLoader";
import { useAuth } from "@/providers/AuthProvider";

export default function Home() {
  const { status } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (status === "authenticated") router.replace("/documents");
    if (status === "anonymous") router.replace("/login");
  }, [status, router]);

  return (
    <main className="center-card">
      <SkeletonLoader lines={2} />
    </main>
  );
}
