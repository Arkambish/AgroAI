"use client";

import { useEffect } from "react";
import { useMap } from "react-leaflet";

/**
 * The map's container height now tracks its sibling column (see
 * DistrictMap.tsx), so it can change after Leaflet's initial layout — e.g.
 * once the "Selected District Details" card swaps in and grows the left
 * column. Leaflet doesn't observe CSS-driven size changes on its own, so
 * without this the tile layer stays clipped/offset until a manual window
 * resize.
 */
export default function MapResizeHandler() {
  const map = useMap();

  useEffect(() => {
    const container = map.getContainer();
    const observer = new ResizeObserver(() => {
      map.invalidateSize();
    });
    observer.observe(container);

    return () => observer.disconnect();
  }, [map]);

  return null;
}
