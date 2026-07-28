"use client";

import { MapPin, RefreshCw } from "lucide-react";
import { useTranslations } from "next-intl";
import type { DistrictInfo } from "@/lib/api";

export interface FarmerInputs {
  district: string;
  season: string;
  year: number;
  /** Optional — hectares planted last season */
  extentHa: string;
  /** Optional — MT/Ha harvested last season */
  lastSeasonYield: string;
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
 * Tier A — the only things a farmer actually knows.
 *
 * District, season and year are required; extent and last season's yield are
 * optional and fall back to district records. Everything else the model needs
 * is filled server-side, so nothing here asks for a satellite index.
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
  const availableSeasons = selected?.seasons ?? [];
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

      {/* The only two model features a farmer genuinely owns. Both optional
          — set off by a dashed divider and a lighter label weight so the
          three required fields above stay the primary focus. */}
      <div className="space-y-3 border-t border-dashed border-slate-100 pt-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <label
              htmlFor="extentHa"
              className="text-xs font-semibold text-slate-500"
            >
              {t("extentLabel")}
            </label>
            <input
              id="extentHa"
              type="number"
              inputMode="decimal"
              min={0}
              step={0.1}
              placeholder={t("useDistrictAverage")}
              value={value.extentHa}
              onChange={(e) => onChange({ extentHa: e.target.value })}
              className={selectClass}
              suppressHydrationWarning
            />
            <p className="text-[11px] text-slate-400">{t("extentHelp")}</p>
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="lastSeasonYield"
              className="text-xs font-semibold text-slate-500"
            >
              {t("lastYieldLabel")}
            </label>
            <input
              id="lastSeasonYield"
              type="number"
              inputMode="decimal"
              min={0}
              step={0.1}
              placeholder={t("useDistrictAverage")}
              value={value.lastSeasonYield}
              onChange={(e) => onChange({ lastSeasonYield: e.target.value })}
              className={selectClass}
              suppressHydrationWarning
            />
            <p className="text-[11px] text-slate-400">{t("lastYieldHelp")}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
