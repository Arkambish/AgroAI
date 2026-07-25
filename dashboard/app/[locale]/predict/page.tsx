"use client";

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { Sprout, Info, Sparkles } from "lucide-react";
import { useTranslations, useLocale } from "next-intl";

import {
  predictYield,
  getContext,
  getDistricts,
  getBaseline,
  type PredictResponse,
  type ContextResponse,
  type BaselineResponse,
  type DistrictInfo,
} from "@/lib/api";
import { FEATURE_META_BY_NAME } from "@/lib/features";
import { useLocalFlag, useLocalJSONState } from "@/lib/use-local-flag";
import FieldInputCard, { type FarmerInputs } from "@/components/FieldInputCard";
import KnownDataPanel from "@/components/KnownDataPanel";
import AdvancedOverrides, {
  validateOverride,
} from "@/components/AdvancedOverrides";
import PredictionResultCard from "@/components/PredictionResultCard";
import ChatAssistant from "@/components/ChatAssistant";

const ADVANCED_KEY = "agrisense_advanced_mode";
const PREDICTION_KEY = "last_prediction";
const FARMER_INPUTS_KEY = "last_farmer_inputs";

const DEFAULT_FARMER_INPUTS: FarmerInputs = {
  district: "",
  season: "",
  year: new Date().getFullYear(),
  extentHa: "",
  lastSeasonYield: "",
};

