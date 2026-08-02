"use client";

import { MapPin, RefreshCw } from "lucide-react";
import { useTranslations } from "next-intl";
import type { DistrictInfo } from "@/lib/api";

export interface FarmerInputs {
  district: string;
  season: string;
  year: number;
}

interface Props {
  value: FarmerInputs;
  districts: DistrictInfo[];
  loading: boolean;
  onChange: (patch: Partial<FarmerInputs>) => void;
}

const selectClass =
  "w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm font-semibold text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 outline-none";

/**
 * The only three things a farmer actually provides: district, season and
 * year. Every other model input (rainfall, temperature, NDVI, soil, prior
 * yield, ...) is resolved server-side and shown read-only in
 * KnownDataPanel — nothing here asks for a satellite index.
 */
export default function FieldInputCard({
  value,
  districts,
  loading,
  onChange,
}: Props) {
  const t = useTranslations("form");
  const tDistricts = useTranslations("districts");
  const tSeasons = useTranslations("seasons");

  // Option labels have translations keyed by lowercase name; fall back to the
  // API's own spelling for anything not in the message files.
  const districtLabel = (name: string) => {
    const key = name.toLowerCase();
    return tDistricts.has(key) ? tDistricts(key) : name;
  };
  const seasonLabel = (name: string) => {
    const key = name.toLowerCase();
    return tSeasons.has(key) ? tSeasons(key) : name;
  };

  const selected = districts.find((d) => d.name === value.district);
  // Only Yala is offered — Maha season has been retired from this dashboard,
  // so it's filtered out here even if the backend catalog still reports it.
  const availableSeasons = (selected?.seasons ?? []).filter(
    (s) => s.toLowerCase() === "yala"
  );
  // Offer the dataset's years plus projection years beyond the last, always
  // reaching at least two years past *today* (not just past the dataset) —
  // otherwise a district whose data ends in the past (e.g. the synthetic
  // variant's 2023 cutoff) would never offer the current year the form
  // defaults to, leaving the dropdown out of sync with the selected value.
  const datasetYears = selected?.years ?? [];
  const lastYear = datasetYears.length
    ? datasetYears[datasetYears.length - 1]
    : new Date().getFullYear();
  const projectionEnd = Math.max(lastYear + 2, new Date().getFullYear() + 2);
  const projectedYears = [];
  for (let y = lastYear + 1; y <= projectionEnd; y++) projectedYears.push(y);
  const years = [...datasetYears, ...projectedYears];

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm space-y-5">
      <div className="flex items-center justify-between border-b pb-3">
        <div className="flex items-center space-x-2">
          <MapPin className="text-emerald-600" size={20} />
          <h3 className="text-lg font-bold text-slate-900">
            {t("fieldSectionTitle")}
          </h3>
        </div>
        {loading && (
          <div className="flex items-center space-x-1 text-xs font-semibold text-emerald-600">
            <RefreshCw size={12} className="animate-spin" />
            <span>{t("loadingArea")}</span>
          </div>
        )}
      </div>

      <p className="text-sm text-slate-500">{t("fieldSectionHelp")}</p>

      {/* suppressHydrationWarning on the fields below: autofill/password-
          manager browser extensions (LastPass, Dashlane, 1Password, Fillr,
          ...) stamp fdprocessedid="..." onto every <select>/<input> they
          scan right after the DOM is available, before React hydrates —
          React then reports that as a mismatch even though nothing here
          actually renders differently server vs. client (see
          LanguageSwitcher.tsx/Navbar.tsx for the same, already-confirmed
          case). This only silences that one false-positive attribute. */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="space-y-1.5">
          <label htmlFor="district" className="text-xs font-bold text-slate-700">
            {t("district")}
          </label>
          <select
            id="district"
            name="district"
            value={value.district}
            onChange={(e) => onChange({ district: e.target.value })}
            className={selectClass}
            suppressHydrationWarning
          >
            {districts.map((d) => (
              <option key={d.name} value={d.name}>
                {districtLabel(d.name)}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-1.5">
          <label htmlFor="season" className="text-xs font-bold text-slate-700">
            {t("season")}
          </label>
          <select
            id="season"
            name="season"
            value={value.season}
            onChange={(e) => onChange({ season: e.target.value })}
            className={selectClass}
            suppressHydrationWarning
          >
            {availableSeasons.map((s) => (
              <option key={s} value={s}>
                {seasonLabel(s)}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-1.5">
          <label htmlFor="year" className="text-xs font-bold text-slate-700">
            {t("year")}
          </label>
          <select
            id="year"
            name="year"
            value={value.year}
            onChange={(e) => onChange({ year: Number(e.target.value) })}
            className={selectClass}
            suppressHydrationWarning
          >
            {years.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
