"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, type FormEvent } from "react";
import { ArrowRight, Eye, EyeOff, LockKeyhole, Mail, AlertCircle } from "lucide-react";

type AuthMode = "login" | "sign-up";

function getAuthErrorMessage(message: string, isSignup: boolean): string {
  const msg = message.toLowerCase();
  
  if (isSignup) {
    if (msg.includes("password")) return "Password must be at least 8 characters long.";
    if (msg.includes("already exists")) return "An account with this email already exists. Try signing in instead.";
    if (msg.includes("invalid email")) return "Please enter a valid email address.";
    return "We couldn't create your account. Please check your details and try again.";
  } else {
    if (msg.includes("invalid email or password")) return "Invalid email or password. Please check your credentials and try again.";
    return "We couldn't sign you in right now. Please try again.";
  }
}

export function AuthForm({ mode }: { mode: AuthMode }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const isSignup = mode === "sign-up";

  // Check for URL-based error messages (from redirect)
  const urlError = searchParams.get('error');
  const urlMessage = searchParams.get('message');
  if (urlError && urlMessage && !error) {
    setError(urlMessage);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setMessage("");
    setError("");
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "").trim();
    const password = String(form.get("password") ?? "");

    const endpoint = isSignup ? "/api/auth/register" : "/api/auth/login";
    const body: Record<string, string> = { email, password };
    
    if (isSignup) {
      const name = String(form.get("name") ?? "").trim();
      body.name = name;
    }

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(getAuthErrorMessage(data.error || "Authentication failed", isSignup));
      } else {
        const next = searchParams.get('next') ?? '/dashboard';
        router.push(next);
        router.refresh();
      }
    } catch {
      setError("An unexpected error occurred. Please try again.");
    } finally {
      setPending(false);
    }
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
          
          {(error || urlError) && (
            <div className="form-alert form-alert-error" role="alert">
              <AlertCircle size={16} aria-hidden="true" />
              <span>{error || urlMessage}</span>
            </div>
          )}
          
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
