"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { Activity, ArrowUpRight, Bell, CalendarDays, ChevronDown, ClipboardCheck, LayoutDashboard, LogOut, Menu, Users, X, Cog } from "lucide-react";
import { WorkspaceUserProvider } from "@/components/workspace-user";

const navigation = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/employees", label: "Employees", icon: Users },
  { href: "/cycles", label: "Review cycles", icon: CalendarDays },
  { href: "/assessments", label: "Assessments", icon: ClipboardCheck },
];

const adminNavigation = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/employees", label: "Employees", icon: Users },
  { href: "/cycles", label: "Review cycles", icon: CalendarDays },
  { href: "/assessments", label: "Assessments", icon: ClipboardCheck },
  { href: "/settings", label: "Settings", icon: Cog },
];

export function WorkspaceShell({ children, email, userId, role, fullName }: { children: React.ReactNode; email: string; userId: string; role: string; fullName?: string }) {
  const pathname = usePathname();
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);

  // Determine accessible navigation based on role
  // role: "admin" - full access, "hr" - HR access, "employee" - limited access
  const isAdmin = role === "admin";
  const isHR = role === "hr";
  const isEmployee = role === "employee" || !role;

  const navigationItems = isAdmin
    ? adminNavigation
    : isHR
      ? [
          { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
          { href: "/employees", label: "Employees", icon: Users },
          { href: "/cycles", label: "Review cycles", icon: CalendarDays },
          { href: "/assessments", label: "Assessments", icon: ClipboardCheck },
        ]
      : navigation;

  async function signOut() {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } catch {
      // Ignore network errors during logout
    }
    router.replace("/auth/login");
    router.refresh();
  }

  return (
    <div className="workspace-frame">
      <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
        <Link href="/dashboard" className="brand-lockup" aria-label="WorkPulse overview"><span className="brand-mark">W</span><span>workpulse</span></Link>
        <div className="workspace-switcher"><span className="workspace-avatar">{email.slice(0, 1).toUpperCase()}</span><span className="workspace-name"><strong>My workspace</strong><small>Private workspace</small></span><ChevronDown size={15} aria-hidden="true" /></div>
        <p className="nav-caption">WORKSPACE</p>
        <nav className="side-nav" aria-label="Main navigation">
          {navigationItems.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || (href === "/dashboard" && pathname === "/");
            return <Link key={href} href={href} onClick={() => setMenuOpen(false)} className={`nav-link ${active ? "nav-link-active" : ""}`} aria-current={active ? "page" : undefined}><Icon size={18} strokeWidth={active ? 2.2 : 1.8} aria-hidden="true" /><span>{label}</span>{active && <span className="nav-active-mark" />}</Link>;
          })}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-note"><span className="note-icon"><Activity size={16} /></span><div><strong>Keep growing</strong><span>Small steps make lasting progress.</span></div></div>
          <button className="profile-button" type="button" onClick={() => setAccountOpen(!accountOpen)} aria-expanded={accountOpen}>
            <span className="profile-avatar">{email.slice(0, 1).toUpperCase()}</span><span className="profile-copy"><strong>{email.split("@")[0]}</strong><small>{email}</small></span><ChevronDown size={16} aria-hidden="true" />
          </button>
          {accountOpen && <button className="signout-button" type="button" onClick={signOut}><LogOut size={16} aria-hidden="true" /> Sign out</button>}
        </div>
      </aside>
      <div className="mobile-menu-backdrop" aria-label="Close menu" onClick={() => setMenuOpen(false)} />
      <div className="main-column">
        <header className="topbar">
          <button className="mobile-menu-toggle" type="button" aria-label={menuOpen ? "Close navigation" : "Open navigation"} onClick={() => setMenuOpen(!menuOpen)}>{menuOpen ? <X size={20} /> : <Menu size={20} />}</button>
          <div className="breadcrumb"><span>Workspace</span><span className="breadcrumb-slash">/</span><strong>{navigationItems.find((item) => item.href === pathname)?.label ?? "Overview"}</strong></div>
          <div className="topbar-actions">
            <span className="secure-label"><span className="secure-dot" /> Private workspace</span>
            <button className="icon-button" type="button" aria-label="Notifications" title="Notifications are coming soon"><Bell size={18} /></button>
            <Link className="help-link" href="/dashboard">Help center <ArrowUpRight size={14} /></Link>
          </div>
        </header>
        <main className="workspace-main"><WorkspaceUserProvider userId={userId} role={role}>{children}</WorkspaceUserProvider></main>
        <footer className="workspace-footer"><span>WorkPulse</span><span>Performance with purpose</span><span>© {new Date().getFullYear()} WorkPulse</span></footer>
      </div>
    </div>
  );
}