"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { ArrowRight, Eye, EyeOff, LockKeyhole, Mail } from "lucide-react";
import { createClient } from "@/lib/supabase/client";

type AuthMode = "login" | "sign-up";

export function AuthForm({ mode }: { mode: AuthMode }) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const isSignup = mode === "sign-up";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setMessage("");
    setError("");
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "").trim();
    const password = String(form.get("password") ?? "");
    const supabase = createClient();

    if (isSignup) {
      const { data, error: authError } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: process.env.NEXT_PUBLIC_DEV_SUPABASE_REDIRECT_URL ?? `${window.location.origin}/auth/callback`,
          data: { display_name: String(form.get("name") ?? "").trim() },
        },
      });
      if (authError) {
        const detail = authError.message.toLowerCase();
        setError(detail.includes("password") ? "Choose a stronger password and try again." : detail.includes("rate") ? "Too many attempts. Wait a little while before trying again." : "We couldn’t create your account. Check the details and try again.");
      } else if (data.session) {
        router.push("/dashboard");
        router.refresh();
      } else {
        setMessage("Check your inbox for a confirmation link. You can sign in after confirming your email.");
      }
    } else {
      const { error: authError } = await supabase.auth.signInWithPassword({ email, password });
      if (authError) {
        setError(authError.message.toLowerCase().includes("not confirmed")
          ? "Confirm your email from the link we sent before signing in."
            : authError.message.toLowerCase().includes("invalid login credentials")
            ? "Invalid email or password."
            : authError.message.toLowerCase().includes("rate")
              ? "Too many attempts. Wait a little while before trying again."
              : "We couldn’t sign you in right now. Please try again.");
      } else {
        router.push("/dashboard");
        router.refresh();
      }
    }
    setPending(false);
  }

  return (
    <main className="auth-page">
      <div className="auth-aside" aria-hidden="true">
        <div className="auth-aside-top"><div className="brand-mark">W</div><span>WorkPulse</span></div>
        <div className="auth-aside-content">
          <span className="eyebrow eyebrow-light">A better rhythm for growth</span>
          <h2>Performance is a conversation, not a score.</h2>
          <p>Bring reviews, progress, and people into focus — all in one thoughtful workspace.</p>
          <div className="auth-orbit"><span className="orbit-dot dot-one" /><span className="orbit-dot dot-two" /><span className="orbit-dot dot-three" /><div className="orbit-center">W</div></div>
        </div>
        <span className="auth-aside-foot">Thoughtful reviews. Stronger teams.</span>
      </div>
      <section className="auth-panel">
        <div className="auth-panel-brand"><div className="brand-mark">W</div><span>WorkPulse</span></div>
        <div className="auth-card">
          <p className="eyebrow">{isSignup ? "Start your workspace" : "Welcome back"}</p>
          <h1>{isSignup ? "Make room for growth." : "Good to see you."}</h1>
          <p className="auth-copy">{isSignup ? "Create your private performance workspace." : "Sign in to continue to your workspace."}</p>
          {error && <div className="form-alert form-alert-error" role="alert">{error}</div>}
          {message && <div className="form-alert form-alert-success" role="status">{message}</div>}
          <form className="auth-form" onSubmit={handleSubmit}>
            {isSignup && <label className="field"><span>Your name</span><input name="name" autoComplete="name" placeholder="Jordan Lee" required /></label>}
            <label className="field"><span>Email address</span><span className="input-wrap"><Mail size={17} aria-hidden="true" /><input name="email" type="email" autoComplete="email" placeholder="you@company.com" required /></span></label>
            <label className="field">
              <span>Password</span>
              <span className="input-wrap">
                <LockKeyhole size={17} aria-hidden="true" />
                <input name="password" type={showPassword ? "text" : "password"} autoComplete={isSignup ? "new-password" : "current-password"} placeholder={isSignup ? "At least 8 characters" : "Enter your password"} minLength={8} required />
                <button type="button" className="eye-toggle" aria-label={showPassword ? "Hide password" : "Show password"} onClick={() => setShowPassword(!showPassword)}>
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </span>
            </label>
            <button className="button button-primary button-full" type="submit" disabled={pending}>{pending ? "Please wait…" : isSignup ? "Create account" : "Sign in"}<ArrowRight size={17} aria-hidden="true" /></button>
          </form>
          <p className="auth-switch">{isSignup ? "Already have an account?" : "New to WorkPulse?"} <Link href={isSignup ? "/auth/login" : "/auth/sign-up"}>{isSignup ? "Sign in" : "Create an account"}</Link></p>
          <p className="auth-legal">Your workspace is private to your account. We never use sample employee records.</p>
        </div>
      </section>
    </main>
  );
}
