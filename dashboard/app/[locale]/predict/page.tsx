"use client";

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { Sprout, Info, Sparkles, RotateCcw } from "lucide-react";
import { useTranslations, useLocale } from "next-intl";

import {
  predictYield,
  getContext,
  getDistricts,
  getBaseline,
  TARGET_DISTRICTS,
  type PredictResponse,
  type ContextResponse,
  type BaselineResponse,
  type DistrictInfo,
} from "@/lib/api";
import { FEATURE_META_BY_NAME } from "@/lib/features";
import {
  useLocalFlag,
  useLocalJSONState,
  resetPrediction,
  PREDICTION_KEY,
  FARMER_INPUTS_KEY,
} from "@/lib/use-local-flag";
import FieldInputCard, { type FarmerInputs } from "@/components/FieldInputCard";
import KnownDataPanel from "@/components/KnownDataPanel";
import AdvancedOverrides, {
  validateOverride,
} from "@/components/AdvancedOverrides";
import PredictionResultCard from "@/components/PredictionResultCard";
import ChatAssistant from "@/components/ChatAssistant";

const ADVANCED_KEY = "agrisense_advanced_mode";

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

  // Read via a ref rather than a dependency: the seed effect below should
  // only re-seed when it actually needs to, not every time the persisted
  // inputs change (which would fight the farmer's own edits).
  const farmerInputsRef = useRef(farmerInputs);
  farmerInputsRef.current = farmerInputs;

  // Fetch the district catalog. Split from seeding (below) so a "New
  // Prediction" reset — which clears farmerInputs but doesn't need a fresh
  // fetch, since `districts` is already loaded — can re-trigger seeding on
  // its own without an extra network round-trip.
  //
  // The catalog is filtered down to TARGET_DISTRICTS rather than used as-is:
  // the backend's /districts list is DATA_VARIANT-dependent (synthetic data
  // has Jaffna, no Kurunegala; real data has Kurunegala, no Jaffna — see
  // src/data_loader.py), but this app only ever supports the 4 fixed target
  // districts. Passing the raw catalog through let "Jaffna" leak into the
  // dropdown and, via persisted form state, become the district actually
  // sent to /predict even when the farmer meant to pick Kurunegala. Any
  // target district missing its own catalog entry (e.g. Kurunegala under the
  // synthetic variant) still gets listed, backed by the dataset-wide
  // seasons/years — /predict resolves its features from broader averages in
  // that case, but the request still names the district the farmer picked.
  useEffect(() => {
    let active = true;

    getDistricts()
      .then((data) => {
        if (!active) return;
        const byName = new Map(data.districts.map((d) => [d.name, d]));
        const merged: DistrictInfo[] = TARGET_DISTRICTS.map(
          (name) =>
            byName.get(name) ?? {
              name,
              seasons: data.seasons,
              years: data.years,
            }
        );
        setDistricts(merged);
      })
      .catch(() => {
        if (active) setContextError(t("predict.districtsError"));
      });

    return () => {
      active = false;
    };
  }, [t]);

  // Seed the first valid district/season/year whenever the current selection
  // is empty or no longer valid for the loaded catalog — covers both the
  // first-ever load (nothing persisted yet) and a reset (which clears
  // farmerInputs back to blank), without duplicating this logic between the
  // two call sites.
  useEffect(() => {
    if (!districts.length) return;
    const current = farmerInputsRef.current;
    const stillValid = districts.some((d) => d.name === current.district);
    if (current.district && stillValid) return;

    const first = districts[0];
    // Current year, not the dataset's last recorded year (which for the
    // synthetic variant is 2023) — the farmer is predicting for now unless
    // they explicitly pick another year.
    const seeded = {
      ...current,
      district: first.name,
      // Yala is the only season this dashboard offers (Maha was retired) —
      // never seed from first.seasons[0], which could still be "Maha".
      season: "Yala",
      year: new Date().getFullYear(),
    };
    // TEMP DEBUG — remove once district/year propagation is verified.
    console.log("[Predict] seeding default district/season/year:", seeded);
    setFarmerInputs(seeded);
  }, [districts, storedFarmerInputs, setFarmerInputs]);

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
        // TEMP DEBUG — remove once district/year propagation is verified.
        console.log("[Predict] district selected:", patch.district);
        const info = districts.find((d) => d.name === patch.district);
        if (info) {
          // Yala is the only season this dashboard offers (Maha was
          // retired), so every district reconciles to it rather than
          // falling back to whatever info.seasons[0] happens to be.
          next.season = "Yala";
          const maxYear = info.years[info.years.length - 1];
          // Never clamp below the current year — a target district backed
          // only by dataset-wide averages (e.g. Kurunegala under the
          // synthetic variant, whose own years stop at 2023) would otherwise
          // silently reset the year the farmer is predicting for.
          const upperBound =
            maxYear !== undefined
              ? Math.max(maxYear + 2, new Date().getFullYear())
              : undefined;
          if (upperBound !== undefined && next.year > upperBound) {
            next.year = upperBound;
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

      // TEMP DEBUG — remove once district/year propagation is verified.
      console.log("[Predict] request payload:", payload);

      const res = await predictYield(payload);

      // TEMP DEBUG — remove once district/year propagation is verified.
      console.log("[Predict] response district:", res.district, "year:", res.year);

      // A full overwrite, not a merge — localStorage.setItem inside setResult
      // always replaces the previous value wholesale, so a re-predict can
      // never leave a stale SHAP value or field lingering from the last one.
      setResult(res);
    } catch (error) {
      console.error("Prediction failed:", error);
      setPredictError(t("predict.error"));
    } finally {
      setLoading(false);
    }
  };

  // "New Prediction": clears the shared prediction/SHAP state (which also
  // sends Explain/Recommendation back to their "run a prediction first"
  // placeholder, since they read the same key) and the form, but never the
  // locale — resetPrediction() only ever touches its own two keys. The
  // district/season/year seed effect above re-populates the form the moment
  // farmerInputs goes back to empty, using the catalog already in memory.
  const handleNewPrediction = useCallback(() => {
    resetPrediction();
    setPredictError(null);
    setOverrides({});
    setOverrideErrors({});
    setContext(null);
    setContextError(null);
    setBaseline(null);
  }, []);

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

          <div className="flex gap-3">
            {/* suppressHydrationWarning: this button is always rendered, so
                (unlike "New Prediction" below, gated on `result` which is
                `null` during hydration via useSyncExternalStore's server
                snapshot) it's exposed to autofill/password-manager browser
                extensions stamping fdprocessedid="..." onto it post-mount —
                see LanguageSwitcher.tsx/Navbar.tsx for the same,
                already-confirmed case. */}
            <button
              type="button"
              onClick={handlePredict}
              disabled={loading || !isValid}
              className="flex flex-1 items-center justify-center space-x-2 rounded-2xl bg-emerald-600 py-4 text-lg font-bold text-white shadow-lg transition-all hover:bg-emerald-700 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60"
              suppressHydrationWarning
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

            {result && (
              <button
                type="button"
                onClick={handleNewPrediction}
                className="flex items-center justify-center space-x-2 rounded-2xl border-2 border-slate-200 bg-white px-5 py-4 font-bold text-slate-600 transition-colors hover:border-slate-300 hover:bg-slate-50"
              >
                <RotateCcw size={20} />
                <span className="hidden sm:inline">{t("button.newPrediction")}</span>
              </button>
            )}
          </div>

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
