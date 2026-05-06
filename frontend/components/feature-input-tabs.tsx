"use client";

import * as React from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FEATURE_GROUPS, FEATURE_META } from "@/lib/constants";

interface FeatureInputTabsProps {
  values: Record<string, number>;
  onChange: (next: Record<string, number>) => void;
}

const GROUP_NAMES = Object.keys(FEATURE_GROUPS) as (keyof typeof FEATURE_GROUPS)[];

export function FeatureInputTabs({ values, onChange }: FeatureInputTabsProps) {
  const updateOne = (name: string, raw: string) => {
    const parsed = Number(raw);
    onChange({ ...values, [name]: Number.isFinite(parsed) ? parsed : 0 });
  };

  return (
    <Tabs defaultValue={GROUP_NAMES[0]} className="w-full">
      <TabsList>
        {GROUP_NAMES.map((g) => (
          <TabsTrigger key={g} value={g}>
            {g}
            <span className="ml-1 text-xs text-slate-400">
              ({FEATURE_GROUPS[g].length})
            </span>
          </TabsTrigger>
        ))}
      </TabsList>

      {GROUP_NAMES.map((group) => (
        <TabsContent key={group} value={group}>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {FEATURE_GROUPS[group].map((name) => {
              const meta = FEATURE_META[name] ?? { label: name };
              const id = `feat-${name}`;
              const v = values[name];
              return (
                <div key={name} className="space-y-1">
                  <Label htmlFor={id} className="flex items-center gap-1 text-xs">
                    <span>{meta.label}</span>
                    {meta.unit && (
                      <span className="text-slate-400 dark:text-slate-500">
                        ({meta.unit})
                      </span>
                    )}
                  </Label>
                  <Input
                    id={id}
                    type="number"
                    step="any"
                    value={Number.isFinite(v) ? v : ""}
                    onChange={(e) => updateOne(name, e.target.value)}
                    aria-describedby={meta.help ? `${id}-help` : undefined}
                  />
                  {meta.help && (
                    <p id={`${id}-help`} className="text-[10px] text-slate-400">
                      {meta.help}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </TabsContent>
      ))}
    </Tabs>
  );
}