export default function PredictPage() {
  const t = useTranslations();
  const tForm = useTranslations("form");
  const locale = useLocale();

  const [loading, setLoading] = useState(false);
  // Backed by localStorage rather than plain useState: Next.js's App Router
  // resets page-level useState on ANY URL change, including a locale-only
  // switch (/en/predict -> /si/predict), since locale lives in the path.
  // This is what made the prediction and form inputs appear to vanish when
  // switching language even though nothing about the data actually changed.
  const [result, setResult] = useLocalJSONState<PredictResponse>(PREDICTION_KEY);
  const [predictError, setPredictError] = useState<string | null>(null);

  // Districts/seasons/years come from the dataset the API actually loaded, so
  // the UI can't offer a combination that has no data behind it.
  const [districts, setDistricts] = useState<DistrictInfo[]>([]);

  // Tier A — what the farmer tells us. Same localStorage-backed persistence
  // as `result`, for the same reason.
  const [storedFarmerInputs, setFarmerInputs] =
    useLocalJSONState<FarmerInputs>(FARMER_INPUTS_KEY);
  const farmerInputs = storedFarmerInputs ?? DEFAULT_FARMER_INPUTS;

  // Tier B — what the system knows. Read-only; never mutated by the user, so
  // refreshing it can no longer wipe what they typed.
  const [context, setContext] = useState<ContextResponse | null>(null);
  const [contextLoading, setContextLoading] = useState(false);
  const [contextError, setContextError] = useState<string | null>(null);
  const [baseline, setBaseline] = useState<BaselineResponse | null>(null);

  // Tier C — expert overrides, kept in their own bucket. The officer-mode
  // preference persists across sessions.
  const [advanced, handleAdvancedToggle] = useLocalFlag(ADVANCED_KEY);
  const [overrides, setOverrides] = useState<Record<string, number>>({});
  const [overrideErrors, setOverrideErrors] = useState<Record<string, string>>(
    {}
  );

  // Read via a ref rather than a dependency: this effect should only run
  // once per real "load" trigger, not every time the persisted inputs
  // change (which would refetch the catalog on every keystroke).
  const farmerInputsRef = useRef(farmerInputs);
  farmerInputsRef.current = farmerInputs;

  // Load the district catalog once, then seed the form with the first valid
  // district/season/year combination — but only if nothing is already
  // persisted, so a language switch (which re-runs this effect, since `t`
  // gets a new identity per locale) doesn't stomp on what the farmer already
  // entered.
  useEffect(() => {
    let active = true;

    const loadDistricts = async () => {
      try {
        const data = await getDistricts();
        if (!active || !data.districts?.length) return;
        setDistricts(data.districts);

        const current = farmerInputsRef.current;
        const stillValid = data.districts.some((d) => d.name === current.district);
        if (!current.district || !stillValid) {
          const first = data.districts[0];
          setFarmerInputs({
            ...current,
            district: first.name,
            season: first.seasons[0] ?? "Yala",
            year: first.years[first.years.length - 1] ?? current.year,
          });
        }
      } catch {
        if (active) setContextError(t("predict.districtsError"));
      }
    };

    void loadDistricts();

    return () => {
      active = false;
    };
  }, [t, setFarmerInputs]);

  const { district, season, year } = farmerInputs;

  // Fetch the area's known values + historical baseline whenever the location
  // changes. Only `context`/`baseline` are touched — overrides survive.
  useEffect(() => {
    if (!district || !season) return;
    let active = true;

    const loadArea = async () => {
      setContextLoading(true);
      setContextError(null);

      const [ctxResult, baseResult] = await Promise.allSettled([
        getContext(district, season, year),
        getBaseline(district, season),
      ]);
      if (!active) return;

      if (ctxResult.status === "fulfilled") {
        setContext(ctxResult.value);
      } else {
        setContext(null);
        setContextError(tForm("contextUnavailable"));
      }
      setBaseline(baseResult.status === "fulfilled" ? baseResult.value : null);
      setContextLoading(false);
    };

    void loadArea();

    return () => {
      active = false;
    };
  }, [district, season, year, tForm]);

  const handleFarmerChange = useCallback(
    (patch: Partial<FarmerInputs>) => {
      // A result belongs to the location it was produced for — drop it so the
      // panel can't show a Matale prediction next to a Kurunegala form.
      if (patch.district || patch.season || patch.year !== undefined) {
        setResult(null);
        setPredictError(null);
      }

      const next = { ...farmerInputs, ...patch };
      // Reconcile season/year against the new district's actual coverage, so
      // the form can never request a combination the dataset lacks.
      if (patch.district) {
        const info = districts.find((d) => d.name === patch.district);
        if (info) {
          if (!info.seasons.includes(next.season)) {
            next.season = info.seasons[0] ?? next.season;
          }
          const maxYear = info.years[info.years.length - 1];
          if (maxYear !== undefined && next.year > maxYear + 2) {
            next.year = maxYear;
          }
        }
      }
      setFarmerInputs(next);
    },
    [districts, farmerInputs, setFarmerInputs, setResult]
  );

  const handleOverrideChange = useCallback((name: string, raw: string) => {
    const meta = FEATURE_META_BY_NAME[name];
    if (!meta) return;

    setOverrides((prev) => {
      const next = { ...prev };
      if (raw === "") {
        delete next[name];
      } else {
        next[name] = Number(raw);
      }
      return next;
    });

    setOverrideErrors((prev) => {
      const next = { ...prev };
      if (raw === "") {
        delete next[name];
        return next;
      }
      const problem = validateOverride(meta, Number(raw));
      if (problem) {
        next[name] = tForm(problem.key, {
          min: problem.min,
          max: problem.max,
        });
      } else {
        delete next[name];
      }
      return next;
    });
  }, [tForm]);

  const handleReset = useCallback(() => {
    setOverrides({});
    setOverrideErrors({});
  }, []);

  const hasErrors = Object.keys(overrideErrors).length > 0;

  const isValid = useMemo(
    () => Boolean(district && season && !hasErrors),
    [district, season, hasErrors]
  );

  const handlePredict = async () => {
    if (!isValid) return;
    setLoading(true);
    setPredictError(null);

    try {
      // Send only what we actually know. The backend resolves the remaining
      // features from its per-district defaults and recomputes the interaction
      // terms, so nothing here can be silently zero-filled.
      const payload: Record<string, unknown> = {
        district,
        season,
        year,
        ...overrides,
      };

      const extent = Number(farmerInputs.extentHa);
      if (farmerInputs.extentHa !== "" && Number.isFinite(extent)) {
        payload.extent_prev_season = extent;
      }

      const lastYield = Number(farmerInputs.lastSeasonYield);
      if (farmerInputs.lastSeasonYield !== "" && Number.isFinite(lastYield)) {
        // The farmer's own recall of last harvest — the strongest signal they own.
        payload.prev_season_yield = lastYield;
        payload.prev_year_yield = lastYield;
      }

      const res = await predictYield(payload);
      setResult(res);
    } catch (error) {
      console.error("Prediction failed:", error);
      setPredictError(t("predict.error"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col space-y-2">
        <div className="inline-flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-emerald-600">
          <Sparkles size={16} />
          <span>{t("predict.eyebrow")}</span>
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 md:text-4xl">
          {t("predict.title")}
        </h1>
        <p className="max-w-2xl text-slate-500">{t("predict.subtitle")}</p>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        <section className="space-y-6 lg:col-span-7">
          <FieldInputCard
            value={farmerInputs}
            districts={districts}
            loading={contextLoading}
            onChange={handleFarmerChange}
          />

          <KnownDataPanel
            context={context}
            featureSources={result?.feature_sources}
            resolved={result?.resolved_features}
            overrides={overrides}
            loading={contextLoading}
            error={contextError}
          />

          <AdvancedOverrides
            enabled={advanced}
            onToggle={handleAdvancedToggle}
            context={context}
            overrides={overrides}
            errors={overrideErrors}
            onOverrideChange={handleOverrideChange}
            onReset={handleReset}
          />

          <button
            type="button"
            onClick={handlePredict}
            disabled={loading || !isValid}
            className="flex w-full items-center justify-center space-x-2 rounded-2xl bg-emerald-600 py-4 text-lg font-bold text-white shadow-lg transition-all hover:bg-emerald-700 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? (
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : (
              <>
                <Sprout size={24} />
                <span>{t("button.predict")}</span>
              </>
            )}
          </button>

          {hasErrors && (
            <p className="text-center text-sm font-medium text-red-600">
              {tForm("fixErrors")}
            </p>
          )}
        </section>

        <section className="space-y-6 lg:col-span-5">
          {predictError && (
            <div className="rounded-2xl border border-red-200 bg-red-50 p-5 text-sm font-medium text-red-700">
              {predictError}
            </div>
          )}

          {result ? (
            <PredictionResultCard
              result={result}
              baseline={baseline}
              locale={locale}
            />
          ) : (
            <div className="flex h-fit min-h-105 flex-col items-center justify-center rounded-3xl border-2 border-dashed border-slate-200 bg-slate-50 p-8 text-center">
              <div className="mb-4 rounded-2xl bg-emerald-100/60 p-4 text-emerald-700">
                <Info size={36} />
              </div>
              <h3 className="text-xl font-bold text-slate-900">
                {t("predict.waiting")}
              </h3>
              <p className="mt-2 max-w-xs text-sm text-slate-500">
                {t("predict.waitingDescription")}
              </p>
            </div>
          )}

          <ChatAssistant
            district={district}
            season={season}
            year={year}
            hasPrediction={Boolean(result)}
          />
        </section>
      </div>
    </div>
  );
}
