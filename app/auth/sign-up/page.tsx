import { AuthForm } from "@/components/auth-form";
import { Suspense } from "react";

export default function SignUpPage() {
  return <Suspense fallback={<div>Loading…</div>}><AuthForm mode="sign-up" /></Suspense>;
}
