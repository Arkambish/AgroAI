"use client";
import { useRouter, usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const LANGS = [
  { code: "en", label: "English" },
  { code: "ta", label: "தமிழ்" },
  { code: "si", label: "සිංහල" },
];

export default function LanguageSwitcher() {
  const router = useRouter();
  const pathname = usePathname();
  const [selected, setSelected] = useState<string>("en");

  useEffect(() => {
    // Try to restore from localStorage
    const stored = localStorage.getItem("lang");
    if (stored && LANGS.some(l => l.code === stored)) {
      setSelected(stored);
    } else {
      // Detect from URL
      const match = pathname?.split("/")[1];
      if (match && LANGS.some(l => l.code === match)) {
        setSelected(match);
      }
    }
  }, [pathname]);

  const handleChange = (code: string) => {
    setSelected(code);
    localStorage.setItem("lang", code);
    // Replace the locale in the URL
    const parts = pathname.split("/");
    if (LANGS.some(l => l.code === parts[1])) {
      parts[1] = code;
    } else {
      parts.splice(1, 0, code);
    }
    router.push(parts.join("/"));
  };

  return (
    <div className="flex gap-2 items-center">
      {LANGS.map((lang) => (
        <button
          key={lang.code}
          onClick={() => handleChange(lang.code)}
          className={`px-3 py-1 rounded-lg font-bold border transition-colors duration-150 ${selected === lang.code ? "bg-emerald-600 text-white border-emerald-600" : "bg-white text-emerald-600 border-emerald-300 hover:bg-emerald-50"}`}
        >
          {lang.label}
        </button>
      ))}
    </div>
  );
}
