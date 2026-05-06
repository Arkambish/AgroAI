"use client";

import * as React from "react";
import useSWR from "swr";
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ModelComparisonChart } from "@/components/model-comparison-chart";
import { getModelsCompare } from "@/lib/api";
import type { ModelComparisonRow } from "@/lib/types";
import { formatNumber, cn } from "@/lib/utils";
import { TARGET_R2 } from "@/lib/constants";

type SortKey = keyof ModelComparisonRow;

export default function AdminPage() {
  const { data, error, isLoading } = useSWR("models-compare", getModelsCompare);
  const [sortKey, setSortKey] = React.useState<SortKey>("R2");
  const [sortDir, setSortDir] = React.useState<"asc" | "desc">("desc");

  const sorted = React.useMemo(() => {
    if (!data) return [];
    const copy = [...data];
    copy.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av === null) return 1;
      if (bv === null) return -1;
      if (typeof av === "number" && typeof bv === "number") {
        return sortDir === "asc" ? av - bv : bv - av;
      }
      return sortDir === "asc"
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av));
    });
    return copy;
  }, [data, sortKey, sortDir]);

  const onSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(key === "Model" ? "asc" : "desc");
    }
  };

  const SortIcon = ({ column }: { column: SortKey }) => {
    if (column !== sortKey) return <ArrowUpDown className="ml-1 inline h-3 w-3 opacity-40" />;
    return sortDir === "asc" ? (
      <ArrowUp className="ml-1 inline h-3 w-3" />
    ) : (
      <ArrowDown className="ml-1 inline h-3 w-3" />
    );
  };

  const columns: { key: SortKey; label: string; align?: "right" }[] = [
    { key: "Model", label: "Model" },
    { key: "RMSE", label: "RMSE", align: "right" },
    { key: "MAE", label: "MAE", align: "right" },
    { key: "R2", label: "R²", align: "right" },
    { key: "MAPE", label: "MAPE %", align: "right" },
    { key: "Train_Time_s", label: "Train (s)", align: "right" },
    { key: "Parameters", label: "Params", align: "right" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Model performance</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Side-by-side metrics for all seven models from <code>outputs/results/model_comparison.csv</code>.
          Evaluated using Leave-One-Year-Out cross-validation.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>RMSE and R² by model</CardTitle>
          <CardDescription>
            Bars: RMSE (lower is better, left axis). Line: R² (higher is better, right axis,
            target dashed at R² = {TARGET_R2}).
            Colours follow the report convention: blue = ML, orange = DL, red = Hybrid.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="grid h-[360px] place-items-center text-sm text-slate-500">
              Loading model metrics…
            </div>
          )}
          {error && (
            <p className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
              Could not load model comparison: {String(error)}
            </p>
          )}
          {data && <ModelComparisonChart rows={data} height={400} />}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Detailed metrics</CardTitle>
          <CardDescription>Click any column header to sort.</CardDescription>
        </CardHeader>
        <CardContent>
          {data && (
            <Table>
              <TableHeader>
                <TableRow>
                  {columns.map((c) => (
                    <TableHead
                      key={c.key}
                      className={cn("cursor-pointer select-none", c.align === "right" && "text-right")}
                      onClick={() => onSort(c.key)}
                      aria-sort={
                        sortKey === c.key
                          ? sortDir === "asc"
                            ? "ascending"
                            : "descending"
                          : "none"
                      }
                    >
                      {c.label}
                      <SortIcon column={c.key} />
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {sorted.map((row) => (
                  <TableRow key={row.Model}>
                    <TableCell className="font-medium">{row.Model}</TableCell>
                    <TableCell className="text-right tabular-nums">{formatNumber(row.RMSE)}</TableCell>
                    <TableCell className="text-right tabular-nums">{formatNumber(row.MAE)}</TableCell>
                    <TableCell
                      className={cn(
                        "text-right tabular-nums",
                        row.R2 >= TARGET_R2 ? "text-emerald-600 dark:text-emerald-400" : "",
                      )}
                    >
                      {formatNumber(row.R2, 3)}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">{formatNumber(row.MAPE, 2)}</TableCell>
                    <TableCell className="text-right tabular-nums">
                      {row.Train_Time_s !== null ? formatNumber(row.Train_Time_s, 2) : "—"}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {row.Parameters !== null ? row.Parameters.toLocaleString() : "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
