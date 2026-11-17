import Link from "next/link";

export default function AuthErrorPage() {
  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="brand-mark">W</div>
        <p className="eyebrow">WorkPulse account</p>
        <h1>That link didn&apos;t work</h1>
        <p className="auth-copy">The sign-in link may have expired. Request a fresh one or return to your account.</p>
        <Link className="button button-primary button-full" href="/auth/login">Return to sign in</Link>
      </section>
    </main>
  );
}
