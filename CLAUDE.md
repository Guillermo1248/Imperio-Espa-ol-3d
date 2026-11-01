# Visor 3D — Imperio Español 1794

Contexto completo del proyecto para retomar el desarrollo en Claude Code.

---

## 🎯 Qué es este proyecto

Visor cartográfico 3D interactivo del **Imperio Español en 1794** (reinado de
Carlos IV, tras las Reformas Borbónicas). Construido con **CesiumJS 1.116**
sobre imágenes satelitales de Esri (sin token, sin terrain provider real).

Todo el código vive en un único archivo `index.html` (~1.500 líneas de HTML +
CSS + JS vanilla), sin frameworks ni bundlers.

---

## 📁 Estructura del proyecto

```
imperio-espanol-1794/
├── index.html                            ← todo el visor (HTML+CSS+JS)
├── server.py                             ← servidor HTTP local en puerto 8000
├── README.md
│
├── bandera.png                           ← bandera España 1785 (canvas ondeante)
├── plus ultra.png                        ← columnas Hércules originales (354×564)
├── columna_izquierda.png                 ← mitad izquierda (PLVS)
├── columna_derecha.png                   ← mitad derecha (VLTRA)
│
├── logo_hospitales.png                   ← 1408×768, para el menú (CSS crop)
├── logo_universidades.png                ← idem
├── logo_ciudades.png                     ← idem
├── pin_hospitales.png                    ← 200×200 pre-recortado transparente
├── pin_universidades.png                 ← idem, para billboards Cesium
├── pin_ciudades.png                      ← idem
│
├── galeon/
│   ├── scene.gltf                        ← modelo 3D del Galeón de Manila
│   ├── scene.bin
│   └── textures/
│
└── data/
    ├── imperio-espanol-1794.geojson      ← 33 polígonos de virreinatos
    ├── rutas.geojson                     ← 209 LineStrings expediciones
    ├── universidades.geojson             ← 75 Points
    ├── hospitales.geojson                ← 385 Points
    ├── ciudades_fundadas.geojson         ← 916 Points (formato Wikimedia con wrapper .data)
    └── ciudades_principales.geojson      ← 21 ciudades destacadas de 1794 (con descripciones)
```

---

## ▶️ Cómo ejecutar

**No abrir el HTML con doble clic** — los `fetch()` fallarán por CORS. Servir vía HTTP:

```bash
cd imperio-espanol-1794
python3 server.py
# abrir http://localhost:8000
```

Alternativa: extensión **Live Server** de VS Code → clic derecho en `index.html`
→ "Open with Live Server".

---

## 🗺️ Los 5 virreinatos representados

| Región               | Color        | Contenido                                                                                    |
|----------------------|--------------|----------------------------------------------------------------------------------------------|
| **Nueva España**     | `#d4a017`    | México→Centroamérica + Cuba + Sto. Domingo + PR + Filipinas + Marianas + Carolinas + Nutka   |
| **Nueva Granada**    | `#8a5fa0`    | Colombia + Venezuela + norte Ecuador + Margarita                                             |
| **Perú**             | `#c44848`    | MultiPolygon: Perú continental + Chile (oeste de -70° W)                                     |
| **Río de la Plata**  | `#4880b8`    | Argentina + Bolivia + Paraguay + Uruguay + Fernando Poo + Annobón + Guinea + Malvinas       |
| **Península Ibérica**| `#98681c`    | España + 7 Canarias + 4 Baleares + Ceuta + Melilla + Orán                                    |

Los polígonos se generaron con Sutherland-Hodgman sobre los límites históricos.

---

## 🌟 Las 5 capitales virreinales (hard-coded en JS)

```javascript
const CAPITALES = [
  { name: 'Madrid',             lng:  -3.7038, lat:  40.4168, desc: '...' },
  { name: 'Ciudad de México',   lng: -99.13,   lat:  19.43,   desc: '...' },
  { name: 'Lima',               lng: -77.04,   lat: -12.05,   desc: '...' },
  { name: 'Santa Fe de Bogotá', lng: -74.08,   lat:   4.71,   desc: '...' },
  { name: 'Buenos Aires',       lng: -58.38,   lat: -34.61,   desc: '...' }
];
```

