// =====================================================================
// FloatTime MT — river & section database
//
// Each river is tied to a USGS gauge. Float speed is estimated with a
// hydraulic-geometry relationship:  v = refSpeedMph * (Q / refFlowCfs)^0.34
// refSpeedMph is the typical drift speed of a raft at refFlowCfs.
// Mileages are approximate river miles between access points.
// =====================================================================

const RIVERS = [
  {
    id: "madison-lower",
    name: "Madison River (Lower)",
    gauge: "06041000",
    gaugeName: "Madison bl Ennis Lake nr McAllister",
    lat: 45.487, lon: -111.633,
    refFlowCfs: 1100, refSpeedMph: 3.4,
    blurb: "Bozeman's classic summer float. Warm water, easy current, big crowds on hot weekends.",
    sections: [
      { id: "warm-springs-blacks-ford", putIn: "Warm Springs", takeOut: "Black's Ford", miles: 7.0, difficulty: "Class I", notes: "The beer-can hatch. Watch for shallow gravel bars in late summer." },
      { id: "blacks-ford-greycliff", putIn: "Black's Ford", takeOut: "Greycliff", miles: 9.0, difficulty: "Class I", notes: "Quieter than the upper stretch, good wade-fishing pullouts." },
    ],
  },
  {
    id: "yellowstone-paradise",
    name: "Yellowstone River (Paradise Valley)",
    gauge: "06192500",
    gaugeName: "Yellowstone near Livingston",
    lat: 45.596, lon: -110.566,
    refFlowCfs: 2500, refSpeedMph: 4.2,
    blurb: "Big, fast freestone water under the Absarokas. Moves quicker than it looks.",
    sections: [
      { id: "pine-creek-carters", putIn: "Pine Creek", takeOut: "Carter's Bridge", miles: 10.0, difficulty: "Class I–II", notes: "Braided channels shift every runoff — scout side channels." },
      { id: "carters-mayors", putIn: "Carter's Bridge", takeOut: "Mayor's Landing", miles: 5.0, difficulty: "Class I", notes: "Short town float through Livingston." },
      { id: "mayors-sheep-mtn", putIn: "Mayor's Landing", takeOut: "Sheep Mountain", miles: 9.0, difficulty: "Class I", notes: "Wind can howl through here in the afternoon." },
    ],
  },
  {
    id: "yellowstone-upper",
    name: "Yellowstone River (Gardiner)",
    gauge: "06191500",
    gaugeName: "Yellowstone at Corwin Springs",
    lat: 45.112, lon: -110.794,
    refFlowCfs: 2200, refSpeedMph: 4.5,
    blurb: "Whitewater stretch out of the Park boundary. Rafts and experienced paddlers.",
    sections: [
      { id: "gardiner-corwin", putIn: "Gardiner (Queen of the Waters)", takeOut: "Corwin Springs", miles: 8.0, difficulty: "Class II–III", notes: "Continuous wave trains at higher flows. Not a tube float." },
      { id: "corwin-yankee-jim", putIn: "Corwin Springs", takeOut: "Carbella (below Yankee Jim Canyon)", miles: 7.0, difficulty: "Class III", notes: "Yankee Jim Canyon — Boat Eater rapid. Scout or go with a guide." },
    ],
  },
  {
    id: "blackfoot",
    name: "Blackfoot River",
    gauge: "12340000",
    gaugeName: "Blackfoot near Bonner",
    lat: 46.896, lon: -113.757,
    refFlowCfs: 1200, refSpeedMph: 3.3,
    blurb: "A River Runs Through It water. Clear pools, ledge rock, and a famous recreation corridor.",
    sections: [
      { id: "roundup-johnsrud", putIn: "Roundup Bridge", takeOut: "Johnsrud Park", miles: 10.0, difficulty: "Class I–II", notes: "Ledges and boulder gardens; lively at runoff flows." },
      { id: "johnsrud-weigh-station", putIn: "Johnsrud Park", takeOut: "Weigh Station (Bonner)", miles: 8.0, difficulty: "Class I–II", notes: "The classic Missoula hot-day float. Thibodeau Rapid midway." },
    ],
  },
  {
    id: "clark-fork",
    name: "Clark Fork River (Missoula)",
    gauge: "12340500",
    gaugeName: "Clark Fork above Missoula",
    lat: 46.87, lon: -113.937,
    refFlowCfs: 2500, refSpeedMph: 3.5,
    blurb: "Float straight through downtown Missoula and wave at Brennan's Wave surfers.",
    sections: [
      { id: "sharon-caras", putIn: "Sha-Ron (East Missoula)", takeOut: "Caras Park", miles: 6.0, difficulty: "Class I–II", notes: "Brennan's Wave is at the Caras Park takeout — exit river right above it if unsure." },
      { id: "caras-kelly-island", putIn: "Caras Park", takeOut: "Kelly Island", miles: 5.0, difficulty: "Class I", notes: "Mellow water below town, braided channels near Kelly Island." },
    ],
  },
  {
    id: "bitterroot",
    name: "Bitterroot River",
    gauge: "12352500",
    gaugeName: "Bitterroot near Missoula",
    lat: 46.78, lon: -114.09,
    refFlowCfs: 1000, refSpeedMph: 3.0,
    blurb: "Gentle valley float with Bitterroot peaks for a backdrop. Infamous for shifting logjams.",
    sections: [
      { id: "bell-crossing-stevi", putIn: "Bell Crossing", takeOut: "Stevensville Bridge", miles: 7.0, difficulty: "Class I", notes: "Channels braid and wood moves every year — heads-up floating." },
      { id: "stevi-florence", putIn: "Stevensville Bridge", takeOut: "Florence Bridge", miles: 9.0, difficulty: "Class I", notes: "Check recent obstruction reports — strainers are common here." },
    ],
  },
  {
    id: "gallatin-lower",
    name: "Gallatin River (Valley)",
    gauge: "06043500",
    gaugeName: "Gallatin near Gallatin Gateway",
    lat: 45.507, lon: -111.271,
    refFlowCfs: 800, refSpeedMph: 3.2,
    blurb: "The mellow valley miles below the canyon whitewater. Shallow and quick.",
    sections: [
      { id: "gateway-shedds", putIn: "Gallatin Gateway (Axtell Bridge)", takeOut: "Shedd's Bridge", miles: 9.0, difficulty: "Class I–II", notes: "Gets bony by August — check the flow before you commit." },
    ],
  },
  {
    id: "missouri-craig",
    name: "Missouri River (Craig)",
    gauge: "06066500",
    gaugeName: "Missouri bl Holter Dam",
    lat: 47.0, lon: -112.01,
    refFlowCfs: 4000, refSpeedMph: 3.0,
    blurb: "Tailwater giant. Steady dam-controlled flows, trout everywhere, drift boats everywhere too.",
    sections: [
      { id: "holter-craig", putIn: "Holter Dam", takeOut: "Craig", miles: 3.5, difficulty: "Class I", notes: "Short and sweet. Busy boat ramp on summer weekends." },
      { id: "craig-mtn-palace", putIn: "Craig", takeOut: "Mountain Palace", miles: 8.0, difficulty: "Class I", notes: "Canyon scenery, steady current the whole way." },
    ],
  },
  {
    id: "stillwater",
    name: "Stillwater River",
    gauge: "06205000",
    gaugeName: "Stillwater near Absarokee",
    lat: 45.52, lon: -109.44,
    refFlowCfs: 800, refSpeedMph: 4.3,
    blurb: "Badly named — it's the fastest float in this list. Continuous Class II fun.",
    sections: [
      { id: "cliff-swallow-absarokee", putIn: "Cliff Swallow", takeOut: "Absarokee", miles: 6.0, difficulty: "Class II", notes: "Fast, rocky, cold. Rafts and duckies, not tubes." },
      { id: "absarokee-whitebird", putIn: "Absarokee", takeOut: "Whitebird", miles: 7.0, difficulty: "Class II", notes: "Keep your weight downstream through the rock gardens." },
    ],
  },
  {
    id: "smith",
    name: "Smith River (Permit)",
    gauge: "06077200",
    gaugeName: "Smith bl Eagle Creek nr Fort Logan",
    lat: 46.68, lon: -111.19,
    refFlowCfs: 350, refSpeedMph: 2.8,
    blurb: "Montana's only permit-lottery river. 59 canyon miles, 4–5 days, zero cell service.",
    multiDay: true,
    sections: [
      { id: "camp-baker-eden", putIn: "Camp Baker", takeOut: "Eden Bridge", miles: 59.0, difficulty: "Class I–II", notes: "Launch requires an FWP permit. Below ~150 cfs expect to drag boats." },
    ],
  },
];

// Craft speed multipliers relative to a drift boat / raft at current speed.
const CRAFT = [
  { id: "raft",  label: "Raft / drift boat", mult: 1.0 },
  { id: "kayak", label: "Kayak / canoe (paddling)", mult: 1.2 },
  { id: "tube",  label: "Inner tube", mult: 0.72 },
  { id: "sup",   label: "Paddleboard", mult: 1.05 },
];
