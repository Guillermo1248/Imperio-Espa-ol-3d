# Imperio Español 1794 — Visor 3D Interactivo

Globo interactivo del Imperio Español tras las Reformas Borbónicas, con los **4 virreinatos americanos**, la **Capitanía General de Filipinas** y la **Península Ibérica**.

Cada región puede verse en dos modos:
- **Unificada**: el virreinato como un único bloque coloreado
- **Dividida**: sus subdivisiones administrativas internas (intendencias, provincias, capitanías, reinos)

---

## Estructura

```
imperio-espanol-1794/
├── index.html                           Visor Cesium + menú de regiones
├── data/
│   └── imperio-espanol-1794.geojson     73 features en 5 regiones
├── server.py                            Servidor HTTP local
└── README.md
```

---

## Cómo ejecutarlo

⚠️ Cesium NO funciona con `file://` por restricciones CORS. Necesitas un servidor HTTP local:

```bash
cd imperio-espanol-1794
python3 server.py
```

Se abrirá `http://localhost:8000` automáticamente.

---

## Cómo se usa

1. **Vista inicial**: las 5 regiones aparecen como bloques unificados, cada una con su color distintivo.
2. **Menú lateral derecho**: lista de las 5 regiones del Imperio.
3. **Clic en una región** (ya sea en el menú o sobre el mapa) → se expande, mostrando sus subdivisiones internas con bordes dorados y colores individuales. La cámara vuela hacia ella.
4. **Clic de nuevo en la misma región** → se colapsa, vuelve al modo unificado.
5. **Clic en una subdivisión** (con la región expandida) → la cámara vuela hasta ese territorio concreto.
6. **Botón "↺ Vista global"** → revierte todo y zoom out al planeta.

Solo una región puede estar expandida a la vez. Al activar otra, la anterior se colapsa automáticamente.

---

## Regiones y subdivisiones (73 features)

### 🟡 Virreinato de Nueva España — 32 subdivisiones
- **9 Provincias Internas**: Alta y Baja California, Sonora-Sinaloa, Nueva Vizcaya, Nuevo México, Coahuila, Texas, Nuevo Reino de León, Nuevo Santander
- **9 Intendencias del Reino**: México, Puebla, Veracruz, Oaxaca, Valladolid, Guadalajara, Zacatecas, Guanajuato, San Luis Potosí
- **Capitanía General de Yucatán**
- **6 jurisdicciones de la Capitanía General de Guatemala**: Chiapas, Guatemala, San Salvador, Comayagua (Honduras), León (Nicaragua), Costa Rica
- **6 jurisdicciones de la Capitanía General de Cuba**: Cuba, Luisiana, Florida Occidental, Florida Oriental, Santo Domingo, Puerto Rico
- **Capitanía General de Filipinas** (Luzón, Mindanao, Visayas, Batanes)

### 🔴 Virreinato del Perú — 8 subdivisiones
Intendencias de Trujillo, Lima, Tarma, Huancavelica, Huamanga, Cuzco, Arequipa + Capitanía General de Chile.

### 🟣 Virreinato de Nueva Granada — 10 subdivisiones
Provincias de Cartagena, Santa Marta, Antioquia-Chocó, Popayán, Santa Fe de Bogotá, Panamá + Audiencia de Quito + Gobernación de Maynas + Capitanía General de Venezuela + Provincia de Maracaibo.

### 🔵 Virreinato del Río de la Plata — 9 subdivisiones
Intendencias de Buenos Aires, Paraguay, Córdoba del Tucumán, Salta del Tucumán, Cochabamba, Charcas, La Paz, Potosí, Puno.

### 🟤 Península Ibérica — 14 reinos y provincias
Galicia, Asturias, Provincias Vascongadas, Navarra, Aragón, Cataluña, Valencia, Murcia, León, Castilla la Vieja, Castilla la Nueva, Extremadura, Andalucía, Mallorca (con Menorca e Ibiza).

---

## Esquema de propiedades del GeoJSON

```json
{
  "region": "Nueva España",          // Región top-level (1 de 5)
  "name": "Intendencia de Puebla",   // Nombre de la subdivisión
  "type": "Intendencia",             // Intendencia | Provincia | Capitanía General | Audiencia | Reino...
  "parent": "Reino de Nueva España", // Jurisdicción superior inmediata
  "color": "#f4c8a8",                // Color en modo dividido
  "desc": "Capital: Puebla..."       // Descripción para el tooltip
}
```

El campo **`region`** controla a qué grupo pertenece la subdivisión y, por tanto, qué color unificado se le aplica al colapsar.

---

## ⚠️ Sobre la precisión cartográfica

Las coordenadas son **aproximaciones** basadas en:
1. Correspondencia con divisiones modernas (estados, departamentos, provincias)
2. Fronteras naturales históricas (ríos Bravo, Sabine, Misisipi, Miño, Duero…)
3. Paralelos políticos documentados (31°N, 42°N en América; frontera con Portugal)

**Limitaciones conocidas**:
- Los polígonos están simplificados (6–15 puntos por región)
- Los bordes entre intendencias internas son aproximados
- Portugal queda excluido como reino independiente desde 1640
- Andorra y Gibraltar (británico desde 1713) no se representan

Para precisión académica, ver:
- Peter Gerhard, *A Guide to the Historical Geography of New Spain* (1972)
- Áurea Commons, *Las intendencias de la Nueva España* (UNAM, 1993)
- John Lynch, *Bourbon Spain 1700–1808* (Blackwell, 1989)
- Atlas Histórico de Mesoamérica, INAH

---

## Cambiar el dataset

El renderizado es totalmente **agnóstico al contenido del GeoJSON**. Para usar datos académicos:

1. Reemplaza `data/imperio-espanol-1794.geojson`.
2. Asegúrate de que cada `Feature` tenga las propiedades: `region`, `name`, `type`, `parent`, `color`, `desc`.
3. Ajusta el objeto `REGIONS` en `index.html` si añades regiones nuevas (define color unificado y posición de cámara).

---

## Créditos

- **CesiumJS** 1.116 — motor 3D (Apache 2.0)
- **Esri World Imagery** — capa base satelital
- **Datos** — reconstrucción aproximada para fines didácticos (dominio público)
