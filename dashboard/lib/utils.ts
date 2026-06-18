export function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

export function formatNumber(value: number, decimals = 2) {
  return Number(value).toFixed(decimals);
}