Se renderizan como **estrellas doradas** generadas con `canvas` (dataURL) y se
integran como un `CustomDataSource` toggleable desde el menú.

---

## ⚙️ Configuración definitiva de marcadores

Tras muchas iteraciones (ver §"Historial de iteraciones" más abajo), esta es
la combinación óptima:

```javascript
// Setup del viewer
viewer.scene.globe.depthTestAgainstTerrain = false;
// → el elipsoide sólido oculta los pines del lado opuesto por curvatura,
//   sin que la malla del terreno se los trague.

// Posición: ABSOLUTA sobre la superficie real (terrainHeight × exageración + 5 m)
position: surfacePosition(lng, lat),

// Billboard de cada pin
billboard: {
  image: conf.billboardImage,          // pin_*.png (200×200 transparente)
  scale: 0.2,                          // 0.5 para las capitales
  verticalOrigin:  Cesium.VerticalOrigin.BOTTOM,
  distanceDisplayCondition: hideOnMoveDDC()            // ocultar al mover
}

// Label de cada pin
label: {
  text: props.title,
  font: '14px "Crimson Text", serif',
  fillColor:    Cesium.Color.WHITE,
  outlineColor: Cesium.Color.BLACK,
  outlineWidth: 2,
  style: Cesium.LabelStyle.FILL_AND_OUTLINE,
  verticalOrigin:  Cesium.VerticalOrigin.BOTTOM,
  pixelOffset: new Cesium.Cartesian2(0, -35),
  distanceDisplayCondition: hideOnMoveDDC(conf.labelMaxDistance)  // + LOD
}
```

`terrainHeight()` devuelve 0 con `EllipsoidTerrainProvider` (no hay terreno
real: la superficie es el elipsoide). Si se añade un terreno real, cambiar
`terrainHeight()` por alturas precalculadas con `sampleTerrainMostDetailed`.

**Prohibido usar**:
- ❌ `heightReference: CLAMP_TO_GROUND` en pines, labels o el galeón → muestrea la malla visible del globo, que a poco zoom queda por debajo del elipsoide (medido: hasta −43 km) → pines hundidos y saltando; en labels, cada letra muestrea por separado → congelones de ~2,6 s
- ❌ `disableDepthTestDistance: Number.POSITIVE_INFINITY` → produce efecto "rayos X" (pines de América visibles al mirar Filipinas atravesando la Tierra)
- ❌ `Cesium.GeoJsonDataSource.load()` → crea primitivas internas fantasma
- ❌ `eyeOffset` → hack innecesario con la config actual
- ❌ `scaleByDistance` → los pines cambian de tamaño de forma confusa

---

## 🎬 Sistemas clave que hay que preservar

### 1. Creación manual de entidades (NO usar GeoJsonDataSource.load)

```javascript
const ds = new Cesium.CustomDataSource(key);
features.forEach(feat => {
  if (feat.geometry.type === 'Point' && conf.billboardImage) {
    const [lng, lat] = feat.geometry.coordinates;
    const pointRegion = findRegionForPoint(lng, lat);
    ds.entities.add({
      position: Cesium.Cartesian3.fromDegrees(lng, lat, 0),
      billboard: { ... },
      label: { ... },
      properties: { ...feat.properties, region: pointRegion }
    });
  } else if (feat.geometry.type === 'LineString') {
    ds.entities.add({ polyline: { positions, clampToGround: true, ... } });
  }
});
ds.show = false;
viewer.dataSources.add(ds);
layerDataSources[key] = ds;
```

### 2. Fetch con extracción de wrapper `.data`

`ciudades_fundadas.geojson` viene del formato Wikimedia con la FeatureCollection
real anidada en `.data`. Helper defensivo:

```javascript
const fetchGeoJSON = url =>
  fetch(url)
    .then(r => r.json())
    .then(raw => (raw && raw.data && raw.data.type === 'FeatureCollection')
                  ? raw.data
                  : raw);
```

### 3. Point-in-polygon para filtrar pines por virreinato

Al cargar los polígonos se guarda cada anillo en `regionPolygons`. Cada pin
recibe `properties.region` calculado con ray-casting + bbox check:

