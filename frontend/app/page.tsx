"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiRequest } from "@/lib/api";
import { homeFor } from "@/lib/session";
import type { Me } from "@/lib/types";

// Send people to the right place: sign-in if there's no valid session, otherwise their home page by role.
export default function Home() {
  const router = useRouter();
  useEffect(() => {
    if (!localStorage.getItem("access_token")) {
      router.replace("/login");
      return;
    }
    apiRequest<Me>("/auth/me")
      .then((me) => router.replace(homeFor(me.role)))
      .catch(() => router.replace("/login"));
  }, [router]);
  return (
    <main className="flex min-h-screen items-center justify-center" aria-busy="true">
      <p className="text-sm text-ash">Loading…</p>
    </main>
  );
}
