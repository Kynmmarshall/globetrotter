import { NavLink, Outlet } from "react-router-dom";
import { Compass, Map, Luggage, MessageCircle, User } from "lucide-react";
import clsx from "clsx";

const NAV_ITEMS = [
  { to: "/", label: "Explore", icon: Compass, end: true },
  { to: "/map", label: "Map", icon: Map },
  { to: "/trips", label: "Trips", icon: Luggage },
  { to: "/chat", label: "Chat", icon: MessageCircle },
  { to: "/profile", label: "Profile", icon: User },
];

export function AppShell() {
  return (
    <div className="flex h-dvh text-ink">
      <nav
        aria-label="Primary"
        className="hidden w-56 shrink-0 flex-col gap-1 overflow-y-auto border-r border-border bg-surface/90 px-3 py-6 backdrop-blur-sm md:flex"
      >
        <div className="mb-6 px-3 font-heading text-lg font-bold text-primary">GlobeTrotter</div>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive ? "bg-primary/10 text-primary" : "text-ink/70 hover:bg-canvas hover:text-ink",
              )
            }
          >
            <item.icon size={18} aria-hidden="true" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <main className="flex-1 overflow-y-auto pb-20 md:pb-0">
        <Outlet />
      </main>

      <nav
        aria-label="Primary"
        className="fixed inset-x-0 bottom-0 z-20 flex items-stretch justify-around border-t border-border bg-surface/90 backdrop-blur-sm pb-[env(safe-area-inset-bottom)] md:hidden"
      >
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              clsx(
                "flex min-h-[56px] flex-1 flex-col items-center justify-center gap-0.5 text-[11px] font-medium",
                isActive ? "text-primary" : "text-ink/60",
              )
            }
          >
            <item.icon size={20} aria-hidden="true" />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
