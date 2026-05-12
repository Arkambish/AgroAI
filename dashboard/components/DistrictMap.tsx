"use client";

import { MapPin } from "lucide-react";

interface DistrictMapProps {
  predictions?: Record<string, number>;
}

export default function DistrictMap({ predictions = {} }: DistrictMapProps) {
  // Mock districts data for visualization
  const districts = [
    { name: "Anuradhapura", yield: predictions["Anuradhapura"] || 12.5, x: 40, y: 35 },
    { name: "Matale", yield: predictions["Matale"] || 18.2, x: 55, y: 65 },
    { name: "Polonnaruwa", yield: predictions["Polonnaruwa"] || 14.8, x: 70, y: 50 },
    { name: "Jaffna", yield: predictions["Jaffna"] || 8.4, x: 30, y: 10 },
  ];

  const getColor = (yieldVal: number) => {
    if (yieldVal > 15) return "fill-emerald-600";
    if (yieldVal > 10) return "fill-emerald-400";
    return "fill-emerald-200";
  };

  return (
    <div className="relative overflow-hidden rounded-2xl border bg-white p-6 shadow-md dark:bg-slate-900">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-bold text-slate-900 dark:text-white">Yield by District</h3>
        <div className="flex space-x-2 text-xs">
          <div className="flex items-center"><div className="mr-1 h-3 w-3 rounded-full bg-emerald-600"></div> High</div>
          <div className="flex items-center"><div className="mr-1 h-3 w-3 rounded-full bg-emerald-400"></div> Med</div>
          <div className="flex items-center"><div className="mr-1 h-3 w-3 rounded-full bg-emerald-200"></div> Low</div>
        </div>
      </div>
      
      <div className="relative mx-auto h-[400px] w-full max-w-[300px]">
        {/* Simple stylized map of Sri Lanka */}
        <svg viewBox="0 0 100 120" className="h-full w-full">
          <path
            d="M50 5 L70 20 L80 50 L75 80 L60 110 L40 115 L20 100 L10 70 L15 40 L30 10 Z"
            className="fill-slate-100 stroke-slate-200 dark:fill-slate-800 dark:stroke-slate-700"
            strokeWidth="0.5"
          />
          
          {districts.map((d) => (
            <g key={d.name} className="cursor-pointer transition-opacity hover:opacity-80">
              <circle
                cx={d.x}
                cy={d.y}
                r="6"
                className={`${getColor(d.yield)} stroke-white`}
                strokeWidth="1"
              />
              <text
                x={d.x}
                y={d.y + 12}
                textAnchor="middle"
                className="fill-slate-600 text-[4px] font-bold dark:fill-slate-400"
              >
                {d.name}
              </text>
              <text
                x={d.x}
                y={d.y + 18}
                textAnchor="middle"
                className="fill-primary text-[3px] font-bold"
              >
                {d.yield} MT/Ha
              </text>
            </g>
          ))}
        </svg>
        
        <div className="absolute bottom-4 left-4 rounded-lg bg-white/90 p-2 text-[10px] shadow-sm dark:bg-slate-800/90">
          <p className="font-bold text-slate-900 dark:text-white">Quick Fact:</p>
          <p className="text-slate-600 dark:text-slate-400">Matale leads in current predictions.</p>
        </div>
      </div>
    </div>
  );
}
