"use client";

import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, apiRequest } from "./api";
import type { Me } from "./types";

type Session = {
  me: Me;
  /** Replace the cached profile (e.g. after the person renames themselves). */
  updateMe: (me: Me) => void;
  logout: () => void;
  /** Turns any thrown value into a message; sends the user to /login on 401. */
  handleError: (cause: unknown) => string;
};

const SessionContext = createContext<Session | null>(null);

export function useSession(): Session {
  const value = useContext(SessionContext);
  if (!value) throw new Error("useSession must be used inside <SessionGate>");
  return value;
}

export function homeFor(role: string): string {
  return role === "Admin" ? "/admin" : "/workspace";
}

export function SessionGate({ area, children }: { area: "admin" | "workspace"; children: ReactNode }) {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [failure, setFailure] = useState("");

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    router.replace("/login");
  }, [router]);

  useEffect(() => {
    let cancelled = false;
    apiRequest<Me>("/auth/me")
      .then((user) => {
        if (cancelled) return;
        const isAdmin = user.role === "Admin";
        if (area === "admin" && !isAdmin) router.replace(homeFor(user.role));
        else if (area === "workspace" && isAdmin) router.replace(homeFor(user.role));
        else setMe(user);
      })
      .catch((cause) => {
        if (cancelled) return;
        if (cause instanceof ApiError && cause.status === 401) router.replace("/login");
        else setFailure(cause instanceof Error ? cause.message : "Couldn't load your account");
      });
    return () => {
      cancelled = true;
    };
  }, [area, router]);

  const handleError = useCallback(
    (cause: unknown) => {
      if (cause instanceof ApiError && cause.status === 401) {
        router.replace("/login");
        return "Your session ended. Sign in again.";
      }
      return cause instanceof Error ? cause.message : "Something went wrong";
    },
    [router],
  );

  const value = useMemo(() => (me ? { me, updateMe: setMe as (me: Me) => void, logout, handleError } : null), [me, logout, handleError]);

  if (failure) {
    return (
      <main className="flex min-h-screen items-center justify-center px-6">
        <div role="alert" className="panel max-w-md p-6 text-sm">
          <p className="font-semibold">Can't load RAGVault</p>
          <p className="mt-1 text-graphite">{failure}</p>
          <button className="btn-solid mt-4" onClick={() => window.location.reload()}>Try again</button>
        </div>
      </main>
    );
  }
  if (!value) {
    return (
      <main className="flex min-h-screen items-center justify-center" aria-busy="true">
        <p className="text-sm text-ash">Loading…</p>
      </main>
    );
  }
  // Remount the tree for a different signed-in user without a hard refresh.
  return <SessionContext.Provider value={value} key={value.me.id}>{children}</SessionContext.Provider>;
}
