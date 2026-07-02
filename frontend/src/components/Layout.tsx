import {
  Building2,
  FileText,
  LayoutDashboard,
  LogOut,
  Receipt,
  ScrollText,
  Users,
  UserSquare2,
  Clock,
  UserCog,
} from "lucide-react";
import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

const nav = [
  { to: "/", label: "ダッシュボード", icon: LayoutDashboard, end: true },
  { to: "/engineers", label: "技術者", icon: Users },
  { to: "/clients", label: "取引先", icon: Building2 },
  { to: "/projects", label: "案件", icon: FileText },
  { to: "/contracts", label: "契約", icon: ScrollText },
  { to: "/work-records", label: "稼働実績", icon: Clock },
  { to: "/invoices", label: "請求", icon: Receipt },
  { to: "/employees", label: "社員管理", icon: UserSquare2 },
];

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const isAdmin = user?.role === "admin";

  return (
    <div className="flex min-h-screen">
      {/* サイドバー */}
      <aside className="flex w-60 flex-col border-r bg-card">
        <div className="flex h-14 items-center border-b px-4 font-bold text-primary">
          SES管理システム
        </div>
        <nav className="flex-1 space-y-1 p-2">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                )
              }
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          ))}
          {isAdmin && (
            <NavLink
              to="/users"
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                )
              }
            >
              <UserCog className="h-4 w-4" />
              ユーザー管理
            </NavLink>
          )}
        </nav>
      </aside>

      {/* メイン */}
      <div className="flex flex-1 flex-col">
        <header className="flex h-14 items-center justify-end gap-4 border-b bg-card px-6">
          <div className="flex items-center gap-2 text-sm">
            <span className="font-medium">{user?.name}</span>
            {user && <Badge variant="secondary">{user.role}</Badge>}
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            <LogOut className="h-4 w-4" />
            ログアウト
          </button>
        </header>
        <main className="flex-1 overflow-auto bg-muted/30 p-6">{children}</main>
      </div>
    </div>
  );
}
