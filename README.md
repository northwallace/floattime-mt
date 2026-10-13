# FloatTime MT 🛶

**How long will your Montana river float *actually* take?**

A website that turns live USGS streamflow data into real-world float time
estimates for Montana's most popular rivers — with daylight countdowns, water
temperature, weather at the put-in, condition ratings, flow trends, and
community-sourced obstruction reports.

## Run it

```bash
python3 server.py        # http://localhost:8000
python3 server.py 3000   # custom port
```

No dependencies — pure Python 3 standard library on the back end, vanilla
HTML/CSS/JS on the front end.

## What it does

- **Live flow data** — pulls instantaneous discharge (cfs) and water temp from
  the [USGS Water Services API](https://waterservices.usgs.gov/) for 10 rivers
  / 18 float sections, with a 7-day flow sparkline and 24-hour trend.
- **Float time estimates** — per-river calibrated drift speed scaled by the
  hydraulic-geometry relationship v ∝ Q^0.34, adjusted per craft (raft, kayak,
  tube, SUP).
- **Daylight planning** — computes sunset at the put-in and shows the latest
  launch time that still gets you to the takeout before dark.
- **Condition ratings** — Low & bony / Mellow / Prime / High & fast / Runoff,
  based on current flow vs. the river's reference flow.
- **Weather at the put-in** — air temp and wind from
  [Open-Meteo](https://open-meteo.com/) (free, no API key).
- **Community river reports** — anyone can report strainers, diversion dams,
  fences, and other obstructions; others can confirm ("still there") or mark
  cleared. Reports with 3+ "cleared" votes are hidden automatically.
  Persisted server-side in `data/reports.json`.
- **Ad slots** — placeholder leaderboard and in-content units, ready to swap
  for Google AdSense once the site is approved (see the comment in
  `public/index.html`).

## Project layout

```
server.py            Python stdlib server: static files + reports API
public/index.html    Page markup + ad slots
public/styles.css    Styling (dark riverside theme)
public/rivers.js     River/section database + calibration values
public/app.js        USGS fetch, float math, sunset calc, reports UI
data/reports.json    Obstruction report storage (created/updated at runtime)
```

## Adding a river or section

Edit `public/rivers.js`. Each river needs a USGS gauge ID, put-in coordinates
(for sunset/weather), a `refFlowCfs`/`refSpeedMph` calibration pair (typical
drift speed at a typical flow), and one or more sections with approximate
mileages.

## Notes & caveats

- Mileages and speed calibrations are estimates — refine them against real
  float logs over time.
- The reports API has no auth/rate limiting; add both before going public.
- For production, put the Python server behind a real host (or port the ~200
  lines of API to any stack) and serve over HTTPS.
