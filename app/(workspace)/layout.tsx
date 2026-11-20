import { redirect } from "next/navigation";
import { WorkspaceShell } from "@/components/workspace-shell";
import { getSession } from "@/lib/auth/session";

export default async function WorkspaceLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const session = await getSession();

  if (!session) redirect("/auth/login");

  return (
    <WorkspaceShell
      email={session.email}
      userId={session.userId}
      role={session.role}
      fullName={session.fullName}
    >
      {children}
    </WorkspaceShell>
  );
}