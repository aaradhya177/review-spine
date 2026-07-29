import Link from "next/link";
import { Activity, CircleDollarSign, GitPullRequest, ListChecks, Settings2 } from "lucide-react";
import "./globals.css";

export const metadata = { title: "Review Spine", description: "AI pull-request review operations dashboard" };

const navItems = [
  { href: "/reviews", label: "Reviews", icon: GitPullRequest },
  { href: "/hitl", label: "Needs review", icon: ListChecks },
  { href: "/trace", label: "Trace", icon: Activity },
  { href: "/economics", label: "Economics", icon: CircleDollarSign },
  { href: "/settings", label: "Settings", icon: Settings2 },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body><div className="app-shell">
    <aside className="sidebar">
      <div className="brand-lockup"><div className="brand-mark">RS</div><div><h1 className="brand">Review Spine</h1><p className="brand-subtitle">Engineering review desk</p></div></div>
      <div className="nav-label">Workspace</div>
      <nav className="nav" aria-label="Primary navigation">{navItems.map(({ href, label, icon: Icon }) => <Link href={href} key={href}><Icon className="nav-icon" aria-hidden="true" /><span>{label}</span></Link>)}</nav>
      <div className="sidebar-footer"><strong>Acme Engineering</strong><br /><span>Local workspace</span></div>
    </aside>
    <div className="workspace"><main className="main">{children}</main></div>
  </div></body></html>;
}
