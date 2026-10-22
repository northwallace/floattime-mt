# Float ETA

A river float planner with live USGS flow, river-local daylight, optional fishing time,
community reports, and a searchable river catalog. Python standard library on
the server; HTML, CSS, and JavaScript in the browser.

## Run locally

```sh
python3 tools/build_catalog.py
python3 server.py 8000
```

Open http://localhost:8000. Python 3.9+ with IANA timezone data is required.

## Add a river (daily workflow)

1. Copy a nearby record in `catalog/rivers/` to a new file named after its unique
   URL ID, for example `catalog/rivers/new-river.json`.
2. Set `id` to `new-river`. Keep IDs stable after publishing so existing links work.
3. Fill in the name, state, gauge ID (a quoted string, including leading zeros),
   gauge name, put-in coordinates, **IANA timezone**, reference flow and speed,
   blurb, and sections. Every section needs its own ID, put-in, takeout, miles,
   difficulty, and notes. Use `multiDay: true` for designated overnight routes.
4. Verify gauge coverage, access, distance, difficulty, and calibration. Validation
   catches structural errors; it cannot certify geographic or river information.
5. Build and check:

```sh
python3 tools/build_catalog.py
python3 -m unittest discover -s tests
# Optional calculator regression tests (Node 18+):
node --test tests/planner.test.cjs
```

6. Commit the source record **and** generated `public/catalog.json`. Deploy as
   usual. The calculator, search, directories, river pages, counts, and sitemap
   all pick up the record. No HTML or application code edits are needed.

### Add a state

Add the state's `id`, `name`, unique `slug`, `agency`, and HTTPS `agencyUrl` to
`catalog/settings.json`, then add its rivers and rebuild. Restart/redeploy the
server to pick up new state routing. The planner and generated state directory
navigation are automatic. About/contact/privacy pages contain editorial coverage
copy and can be updated separately when announcing new state coverage.

### Catalog validation

The build rejects malformed/duplicate IDs, filename/ID mismatches, unknown
states, invalid gauge strings or timezones, missing sections, duplicate section
IDs, and invalid coordinates, mileage or calibration values. JSON parsing safely
preserves quotes/braces in names and notes. `--check` also rejects stale generated
output; the Render build runs this check and Python tests before starting.

`public/catalog.json` is generated. Edit `catalog/`, not the generated file.
The legacy `public/rivers.js` has been replaced by the catalog source files.

## How growth is handled

- One small source file per river; independent additions are easy to review.
- One shared, generated catalog drives browser and SEO content.
- New reports reference stable river IDs, so similarly named rivers remain distinct.
- Search covers names, states and access points; results render 12 at a time.
- Only the selected river loads gauge and weather data. Requests share a short
  cache and in-flight promise. Search is debounced; outdated responses cannot
  replace the newly selected river.
- SEO parses JSON, caches by modification time, and renders route pages on demand.
- The full catalog is downloaded once. This is suitable for hundreds to low
  thousands of records; for much larger datasets, move search to a paginated API
  rather than loading the entire catalog. This is not an unlimited-scale claim.

## Planning behavior

Flow readings older than two hours, nonpositive flow, and missing flow do not
produce a current estimate. Cached requests refresh after five minutes, and
visible-page results refresh periodically. Temperature freshness is independent.
All launch/arrival/sunset times use the river's timezone. Launch times refer to
**today**, including when opening a shared link. Shared links preserve river,
craft, fishing preference and optional launch time.

Trips are rounded to five minutes; fishing adds 25 minutes per mile. Multi-day
results show total water time and minimum days at seven hours/day, without a
fabricated arrival time. Tubes and recreational SUPs do not receive an estimate
for Class III+ sections. No flow badge claims a route is safe.

Existing timezone records were initialized from the rivers' regions; verify
boundary rivers and put-in locations when reviewing or adding records.

## Reports, storage and production

Reports and contact submissions remain JSON files. Set `DATA_DIR` to durable
storage in production (the default is `./data`). Back up that directory. The
existing Render blueprint does not provision a persistent disk. Confirm your
actual hosting configuration before relying on report persistence.

Clear votes are advisory and no longer automatically hide hazards. Repeated
votes are deduplicated by connection address per report; this is a basic guard,
not identity verification. A reverse proxy or shared network can group users
under one address. Configure a trusted proxy/identity strategy and rate limiting
at the hosting boundary before relying on voting at scale. Report submission
moderation and robust anti-spam controls remain follow-up work. Reports still
expire after 45 days without activity. No reports never means no hazards.

## Project layout

- `catalog/rivers/*.json` — editable river records
- `catalog/settings.json` — states and craft multipliers
- `tools/build_catalog.py` — catalog validator/builder
- `public/catalog.json` — generated shared data
- `public/planner.js` — pure date/time and float calculation functions
- `public/app.js` — data fetching, search and interface
- `public/styles.css` — shared responsive design
- `seo.py` — state pages, river pages and sitemap
- `server.py` — static pages, reports and contact API
- `tests/` — catalog/SEO and calculator regressions

## Release and hosting

Production is the existing Render `floattime-mt` service in Oregon, on the
$7/month `0.5c-512mb` plan. The blueprint explicitly preserves that plan.
Pushes to `main` auto-deploy. Do not push until the storage setup is complete.

The Blueprint provisions a 1 GB persistent disk named `floattime-data` at
`/opt/render/project/src/data`, which is the server's default `DATA_DIR`. Back up
that directory periodically and never commit private submissions to Git.

For each rollout, run the catalog validator, Python tests, and Node calculator/UI
tests locally. After publishing, check health, the homepage, directory, river
links, reports, contact page, and mobile layout on `floateta.com`.

The home page deliberately starts with no state or river selected. A `?river=`
link selects that river. At most four popular rivers appear for the chosen state;
the separate directory searches the catalog and displays 12 results at a time.
The original gauges, seven-day graph, fishing toggle, and stretch cards remain.
