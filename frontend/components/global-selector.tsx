"use client";

import * as React from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { DISTRICTS, SEASONS } from "@/lib/constants";
import { useSelection } from "./selection-context";
import type { District, Season } from "@/lib/types";

export function GlobalSelector() {
  const { district, season, year, setDistrict, setSeason, setYear } = useSelection();

  return (
    <div className="grid gap-3">
      <div>
        <Label htmlFor="district-select" className="mb-1.5 block text-xs uppercase text-slate-500 dark:text-slate-400">
          District
        </Label>
        <Select value={district} onValueChange={(v) => setDistrict(v as District)}>
          <SelectTrigger id="district-select" aria-label="District">
            <SelectValue placeholder="Select district" />
          </SelectTrigger>
          <SelectContent>
            {DISTRICTS.map((d) => (
              <SelectItem key={d} value={d}>
                {d}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div>
        <Label htmlFor="season-select" className="mb-1.5 block text-xs uppercase text-slate-500 dark:text-slate-400">
          Season
        </Label>
        <Select value={season} onValueChange={(v) => setSeason(v as Season)}>
          <SelectTrigger id="season-select" aria-label="Season">
            <SelectValue placeholder="Select season" />
          </SelectTrigger>
          <SelectContent>
            {SEASONS.map((s) => (
              <SelectItem key={s} value={s}>
                {s}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div>
        <Label htmlFor="year-input" className="mb-1.5 block text-xs uppercase text-slate-500 dark:text-slate-400">
          Year
        </Label>
        <Input
          id="year-input"
          type="number"
          min={2004}
          max={2030}
          value={year}
          onChange={(e) => {
            const next = Number(e.target.value);
            if (Number.isFinite(next)) setYear(next);
          }}
          aria-label="Year"
        />
      </div>
    </div>
  );
}
