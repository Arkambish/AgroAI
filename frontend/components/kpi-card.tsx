import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  label: string;
  value: string;
  hint?: string;
  accent?: "data" | "pipeline" | "ml" | "dl" | "novel" | "output";
  icon?: React.ReactNode;
}

const ACCENT_BAR: Record<NonNullable<KpiCardProps["accent"]>, string> = {
  data: "bg-brand-data",
  pipeline: "bg-brand-pipeline",
  ml: "bg-brand-ml",
  dl: "bg-brand-dl",
  novel: "bg-brand-novel",
  output: "bg-brand-output",
};

export function KpiCard({ label, value, hint, accent = "novel", icon }: KpiCardProps) {
  return (
    <Card className="relative overflow-hidden">
      <span className={cn("absolute left-0 top-0 h-full w-1.5", ACCENT_BAR[accent])} aria-hidden />
      <CardHeader className="pb-2 pl-6">
        <CardTitle className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent className="pl-6 pt-0">
        <div className="flex items-end justify-between gap-2">
          <span className="text-2xl font-semibold tabular-nums">{value}</span>
          {icon}
        </div>
        {hint && (
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{hint}</p>
        )}
      </CardContent>
    </Card>
  );
}
