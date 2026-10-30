/* Shared satellite basemap and lazy loader. */
let mapLibraryPromise;
const MAPLIBRE_VERSION = "5.15.0";
const MAPLIBRE_JS = `https://unpkg.com/maplibre-gl@${MAPLIBRE_VERSION}/dist/maplibre-gl.js`;
const MAPLIBRE_CSS = `https://unpkg.com/maplibre-gl@${MAPLIBRE_VERSION}/dist/maplibre-gl.css`;
// Browser-visible, referrer-restricted map key comes from runtime configuration.
// Never place account credentials or private application secrets here.
function satelliteMapStyle(apiKey, {labels = false} = {}) {
  if (typeof apiKey !== "string" || !apiKey.trim()) throw new Error("Satellite maps are not configured.");
  const token = encodeURIComponent(apiKey);
  const style = {
    version: 8,
    sources: {
      "world-imagery": {
        type: "raster",
        tiles: [`https://ibasemaps-api.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}?token=${token}`],
        tileSize: 256, maxzoom: 23,
        attribution: 'Powered by <a href="https://www.esri.com/" target="_blank" rel="noopener">Esri</a> &mdash; Esri, Vantor, GeoEye, Earthstar Geographics, CNES/Airbus DS, USDA, USGS, AeroGRID, IGN, and the GIS User Community',
      },
      "imagery-labels": {
        type: "raster",
        tiles: [`https://static-map-tiles-api.arcgis.com/arcgis/rest/services/static-basemap-tiles-service/v1/arcgis/imagery/labels/static/tile/{z}/{y}/{x}?token=${token}`],
        tileSize: 512, maxzoom: 22,
        attribution: 'Esri, TomTom, Garmin, FAO, NOAA, USGS, &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap contributors</a>, and the GIS User Community',
      },
    },
    layers: [
      {id: "world-imagery", type: "raster", source: "world-imagery"},
      {id: "imagery-labels", type: "raster", source: "imagery-labels"},
    ],
  };
  // Static label tiles require their own ArcGIS Location Platform privilege.
  // Keep imagery available without making unauthorized label-tile requests.
  if (!labels) {
    delete style.sources["imagery-labels"];
    style.layers = style.layers.filter(layer => layer.id !== "imagery-labels");
  }
  return style;
}
function loadMapLibrary() {
  if (window.maplibregl) return Promise.resolve(window.maplibregl);
  if (mapLibraryPromise) return mapLibraryPromise;
  mapLibraryPromise = new Promise((resolve, reject) => {
    if (!document.querySelector(`link[href="${MAPLIBRE_CSS}"]`)) {
      const link = document.createElement("link");
      link.rel = "stylesheet"; link.href = MAPLIBRE_CSS;
      document.head.appendChild(link);
    }
    const script = document.createElement("script");
    script.src = MAPLIBRE_JS; script.async = true;
    script.onload = () => resolve(window.maplibregl);
    script.onerror = () => reject(new Error("The map library could not load."));
    document.head.appendChild(script);
  });
  return mapLibraryPromise;
}

