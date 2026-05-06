"use client";

import * as React from "react";
import useSWR from "swr";
import { Sprout, MapIcon, Trophy, Target } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { KpiCard } from "@/components/kpi-card";
import { DistrictMap } from "@/components/district-map";
import { SeasonalComparisonChart, type SeasonalRow } from "@/components/seasonal-comparison-chart";
import { useSelection } from "@/components/selection-context";
import { getContext, getHealth, getModelsCompare, predict } from "@/lib/api";
import { DISTRICTS, SEASONS, TARGET_R2 } from "@/lib/constants";
import type { District, PredictResponse } from "@/lib/types";
import { formatNumber } from "@/lib/utils";
import Link from "next/link";

interface DistrictSeasonPrediction {
  district: District;
  season: "Yala" | "Maha";
  predicted: number;
  ci_lower: number;
  ci_upper: number;
}

function r2TargetHint(r2: number | undefined): string {
  if (r2 === undefined) return "—";
  return r2 >= TARGET_R2 ? "Met on synthetic data" : "Below target";
}

async function predictAllDistrictsForYear(year: number): Promise<DistrictSeasonPrediction[]> {
  const tasks = DISTRICTS.flatMap((d) =>
    SEASONS.map(async (s) => {
      try {
        const ctx = await getContext(d, s, year);
        const features: Record<string, number> = {};
        for (const [k, v] of Object.entries(ctx)) {
          if (typeof v === "number") features[k] = v;
        }
        const r: PredictResponse = await predict({ district: d, season: s, ...features });
        return {
          district: d,
          season: s,
          predicted: r.predicted_yield_MT_per_Ha,
          ci_lower: r.confidence_lower,
          ci_upper: r.confidence_upper,
        } as DistrictSeasonPrediction;
      } catch {
        return null;
      }
    }),
  );
  const results = await Promise.all(tasks);
  return results.filter((r): r is DistrictSeasonPrediction => r !== null);
}

export default function HomePage() {
  const { year, season } = useSelection();
  const { data: health } = useSWR("health", getHealth);
  const { data: models } = useSWR("models-compare", getModelsCompare);
  const { data: predictions, isLoading: predicting } = useSWR(
    ["home-predictions", year] as const,
    ([, y]) => predictAllDistrictsForYear(y),
    { revalidateOnFocus: false },
  );

  const bestModel = React.useMemo(() => {
    if (!models || models.length === 0) return null;
    return [...models].sort((a, b) => b.R2 - a.R2)[0];
  }, [models]);

  const districtPredictionsForSeason = React.useMemo(() => {
    if (!predictions) return {};
    return Object.fromEntries(
      predictions.filter((p) => p.season === season).map((p) => [p.district, p.predicted]),
    ) as Partial<Record<District, number>>;
  }, [predictions, season]);

  const seasonalRows: SeasonalRow[] = React.useMemo(() => {
    if (!predictions) return [];
    const byDistrict = new Map<District, SeasonalRow>();
    for (const p of predictions) {
      const row = byDistrict.get(p.district) ?? { district: p.district };
      if (p.season === "Yala") row.yala = p.predicted;
      else row.maha = p.predicted;
      byDistrict.set(p.district, row);
    }
    return Array.from(byDistrict.values());
  }, [predictions]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Decision-support dashboard</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Big onion (Allium cepa) yield forecasts for {year} across the four target districts.
          </p>
        </div>
        <Link href="/predict">
          <Button>
            <Sprout className="h-4 w-4" />
            New prediction
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          accent="novel"
          label="Best model"
          value={bestModel?.Model ?? "—"}
          hint={bestModel ? `R² = ${formatNumber(bestModel.R2, 3)} (LOYO-CV)` : "Loading…"}
          icon={<Trophy className="h-5 w-5 text-slate-400" />}
        />
        <KpiCard
          accent="ml"
          label="R² target"
          value={`${TARGET_R2}`}
          hint={r2TargetHint(bestModel?.R2)}
          icon={<Target className="h-5 w-5 text-slate-400" />}
        />
        <KpiCard
          accent="data"
          label="Districts covered"
          value={`${DISTRICTS.length}`}
          hint="Matale, Anuradhapura, Polonnaruwa, Jaffna"
          icon={<MapIcon className="h-5 w-5 text-slate-400" />}
        />
        <KpiCard
          accent="output"
          label="API status"
          value={health?.status === "ok" ? "Online" : "Offline"}
          hint={health?.model ? `Serving ${health.model}` : "Backend unavailable"}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Predicted yield by district — {season} {year}</CardTitle>
          <CardDescription>
            Click a district to make it the active selection across pages. Colour scale ranges
            from 4 to 24 MT/Ha (viridis).
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DistrictMap predictions={districtPredictionsForSeason} height={460} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Yala vs Maha — {year}</CardTitle>
          <CardDescription>
            Side-by-side predicted yield per district for both seasons of the chosen year.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {predicting && !seasonalRows.length ? (
            <div className="grid h-80 place-items-center text-sm text-slate-500">
              Loading predictions…
            </div>
          ) : (
            <SeasonalComparisonChart rows={seasonalRows} height={320} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
