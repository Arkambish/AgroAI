/**
 * Metadata for the 32 model features.
 *
 * A farmer cannot supply NDVI, EVI, clay % or solar radiation — those are
 * MODIS, SoilGrids and NASA POWER products. Rather than asking for them, the
 * dashboard shows them read-only with their provenance, and lets an extension
 * officer override them behind the Advanced toggle.
 *
 * Order and names mirror src/config.py ALL_FEATURES exactly.
 */

export type FeatureGroupKey =
  | "weather"
  | "satellite"
  | "historical"
  | "soil"
  | "interaction";

export interface FeatureMeta {
  /** Model feature name — must match src/config.py */
  name: string;
  /** i18n key suffix under `features.*` */
  labelKey: string;
  unit?: string;
  decimals: number;
  /** Editable in Advanced / Officer mode */
  editable?: boolean;
  min?: number;
  max?: number;
  step?: number;
}

export interface FeatureGroup {
  key: FeatureGroupKey;
  /** i18n key suffix under `featureGroups.*` */
  labelKey: string;
  /** Where the data physically comes from — shown as a badge */
  sourceBadge: string;
  features: FeatureMeta[];
}

export const FEATURE_GROUPS: FeatureGroup[] = [
  {
    key: "weather",
    labelKey: "weather",
    sourceBadge: "NASA POWER",
    features: [
      { name: "season_avg_temp", labelKey: "season_avg_temp", unit: "°C", decimals: 1, editable: true, min: 10, max: 50, step: 0.1 },
      { name: "season_total_rainfall", labelKey: "season_total_rainfall", unit: "mm", decimals: 0, editable: true, min: 0, max: 2000, step: 1 },
      { name: "season_avg_humidity", labelKey: "season_avg_humidity", unit: "%", decimals: 1, editable: true, min: 0, max: 100, step: 1 },
      { name: "season_avg_solar_rad", labelKey: "season_avg_solar_rad", unit: "MJ/m²", decimals: 1, editable: true, min: 0, max: 40, step: 0.1 },
      { name: "growing_degree_days", labelKey: "growing_degree_days", unit: "°C·d", decimals: 0 },
      { name: "heat_stress_days", labelKey: "heat_stress_days", unit: "d", decimals: 0 },
      { name: "drought_index_spi", labelKey: "drought_index_spi", decimals: 2 },
      { name: "temp_range", labelKey: "temp_range", unit: "°C", decimals: 1 },
      { name: "max_daily_rainfall", labelKey: "max_daily_rainfall", unit: "mm", decimals: 1 },
    ],
  },
  {
    key: "satellite",
    labelKey: "satellite",
    sourceBadge: "MODIS / Sentinel-2",
    features: [
      { name: "season_mean_ndvi", labelKey: "season_mean_ndvi", decimals: 3, editable: true, min: -1, max: 1, step: 0.01 },
      { name: "season_max_ndvi", labelKey: "season_max_ndvi", decimals: 3 },
      { name: "season_min_ndvi", labelKey: "season_min_ndvi", decimals: 3 },
      { name: "ndvi_std", labelKey: "ndvi_std", decimals: 3 },
      { name: "ndvi_anomaly", labelKey: "ndvi_anomaly", decimals: 3 },
      { name: "time_to_peak_ndvi", labelKey: "time_to_peak_ndvi", unit: "d", decimals: 0 },
      { name: "ndvi_growth_rate", labelKey: "ndvi_growth_rate", decimals: 4 },
      { name: "season_mean_evi", labelKey: "season_mean_evi", decimals: 3, editable: true, min: -1, max: 1, step: 0.01 },
      { name: "season_mean_ndwi", labelKey: "season_mean_ndwi", decimals: 3 },
      { name: "season_mean_lst_day", labelKey: "season_mean_lst_day", unit: "°C", decimals: 1 },
      { name: "season_mean_lst_night", labelKey: "season_mean_lst_night", unit: "°C", decimals: 1 },
    ],
  },
  {
    key: "historical",
    labelKey: "historical",
    sourceBadge: "DCS records",
    features: [
      { name: "prev_season_yield", labelKey: "prev_season_yield", unit: "MT/Ha", decimals: 2 },
      { name: "prev_year_yield", labelKey: "prev_year_yield", unit: "MT/Ha", decimals: 2 },
      { name: "yield_3yr_avg", labelKey: "yield_3yr_avg", unit: "MT/Ha", decimals: 2 },
      { name: "season_indicator", labelKey: "season_indicator", decimals: 0 },
      { name: "extent_prev_season", labelKey: "extent_prev_season", unit: "ha", decimals: 1 },
    ],
  },
  {
    key: "soil",
    labelKey: "soil",
    sourceBadge: "SoilGrids",
    features: [
      { name: "soil_ph", labelKey: "soil_ph", decimals: 1, editable: true, min: 3, max: 10, step: 0.1 },
      { name: "organic_carbon", labelKey: "organic_carbon", unit: "%", decimals: 2, editable: true, min: 0, max: 20, step: 0.1 },
      { name: "clay_pct", labelKey: "clay_pct", unit: "%", decimals: 1, editable: true, min: 0, max: 100, step: 0.1 },
      { name: "sand_pct", labelKey: "sand_pct", unit: "%", decimals: 1, editable: true, min: 0, max: 100, step: 0.1 },
    ],
  },
  {
    key: "interaction",
    labelKey: "interaction",
    sourceBadge: "Derived",
    features: [
      { name: "rainfall_x_ndvi", labelKey: "rainfall_x_ndvi", decimals: 1 },
      { name: "temp_x_humidity", labelKey: "temp_x_humidity", decimals: 1 },
      { name: "ndvi_x_lst", labelKey: "ndvi_x_lst", decimals: 2 },
    ],
  },
];

export const ALL_FEATURE_META: FeatureMeta[] = FEATURE_GROUPS.flatMap(
  (g) => g.features
);

export const EDITABLE_FEATURES: FeatureMeta[] = ALL_FEATURE_META.filter(
  (f) => f.editable
);

export const FEATURE_META_BY_NAME: Record<string, FeatureMeta> =
  Object.fromEntries(ALL_FEATURE_META.map((f) => [f.name, f]));

/**
 * Where a resolved feature value came from. Mirrors the `feature_sources`
 * dict returned by POST /predict in src/api.py.
 */
export type FeatureSource =
  | "user"
  | "exact_year_record"
  | "district_season_mean"
  | "district_mean"
  | "season_mean"
  | "global_mean"
  | "derived"
  | "zero_fallback";

/** Tailwind classes per provenance tier — greener means better grounded. */
export const SOURCE_STYLES: Record<FeatureSource, string> = {
  user: "bg-emerald-100 text-emerald-800",
  exact_year_record: "bg-teal-100 text-teal-800",
  district_season_mean: "bg-sky-100 text-sky-800",
  district_mean: "bg-sky-100 text-sky-800",
  season_mean: "bg-amber-100 text-amber-800",
  global_mean: "bg-amber-100 text-amber-800",
  derived: "bg-slate-100 text-slate-600",
  zero_fallback: "bg-red-100 text-red-800",
};

export function formatFeatureValue(
  value: number | undefined,
  meta: FeatureMeta
): string {
  if (value === undefined || value === null || Number.isNaN(value)) return "—";
  return `${value.toFixed(meta.decimals)}${meta.unit ? ` ${meta.unit}` : ""}`;
}
