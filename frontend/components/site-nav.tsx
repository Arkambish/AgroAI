"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Sprout, BarChart3, Map, Lightbulb, ServerCog } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Home", icon: Map },
  { href: "/predict", label: "Predict", icon: Sprout },
  { href: "/explainability", label: "Explainability", icon: Lightbulb },
  { href: "/admin", label: "Models", icon: ServerCog },
];

export function SiteNav() {
  const pathname = usePathname();
  return (
    <nav className="flex flex-wrap gap-1">
      {NAV.map(({ href, label, icon: Icon }) => {
        const active = pathname === href || (href !== "/" && pathname.startsWith(href));
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              "inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
              active
                ? "bg-emerald-600 text-white"
                : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800",
            )}
            aria-current={active ? "page" : undefined}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

export function HeaderBranding() {
  return (
    <Link href="/" className="flex items-center gap-2 group">
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-emerald-600 text-white">
        <BarChart3 className="h-4 w-4" />
      </span>
      <span className="flex flex-col leading-tight">
        <span className="text-base font-semibold">Agro AI</span>
        <span className="text-xs text-slate-500 dark:text-slate-400">
          Big onion yield · Sri Lanka
        </span>
      </span>
    </Link>
  );
}
