"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest } from "@/lib/api";
import { homeFor } from "@/lib/session";
import type { Me } from "@/lib/types";
import { IconAlert, IconArrowRight, IconLock, IconMail } from "@/components/Icons";

type TokenResponse = { access_token: string };

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Already signed in? Skip the form.
  useEffect(() => {
    if (!localStorage.getItem("access_token")) return;
    apiRequest<Me>("/auth/me")
      .then((me) => router.replace(homeFor(me.role)))
      .catch(() => undefined);
  }, [router]);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await apiRequest<TokenResponse>("/auth/login", {
        method: "POST",
        authenticated: false,
        body: JSON.stringify({ email: email.trim(), password }),
      });
      localStorage.setItem("access_token", data.access_token);
      const me = await apiRequest<Me>("/auth/me");
      router.replace(homeFor(me.role));
    } catch (cause) {
      localStorage.removeItem("access_token");
      setError(cause instanceof Error ? cause.message : "Sign-in failed");
      setLoading(false);
    }
  }

  return (
    <main className="login-grid-background flex min-h-screen flex-col items-center justify-center px-6 py-10">
      <header className="mb-7 flex items-center justify-center gap-3">
        <span aria-hidden="true" className="inline-flex h-12 w-12 items-center justify-center rounded-[15px] bg-gradient-to-br from-[#5468d8] to-[#7660d4] shadow-soft">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3l8 3v6c0 4.5-3.2 7.8-8 9-4.8-1.2-8-4.5-8-9V6z" /><path d="M9 12l2 2 4-4" /></svg>
        </span>
        <h1 className="text-[34px] font-bold tracking-tight">RAGVault</h1>
      </header>

      <form onSubmit={handleLogin} className="panel w-full max-w-[420px] !bg-white p-8 sm:p-9" aria-labelledby="login-title">
          <div className="flex items-center justify-between gap-3">
            <h2 id="login-title" className="text-[22px] font-bold">Sign in</h2>
            <span className="chip-soft"><IconLock size={12} /> Secure</span>
          </div>

          <div className="mt-6 space-y-4">
            <div>
              <label htmlFor="email" className="label">Work email</label>
              <div className="relative">
                <IconMail size={17} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-ash" />
                <input
                  id="email"
                  className="field pl-10"
                  type="email"
                  autoComplete="username"
                  autoFocus
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                />
              </div>
            </div>
            <div>
              <label htmlFor="password" className="label">Password</label>
              <div className="relative">
                <IconLock size={17} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-ash" />
                <input
                  id="password"
                  className="field pl-10 pr-16"
                  type={show ? "text" : "password"}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <button type="button" onClick={() => setShow((v) => !v)} aria-pressed={show} className="absolute inset-y-0 right-1 my-1 rounded-lg px-2.5 text-[13px] font-semibold text-accent hover:bg-mist">
                  {show ? "Hide" : "Show"}
                </button>
              </div>
            </div>
          </div>

          {error && (
            <p role="alert" className="note note-error mb-0 mt-4">
              <IconAlert size={16} className="mt-0.5 shrink-0" /> <span>{error}</span>
            </p>
          )}

          <button type="submit" disabled={loading} className="btn-solid mt-6 w-full py-3">
            {loading ? "Signing in…" : <>Sign in <IconArrowRight size={16} /></>}
          </button>
      </form>
    </main>
  );
}