```javascript
const regionPolygons = [];  // { region, ring, bbox }

function pointInPolygon(lng, lat, ring) { /* ray-casting */ }
function computeBbox(ring) { /* min/max lng-lat */ }
function findRegionForPoint(lng, lat) {
  for (const rp of regionPolygons) {
    if (lng < rp.bbox.minLng || lng > rp.bbox.maxLng) continue;
    if (lat < rp.bbox.minLat || lat > rp.bbox.maxLat) continue;
    if (pointInPolygon(lng, lat, rp.ring)) return rp.region;
  }
  return null;
}
```

`updateVisibility()` filtra polígonos Y pines simultáneamente según
`selectedFilters` del dropdown.

### 4. Sistema "ocultar al mover" (estilo Google Earth)

```javascript
let cameraMoveTimeout = null, cameraMoving = false;

// Un CallbackProperty compartido por maxDistance; DDC precreados (sin
// asignar objetos por frame). Oculta en GPU sin destruir billboards/labels.
function hideOnMoveDDC(maxDistance = Number.MAX_VALUE) { /* ... */
  return new Cesium.CallbackProperty(
    () => cameraMoving ? DDC_HIDDEN : visible, false);
}

viewer.scene.camera.moveStart.addEventListener(() => {
  clearTimeout(cameraMoveTimeout);
  cameraMoving = true;
});
viewer.scene.camera.moveEnd.addEventListener(() => {
  clearTimeout(cameraMoveTimeout);
  cameraMoveTimeout = setTimeout(() => {
    cameraMoving = false;
    viewer.scene.requestRender();
  }, 180);
});
```

**No volver a ocultar con `ds.show = false`** en este sistema: apagar un
DataSource devuelve los labels al pool y al reencenderlo Cesium reconstruye
los glifos de ~1.400 labels → congelón tras cada movimiento de cámara.
`ds.show` queda solo para el menú de capas (acción puntual del usuario).

**LOD de labels**: `labelMaxDistance` en `LAYERS` (ciudades y hospitales
1.500 km, universidades 5.000 km; capitales siempre). Los pines siempre
visibles; solo los nombres dependen de la distancia.

### 5. Galeón de Manila animado

Ruta transpacífica con 21 waypoints. Interpolación Hermite de grado 2 sobre
`SampledPositionProperty`. Como la interpolación es en XYZ, entre waypoints
se separaba del elipsoide (hasta ~18 km); se envuelve en un `CallbackProperty`
que proyecta cada posición al nivel del mar con `scaleToGeodeticSurface`.
Orientación calculada por `VelocityOrientationProperty` sobre esa posición.
La quilla del modelo está en su origen (Y = 0), así que altura 0 = flotando.

```javascript
const MODEL_URI = 'galeon/scene.gltf';

// Al pulsar el botón del evento:
galeonEntity = viewer.entities.add({
  position: seaLevelPosition,
  orientation: new Cesium.VelocityOrientationProperty(seaLevelPosition),
  model: {
    uri: MODEL_URI,
    scale: 1,
    minimumPixelSize: 80,
    maximumScale: 20000,
    runAnimations: false            // sin heightReference (ver Problema 6)
  }
});
```

`SEGMENT_SECONDS = 600`, `multiplier = 600`, `clockRange: LOOP_STOP`,
`start = 1794-01-01T00:00:00Z`. Sin `path` (sin estela) por decisión de diseño.

---

## 🖼️ Interfaz (UI)

### Encabezado central
`#titulo-imperio-container` en `top: 15px` centrado horizontalmente. Flexbox
con las dos mitades de las columnas de Hércules flanqueando el título
"IMPERIO ESPAÑOL". Fondo con gradiente que se desvanece en los bordes.

- Fuente "IMPERIO": Cinzel 14px, letter-spacing 7px, color `#c8a84b`
- Fuente "ESPAÑOL": Cinzel 34px con gradiente blanco→oro→bronce
- `pointer-events: none` para permitir clicks al mapa por debajo

### Bandera ondeante
`#flag-canvas` en `top: 18px left: 18px`. Canvas 2D 180×130 que renderiza
la bandera de España 1785 con doble onda senoidal + luz/sombra.

### Dropdown Virreinatos
`top: 24px right: 24px z-index: 110`. Multi-select con 5 opciones (los 5
virreinatos + Península). Marca `__NONE__` para ocultar todo. Sin selección
= mostrar todo.

