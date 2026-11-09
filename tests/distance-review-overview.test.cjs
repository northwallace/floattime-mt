const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const R=require('../public/river-route.js'),GPS=require('../public/route-progress.js');
const fixture=require('./fixtures/distance-review-overview.json'),data=fixture.public;
const river=require('../public/catalog.json').rivers.find(r=>r.id==='beaverhead');
const section=fixture.section;
const source=fs.readFileSync(require.resolve('../public/app.js'),'utf8'),context=vm.createContext({FloatRoute:R});
vm.runInContext(source.match(/function prepareSectionRoute\([\s\S]*?\n\}/)[0],context);
test('reviewed disputed-distance course renders without enabling GPS progress',()=>{
 const route=context.prepareSectionRoute(data,river,section);
 assert.equal(route.displayOnly,true);assert.ok(route.length/1609.344>1.6&&route.length/1609.344<1.7);
 assert.throws(()=>R.prepare(data),/display only/);assert.throws(()=>GPS.prepare(data),/display only/);
 assert.deepEqual(GPS.locate(route,{longitude:0,latitude:0,accuracy:1,timestamp:1000},1000),{status:'display-only'});
});
test('section and route must agree on the current distance hold',()=>{
 for(const value of [undefined,'','Changed hold'])assert.throws(()=>context.prepareSectionRoute(data,river,{...section,distanceReview:value}),/distance/);
 const r=structuredClone(data);delete r.overview.planningDistanceReview;
 assert.throws(()=>context.prepareSectionRoute(r,river,section),/distance/);
 assert.throws(()=>R.prepare(r,{displayOnly:true}),/mileage/);
});
test('distance exception cannot enable advanced features, ordinary routes or gaps',()=>{
 for(const flag of ['remainingTime','distanceEstimate','landOverlay']){const r=structuredClone(data);r.features[flag]=true;assert.throws(()=>R.prepare(r,{displayOnly:true}));}
 for(const value of [null,42,'',true]){const r=structuredClone(data);r.overview.planningDistanceReview=value;assert.throws(()=>R.prepare(r,{displayOnly:true}));}
 assert.throws(()=>R.prepare({...data,scope:'landing-to-landing'},{displayOnly:true}));
 const r=structuredClone(data);r.geometry.coordinates[5][0]+=.1;assert.throws(()=>R.prepare(r,{displayOnly:true}),/gap/);
});
test('resolved Beaverhead mileage uses current agency distances and rejects the old held record',()=>{
 const current=river.sections.find(s=>s.id==='dam-high-bridge');
 assert.equal(current.miles,1.5);assert.equal(current.distanceReview,undefined);
 assert.throws(()=>context.prepareSectionRoute(data,river,current),/distance/);
 for(const sid of ['dam-high-bridge','henneberry-pipe-organ','pipe-organ-grasshopper','henneberry-grasshopper','high-bridge-henneberry','high-bridge-pipe-organ','dam-henneberry','dam-pipe-organ']){
  const r=require('../public/routes/beaverhead--'+sid+'.json');
  const section=river.sections.find(s=>s.id===sid),route=context.prepareSectionRoute(r,river,section);
  assert.equal(route.displayOnly,true);assert.equal(r.catalogMiles,section.miles);
  assert.throws(()=>GPS.prepare(r),/display only/);
 }
});
