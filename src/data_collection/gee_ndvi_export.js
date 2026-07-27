/**
 * MODIS MOD13Q1 NDVI/EVI export for the four modelled districts, 2000-2025.
 *
 * WHY RE-EXPORT
 * The existing `FYP data(manual) - NDVI-EVI.csv` covers Anuradhapura, Hambantota,
 * Jaffna, Matale, Monaragala and Polonnaruwa — but NOT Kurunegala, which is one of
 * the four districts we actually model. It also carries three districts we never use.
 * PADR indexes weather by an NDVI-derived phenological time axis, so a missing district
 * means that district falls back to a calendar window and loses the novelty entirely.
 *
 * MODIS NDVI is 250 m / 16-day. That resolution matters here: NASA POWER puts
 * Kurunegala and Matale in ONE grid cell with byte-identical daily weather, so NDVI is
 * the only input that can still tell those two districts apart.
 *
 * HOW TO RUN
 *   1. Open https://code.earthengine.google.com  (sign in with your EE-registered account)
 *   2. Paste this whole file into a new script and press Run
 *   3. Go to the Tasks tab, click Run on `modis_ndvi_evi_districts`
 *   4. It lands in your Google Drive as MODIS_NDVI_EVI_districts.csv
 *   5. Save it to  data/collected/modis_ndvi_evi_districts.csv
 *
 * OUTPUT SCHEMA (matches the existing export so downstream code accepts either)
 *   Date (YYYY-MM-DD), District, NDVI, EVI, Year, Month, n_pixels
 *
 * NOTE ON SCALING: MOD13Q1 stores NDVI/EVI as int16 scaled by 10000. This script
 * divides by 10000, so the CSV holds real -1..1 values — do NOT rescale again.
 * Pixels failing the SummaryQA check are dropped before the mean is taken.
 */

var DISTRICTS = ['Anuradhapura', 'Kurunegala', 'Matale', 'Polonnaruwa'];
var START = '2000-01-01';
var END   = '2025-12-31';

// FAO GAUL level 2 = administrative districts. Sri Lanka's ADM2 names match DCS spelling.
var adm = ee.FeatureCollection('FAO/GAUL/2015/level2')
            .filter(ee.Filter.eq('ADM0_NAME', 'Sri Lanka'))
            .filter(ee.Filter.inList('ADM2_NAME', DISTRICTS));

print('Districts matched (expect 4):', adm.size(), adm.aggregate_array('ADM2_NAME'));
Map.addLayer(adm, {color: 'red'}, 'target districts');
Map.centerObject(adm, 8);

var modis = ee.ImageCollection('MODIS/061/MOD13Q1').filterDate(START, END);

/**
 * Keep only good-quality pixels. SummaryQA: 0 = good, 1 = marginal, 2 = snow/ice,
 * 3 = cloudy. We accept 0 and 1 — dropping marginal too would thin the wet-season
 * record badly, which is exactly the part of the phenology curve we need.
 */
function maskQuality(img) {
  var qa = img.select('SummaryQA');
  var ok = qa.lte(1);
  return img.select(['NDVI', 'EVI'])
            .divide(10000)          // int16 -> real reflectance index
            .updateMask(ok)
            .copyProperties(img, ['system:time_start']);
}

var clean = modis.map(maskQuality);

// One row per (composite date x district): spatial mean over the district polygon.
var rows = clean.map(function (img) {
  var date = ee.Date(img.get('system:time_start'));
  var stats = img.reduceRegions({
    collection: adm,
    reducer: ee.Reducer.mean().combine({reducer2: ee.Reducer.count(), sharedInputs: false}),
    scale: 250,
    tileScale: 4
  });
  return stats.map(function (f) {
    return ee.Feature(null, {
      Date:      date.format('YYYY-MM-dd'),
      District:  f.get('ADM2_NAME'),
      NDVI:      f.get('NDVI_mean'),
      EVI:       f.get('EVI_mean'),
      Year:      date.get('year'),
      Month:     date.get('month'),
      n_pixels:  f.get('NDVI_count')
    });
  });
}).flatten();

// Composites fully masked by cloud produce null means — drop them rather than
// exporting nulls that would silently become 0.0 on the pandas side.
rows = rows.filter(ee.Filter.notNull(['NDVI', 'EVI']));

print('Sample rows:', rows.limit(5));

Export.table.toDrive({
  collection: rows,
  description: 'modis_ndvi_evi_districts',
  fileNamePrefix: 'MODIS_NDVI_EVI_districts',
  fileFormat: 'CSV',
  selectors: ['Date', 'District', 'NDVI', 'EVI', 'Year', 'Month', 'n_pixels']
});
