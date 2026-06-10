"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { LayoutDashboard, Sprout, Brain, Lightbulb, Menu, X } from "lucide-react";
import LanguageSwitcher from "./LanguageSwitcher";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const navItems = [
  { name: "Home", href: "", icon: LayoutDashboard },
  { name: "Predict Yield", href: "predict", icon: Sprout },
  { name: "Explanation", href: "explain", icon: Brain },
  { name: "Recommendations", href: "recommend", icon: Lightbulb },
];

export default function Navbar() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const [locale, setLocale] = useState("en");

  useEffect(() => {
    // Detect locale from path
    const match = pathname?.split("/")[1];
    if (["en", "ta", "si"].includes(match)) {
      setLocale(match);
    } else {
      setLocale("en");
    }
  }, [pathname]);

  // Helper to build locale-aware links
  const getLocaleHref = (href: string) => {
    if (!href) return `/${locale}`;
    return `/${locale}/${href}`;
  };

  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-white/80 backdrop-blur-md dark:bg-slate-900/80">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 justify-between">
          <div className="flex items-center">
            <Link href={getLocaleHref("")} className="flex items-center space-x-2">
              <div className="rounded-lg bg-primary p-1.5 text-white">
                <Sprout size={24} />
              </div>
              <span className="hidden text-xl font-bold tracking-tight text-slate-900 dark:text-white sm:block">
                AgroAI <span className="text-primary">Dashboard</span>
              </span>
            </Link>
          </div>

          {/* Desktop Nav */}
          <div className="hidden items-center space-x-4 md:flex">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={getLocaleHref(item.href)}
                className={cn(
                  "flex items-center space-x-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  pathname === getLocaleHref(item.href)
                    ? "bg-primary/10 text-primary"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
                )}
              >
                <item.icon size={18} />
                <span>{item.name}</span>
              </Link>
            ))}
            <div className="ml-4">
              <LanguageSwitcher />
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="flex items-center md:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="inline-flex items-center justify-center rounded-md p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-500 focus:outline-none"
            >
              {isOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Nav */}
      {isOpen && (
        <div className="border-t md:hidden">
          <div className="space-y-1 px-2 pb-3 pt-2">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setIsOpen(false)}
                className={cn(
                  "flex items-center space-x-3 rounded-lg px-3 py-3 text-base font-medium transition-colors",
                  pathname === item.href
                    ? "bg-primary/10 text-primary"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
                )}
              >
                <item.icon size={20} />
                <span>{item.name}</span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
}