### Menú de capas
`top: 84px right: 24px`. 5 items toggleables: rutas, capitales (★),
universidades, hospitales, ciudades. Cada uno con un `logo_*.png` como
CSS background (crop con `background-size: 230%`, `background-position: center 38%`).

### Panel de eventos (Galeón)
`top: 360px right: 24px`. Contiene botón "🚢 Ruta del Galeón de Manila" y
un botón "✕ Cerrar evento" que restaura el reloj original.

### Tooltip
Aparece con clic izquierdo (no hover) sobre cualquier entidad. `drillPick(10)`
para priorizar puntos/rutas sobre polígonos. Botón × para cerrar.

---

## 🏛️ Las columnas de Hércules

`plus ultra.png` (354×564 con transparencia) contiene ambas columnas + el lema
en una única composición. Duplicarla a cada lado del texto produciría 4
columnas y 2 lemas — por eso se partió en dos mitades con PIL:

```python
from PIL import Image
img = Image.open('plus ultra.png').convert('RGBA')
W, H = img.size
mid = W // 2
img.crop((0, 0, mid, H)).save('columna_izquierda.png')  # con "PLVS"
img.crop((mid, 0, W, H)).save('columna_derecha.png')     # con "VLTRA"
```

Se muestran con `height: 110px` en el encabezado central.

---

## 📚 Historial de iteraciones (contexto de por qué las decisiones son así)

### Problema 1: pines que "bailaban" al rotar la cámara

8 intentos sucesivos antes de dar con la solución:

| # | Diagnóstico incorrecto | Consecuencia |
|---|------------------------|--------------|
| 1 | Faltaba `heightReference` en billboards | Siguen bailando |
| 2 | Faltan las mismas props en labels | Siguen bailando |
| 3 | `GeoJsonDataSource.load` no pasa `clampToGround` | Siguen bailando |
| 4 | Cesium crea `entity.point` fantasma con `clampToGround:true` | Aparecen puntos duplicados |
| 5 | `markerSize/markerColor` activan PointPrimitiveCollection interna | Cambio a `CustomDataSource` manual |
| 6 | `CLAMP_TO_GROUND` recalcula posición cada frame → micro-jitter | Se quita `heightReference` |
| 7 | Posición absoluta + `disableDepthTestDistance: Infinity` → efecto rayos X | Se vuelve atrás |
| 8 | `depthTestAgainstTerrain = true` entierra pines en montañas | ✅ Final: `depthTestAgainstTerrain = false` |

**Solución de entonces**: `CLAMP_TO_GROUND` + `VerticalOrigin.BOTTOM` +
`depthTestAgainstTerrain = false` + sistema "ocultar al mover".
→ Sustituida en el Problema 6 (el clamp era la causa raíz).

### Problema 2: efecto "rayos X"

`disableDepthTestDistance: Number.POSITIVE_INFINITY` renderiza el billboard
SIEMPRE encima, sin importar la curvatura. Al mirar Filipinas se veían pines
de México "atravesando" el planeta.

**Solución**: eliminar completamente `disableDepthTestDistance` y usar
`viewer.scene.globe.depthTestAgainstTerrain = false` — el elipsoide sólido
hace el culling natural.

### Problema 3: pines enterrados en la malla del terreno

Se intentó `eyeOffset: new Cesium.Cartesian3(0, 0, -10000)` para "tirar" del
billboard hacia la cámara. Funcionaba pero era un hack. La solución definitiva
fue `depthTestAgainstTerrain = false` que evita el problema desde la raíz.

### Problema 4: pines de todas las regiones a la vez

Al activar una capa se veían pines por todo el imperio, saturando la vista.
**Solución**: filtrado point-in-polygon vinculando cada pin a su virreinato,
que se combina con el filtro del dropdown de virreinatos.

### Problema 5: Ciudades fundadas no aparecían

Dos causas:
1. `ciudades_fundadas.geojson` viene con wrapper `.data` de Wikimedia →
   helper de fetch con detección defensiva.
2. El item del menú "Ciudades" estaba tapado por `#events-panel` que se
   solapaba → se movió a `top: 360px`.

### Problema 6: lentitud con muchas capas + pines medio hundidos

