"use client";

import { useState } from "react";
import { ChevronDown, Lock, Satellite } from "lucide-react";
import { useTranslations } from "next-intl";
import { clsx } from "clsx";
import { FEATURE_GROUPS, formatFeatureValue } from "@/lib/features";
import type { ContextResponse } from "@/lib/api";

interface Props {
  context: ContextResponse | null;
  /** Populated after a prediction — the values actually fed to the model */
  resolved?: Record<string, number>;
  loading: boolean;
  error: string | null;
}

/**
 * Everything the model needs beyond district/season/year — weather,
 * satellite, soil and historical-harvest figures a farmer cannot measure
 * themselves. Shown read-only, with no provenance/source detail: the farmer
 * only needs to know these were filled in automatically and cannot be
 * changed here, not which averaging tier each one came from.
 */
export default function KnownDataPanel({
  context,
  resolved,
  loading,
  error,
}: Props) {
  const t = useTranslations("form");
  const tf = useTranslations("features");
  const tg = useTranslations("featureGroups");
  // Individual group accordions inside the details view all start collapsed
  // — the farmer opens "View details" first, then drills into a group if
  // they want to, rather than being shown Weather's raw feature list by
  // default.
  const [open, setOpen] = useState<string | null>(null);
  // The whole technical breakdown is hidden by default. Non-technical
  // farmers only need to know these values were filled in automatically;
  // the per-group feature list is an opt-in "View details" drawer.
  const [detailsOpen, setDetailsOpen] = useState(false);

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b pb-3">
        <div className="flex items-center space-x-2">
          <Satellite className="text-sky-600" size={20} />
          <h3 className="text-lg font-bold text-slate-900">
            {t("knownSectionTitle")}
          </h3>
        </div>
        <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-500">
          <Lock size={11} />
          {t("autoFilled")}
        </span>
      </div>

      <p className="text-sm text-slate-500">{t("knownSectionHelp")}</p>

      {error && (
        <p className="rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {error}
        </p>
      )}

      {/* This toggle is the only button in this file present during
          hydration — the per-group buttons below only mount once
          `detailsOpen` flips true via a client click, well after hydration
          completes, so they can't hit a mismatch. suppressHydrationWarning:
          autofill/password-manager browser extensions stamp
          fdprocessedid="..." onto every <button> they scan post-mount,
          which React otherwise reports as a mismatch even though nothing
          here renders differently server vs. client — see
          LanguageSwitcher.tsx/Navbar.tsx for the same, already-confirmed
          case. */}
      <button
        type="button"
        aria-expanded={detailsOpen}
        onClick={() => setDetailsOpen((v) => !v)}
        className="inline-flex items-center space-x-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-bold text-sky-700 transition-colors hover:bg-sky-50"
        suppressHydrationWarning
      >
        <span>{detailsOpen ? t("hideDetails") : t("viewDetails")}</span>
        <ChevronDown
          size={14}
          className={clsx("transition-transform", detailsOpen && "rotate-180")}
        />
      </button>

      {detailsOpen && (
        <div className="space-y-2">
          {FEATURE_GROUPS.map((group) => {
            const isOpen = open === group.key;
            return (
              <div
                key={group.key}
                className="overflow-hidden rounded-2xl border border-slate-200"
              >
                <button
                  type="button"
                  aria-expanded={isOpen}
                  onClick={() => setOpen(isOpen ? null : group.key)}
                  className="flex w-full items-center justify-between bg-slate-50 px-4 py-3 text-left transition-colors hover:bg-slate-100"
                >
                  <span className="text-sm font-bold text-slate-800">
                    {tg(group.labelKey)}
                  </span>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-slate-400">
                      {group.features.length}
                    </span>
                    <ChevronDown
                      size={16}
                      className={clsx(
                        "text-slate-400 transition-transform",
                        isOpen && "rotate-180",
                      )}
                    />
                  </div>
                </button>

                {isOpen && (
                  <dl className="divide-y divide-slate-100">
                    {group.features.map((meta) => {
                      // What the model actually used, if a prediction has
                      // already run — otherwise the area's context value.
                      const value =
                        resolved?.[meta.name] ??
                        (context?.[meta.name] as number | undefined);

                      return (
                        <div
                          key={meta.name}
                          className="flex items-center justify-between gap-3 px-4 py-2.5"
                        >
                          <dt className="text-xs text-slate-600">
                            {tf(meta.labelKey)}
                          </dt>
                          <dd className="font-mono text-xs font-semibold tabular-nums text-slate-800">
                            {loading && !context
                              ? "…"
                              : formatFeatureValue(value, meta)}
                          </dd>
                        </div>
                      );
                    })}
                  </dl>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
