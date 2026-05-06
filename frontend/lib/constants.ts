// Mirror of src/config.py — keep these lists in sync if Python changes.

import type { District, Season } from "./types";

export const DISTRICTS: District[] = ["Matale", "Anuradhapura", "Polonnaruwa", "Jaffna"];
export const SEASONS: Season[] = ["Yala", "Maha"];

// Approximate centroids for the four target districts (lat, lng).
export const DISTRICT_CENTROIDS: Record<District, [number, number]> = {
  Matale: [7.4675, 80.6234],
  Anuradhapura: [8.3114, 80.4037],
  Polonnaruwa: [7.9403, 81.0188],
  Jaffna: [9.6615, 80.0255],
};

// 32 ALL_FEATURES from src/config.py, grouped for the prediction form tabs.
export const FEATURE_GROUPS = {
  Weather: [
    "season_avg_temp",
    "season_total_rainfall",
    "season_avg_humidity",
    "season_avg_solar_rad",
    "growing_degree_days",
    "heat_stress_days",
    "drought_index_spi",
    "temp_range",
    "max_daily_rainfall",
  ],
  Satellite: [
    "season_mean_ndvi",
    "season_max_ndvi",
    "season_min_ndvi",
    "ndvi_std",
    "ndvi_anomaly",
    "time_to_peak_ndvi",
    "ndvi_growth_rate",
    "season_mean_evi",
    "season_mean_ndwi",
    "season_mean_lst_day",
    "season_mean_lst_night",
  ],
  Historical: [
    "prev_season_yield",
    "prev_year_yield",
    "yield_3yr_avg",
    "season_indicator",
    "extent_prev_season",
  ],
  Soil: ["soil_ph", "organic_carbon", "clay_pct", "sand_pct"],
  Interaction: ["rainfall_x_ndvi", "temp_x_humidity", "ndvi_x_lst"],
} as const satisfies Record<string, readonly string[]>;

export const ALL_FEATURES: string[] = Object.values(FEATURE_GROUPS).flat();

// Human-friendly labels and units for form fields.
export const FEATURE_META: Record<string, { label: string; unit?: string; help?: string }> = {
  season_avg_temp: { label: "Average temperature", unit: "°C" },
  season_total_rainfall: { label: "Total rainfall", unit: "mm" },
  season_avg_humidity: { label: "Average humidity", unit: "%" },
  season_avg_solar_rad: { label: "Solar radiation", unit: "MJ/m²/day" },
  growing_degree_days: { label: "Growing degree days", unit: "°C·days" },
  heat_stress_days: { label: "Heat-stress days", unit: "days" },
  drought_index_spi: { label: "Drought index (SPI)", help: "Standardised precipitation index" },
  temp_range: { label: "Diurnal temperature range", unit: "°C" },
  max_daily_rainfall: { label: "Max daily rainfall", unit: "mm" },
  season_mean_ndvi: { label: "Mean NDVI", help: "0–1, higher = greener" },
  season_max_ndvi: { label: "Max NDVI" },
  season_min_ndvi: { label: "Min NDVI" },
  ndvi_std: { label: "NDVI std. dev." },
  ndvi_anomaly: { label: "NDVI anomaly", help: "vs. long-term mean" },
  time_to_peak_ndvi: { label: "Time to peak NDVI", unit: "days" },
  ndvi_growth_rate: { label: "NDVI growth rate", unit: "/day" },
  season_mean_evi: { label: "Mean EVI" },
  season_mean_ndwi: { label: "Mean NDWI", help: "Water index" },
  season_mean_lst_day: { label: "LST day", unit: "°C" },
  season_mean_lst_night: { label: "LST night", unit: "°C" },
  prev_season_yield: { label: "Previous-season yield", unit: "MT/Ha" },
  prev_year_yield: { label: "Previous-year yield", unit: "MT/Ha" },
  yield_3yr_avg: { label: "3-year mean yield", unit: "MT/Ha" },
  season_indicator: { label: "Season indicator", help: "Yala = 1, Maha = 0" },
  extent_prev_season: { label: "Extent (prev. season)", unit: "ha" },
  soil_ph: { label: "Soil pH" },
  organic_carbon: { label: "Organic carbon", unit: "%" },
  clay_pct: { label: "Clay", unit: "%" },
  sand_pct: { label: "Sand", unit: "%" },
  rainfall_x_ndvi: { label: "Rainfall × NDVI", help: "Interaction term" },
  temp_x_humidity: { label: "Temperature × humidity", help: "Interaction term" },
  ndvi_x_lst: { label: "NDVI × LST", help: "Interaction term" },
};

export const TARGET_R2 = 0.75;
