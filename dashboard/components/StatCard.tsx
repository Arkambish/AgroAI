import { LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  trend?: string;
  trendType?: "up" | "down" | "neutral";
  color?: string;
}

export default function StatCard({ label, value, icon: Icon, trend, trendType, color = "bg-primary" }: StatCardProps) {
  return (
    <div className="rounded-2xl border bg-white p-6 shadow-md transition-all hover:shadow-lg dark:bg-slate-900">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</p>
          <h3 className="mt-1 text-2xl font-bold text-slate-900 dark:text-white">{value}</h3>
          {trend && (
            <p className={`mt-1 text-xs font-medium ${
              trendType === "up" ? "text-emerald-600" : 
              trendType === "down" ? "text-red-600" : "text-slate-400"
            }`}>
              {trend}
            </p>
          )}
        </div>
        <div className={`rounded-xl ${color} p-3 text-white`}>
          <Icon size={24} />
        </div>
      </div>
    </div>
  );
}