Medido en el navegador (Cesium 1.116, `EllipsoidTerrainProvider`):
- `CLAMP_TO_GROUND` usa `globe.getHeight()` sobre la malla de tiles, que a
  poco zoom es una cuerda bajo el elipsoide: alturas de −16 m a −43.213 m
  en 400 ciudades → pines hundidos que "saltan" al refinarse los tiles
  (era la causa real del Problema 1).
- El "ocultar al mover" con `ds.show` reconstruía al reaparecer todos los
  labels, y con clamp cada letra muestreaba altura: frame de ~2.800 ms tras
  cada movimiento de cámara.

**Solución**: posición absoluta con `surfacePosition()` (altura real del
terreno = 0 + offset 5 m), "ocultar al mover" mediante `distanceDisplayCondition`
compartido, LOD de labels por distancia, galeón proyectado al nivel del mar.
Resultado: el frame tras mover la cámara baja a ~35–140 ms, todos los pines a +5 m.
Sin `disableDepthTestDistance` → no reaparece el efecto rayos X.

---

## 🎨 Paleta de colores

- Fondo oscuro paneles: `rgba(8, 6, 2, 0.92)`
- Dorado principal: `#c8a84b`
- Dorado oscuro: `#8a6e1a`
- Beige texto: `#e8d8a0` / `#f0d985`
- Bordes decorativos: `border-left: 3px solid #c8a84b`

## ✒️ Tipografías

- **Cinzel** (Google Fonts) → títulos, encabezados
- **Crimson Text** (Google Fonts) → labels del mapa, texto de cuerpo

---

## 📋 Convenciones al modificar el código

1. **Nunca añadir `disableDepthTestDistance` a ningún billboard/label**.
2. **Nunca usar `Cesium.GeoJsonDataSource.load()`** — siempre crear entidades
   manualmente con `ds.entities.add()`.
3. **Todos los billboards y labels** deben: posicionarse con
   `surfacePosition(lng, lat)`, usar `verticalOrigin: BOTTOM`, y NO llevar
   `heightReference` (nada de `CLAMP_TO_GROUND`) ni `disableDepthTestDistance`.
4. **Cualquier pin nuevo** debe calcular su región con `findRegionForPoint(lng, lat)`
   para integrarse en el sistema de filtrado.
5. **Cualquier capa nueva de puntos** debe añadirse a `POINT_LAYER_KEYS`
   (filtro por virreinato) y usar `distanceDisplayCondition: hideOnMoveDDC(...)`
   en billboard y label para participar en "ocultar al mover". Crear colores,
   offsets y DDC una vez por capa, no uno por pin.
6. **Preservar** el uso de `pin_*.png` (200×200 transparentes) para
   billboards y `logo_*.png` (1408×768) para CSS del menú.

---

## 🐛 Errores comunes al ejecutar

| Síntoma | Causa | Solución |
|---|---|---|
| Pantalla en negro sin cargar nada | Falta servidor HTTP | Usar `python3 server.py` o Live Server de VS Code |
| HTTP 404 en una capa GeoJSON | Falta un archivo en `data/` | Verificar carpeta completa |
| Galeón como bola gris | Modelo 3D no se carga | Verificar `galeon/scene.gltf` + `.bin` + `textures/` |
| Pines gigantes | Faltan `pin_*.png` | Verificar los 3 pin_*.png en la raíz |
| `POINT_LAYER_KEYS is not defined` | Versiones desincronizadas | Usar la última versión de `index.html` sin mezclar antiguas |
| Efecto rayos X | Alguien re-añadió `disableDepthTestDistance` | Eliminarlo de todos los billboards y labels |
| Pines bailando otra vez | Alguien re-añadió `depthTestAgainstTerrain = true` | Volver a `false` |
| Pines hundidos / congelón al soltar la cámara | Alguien re-añadió `CLAMP_TO_GROUND` o volvió a ocultar con `ds.show` | Ver Problema 6 |

---

## 🚀 Ideas de trabajo futuro (opcionales)

- Añadir más capas históricas (misiones, minas de plata, arsenales)
- Añadir línea temporal deslizable (1500-1900) que anime la evolución del imperio
- Panel lateral con biografías de los 4 virreyes en 1794
- Segunda ruta animada (Flota de Indias Cádiz→La Habana→Veracruz)
- Modo "vista del Rey" con cámara cinemática que gira por todos los virreinatos
- Exportar el visor como PWA para funcionar offline
