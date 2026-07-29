import Link from "next/link";
import "./globals.css";

export const metadata = {
  title: "Review Spine",
  description: "AI pull-request review operations dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="app-shell">
          <aside className="sidebar">
            <h1 className="brand">Review Spine</h1>
            <nav className="nav">
              <Link href="/reviews">Reviews</Link>
              <Link href="/hitl">HITL</Link>
              <Link href="/trace">Trace</Link>
              <Link href="/economics">Economics</Link>
            </nav>
          </aside>
          <main className="main">{children}</main>
        </div>
      </body>
    </html>
  );
}

