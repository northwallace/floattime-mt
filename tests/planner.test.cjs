const { test } = require("node:test");
const assert = require("node:assert/strict");
const P = require("../public/planner.js");
const river = { gauge: "12345678", refFlowCfs: 1100, refSpeedMph: 4 };
test("missing and reference gauges cannot enable timing even with a supplied flow", () => {
  for (const gaugeRelationship of ["none", "same-river-reference", "other-river-reference"])
    assert.equal(P.estimate({...river,gaugeRelationship},{miles:8},1100,1,0),null);
  assert.equal(P.estimate({...river,gauge:null},{miles:8},1100,1,0),null);
});
test("zero/invalid flow never produces an estimate", () => {
  for (const q of [0, -1, NaN, Infinity])
    assert.equal(P.estimate(river, { miles: 8 }, q, 1, 0), null);
});
test("unavailable or missing calibration never produces an ETA even with fresh flow", () => {
  for (const r of [
    {...river, timing:{mode:"unavailable"}},
    {...river, refSpeedMph:null},
    {...river, refFlowCfs:null},
    {...river, refSpeedMph:NaN},
  ]) assert.equal(P.estimate(r,{miles:8},1100,1,0),null);
});
test("rounds total duration without 60-minute remainder", () =>
  assert.equal(P.duration(119.99), "2 hr"));
test("stops and craft alter duration", () => {
  const a = P.estimate(river, { miles: 8 }, 788, 1, 30);
  assert.equal(a.minutes, 165);
  assert(P.estimate(river, { miles: 8 }, 788, 0.72, 30).minutes > a.minutes);
});
test("multi-day uses ceiling and retains total hours", () => {
  const e = P.estimate({ ...river, multiDay: true }, { miles: 60 }, 1100, 1, 0);
  assert.equal(e.rawMinutes, 900);
  assert.equal(e.days, 3);
});
test("one multi-day section does not label a whole mixed river", () => {
 const short=P.estimate({...river,multiDay:false},{miles:8},1100,1,0);
 const long=P.estimate({...river,multiDay:false},{miles:73,multiDay:true},1100,1,0);
 assert.equal(short.multiDay,false);assert.equal(long.multiDay,true);
});
test("freshness excludes stale, future and zero readings", () => {
  const n = Date.now();
  assert(P.fresh({ flow: 1, at: n }, n));
  assert(!P.fresh({ flow: 1, at: n - 121 * 60000 }, n));
  assert(!P.fresh({ flow: 1, at: n + 10 * 60000 }, n));
  assert(!P.fresh({ flow: 0, at: n }, n));
});
test("launch uses river timezone independent of computer timezone", () => {
  const now = new Date("2026-10-21T18:00:00Z");
  assert.equal(
    P.launch("12:00", "America/Los_Angeles", now).toISOString(),
    "2026-10-21T19:00:00.000Z",
  );
  assert.equal(
    P.launch("12:00", "America/Denver", now).toISOString(),
    "2026-10-21T18:00:00.000Z",
  );
});
test("sunset stays on the river calendar date near UTC midnight", () => {
  const now = new Date("2026-10-22T03:00:00Z");
  const s = P.sunset(44.899, -111.593, "America/Denver", now);
  assert.equal(P.dateKey(s, "America/Denver"), "2026-10-21");
  assert(Math.abs(s - new Date("2026-10-22T00:31:00Z")) < 5 * 60000);
});
test("invalid DST local launch is rejected", () =>
  assert.equal(
    P.launch("02:30", "America/Denver", new Date("2026-03-08T18:00:00Z")),
    null,
  ));

test('access under review never yields an estimate',()=>{
 assert.equal(P.estimate(river,{miles:8,accessReview:"Landing not confirmed"},1100,1,0),null);
});
