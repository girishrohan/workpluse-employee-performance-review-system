import { redirect } from "next/navigation";
import { WorkspaceShell } from "@/components/workspace-shell";
import { createClient } from "@/lib/supabase/server";

export default async function WorkspaceLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) redirect("/auth/login");

  return <WorkspaceShell email={user.email ?? ""} userId={user.id}>{children}</WorkspaceShell>;
}
