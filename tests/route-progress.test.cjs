const test=require('node:test'), assert=require('node:assert/strict');
const F=require('../public/route-progress.js');
const data=require('../public/route-pilots/blackfoot-johnsrud-weigh-station.json');
const route=F.prepare(data), now=100000;
const fix=(point,extra={})=>({longitude:point[0],latitude:point[1],accuracy:10,timestamp:now,...extra});
test('real Blackfoot pilot follows river mileage and progresses downstream',()=>{
  assert.ok(Math.abs(route.length/1609.344-10.7)<.1);
  for(const fraction of [0,.25,.5,.75,.9]){
    const p=F.locate(route,fix(F.pointAt(route,fraction)),now);
    assert.equal(p.status,'on-route');
    assert.ok(Math.abs(p.progress-fraction)<.001);
  }
  assert.equal(F.locate(route,fix(F.pointAt(route,1)),now).status,'near-takeout');
  assert.ok(route.length>F.distance(route.coordinates[0],route.coordinates.at(-1))*1.2);
});
test('missing, old, future, poor, and off-river GPS cannot yield ETA distance',()=>{
  const mid=F.pointAt(route,.5);
  for(const [input,status] of [[null,'missing'],[fix(mid,{timestamp:now-30001}),'stale'],[fix(mid,{timestamp:now+5001}),'stale'],[fix(mid,{accuracy:51}),'inaccurate'],[fix([mid[0],mid[1]+.02]),'off-route']]){
    const result=F.locate(route,input,now); assert.equal(result.status,status); assert.equal(result.remainingMiles,undefined);
  }
});
test('parallel hairpin branches with distant river mileage are ambiguous',()=>{
  const coordinates=[[0,0],[.008,0],[.008,.0002],[0,.0002]];
  const miles=coordinates.slice(1).reduce((n,p,i)=>n+F.distance(coordinates[i],p),0)/1609.344;
  const hairpin=F.prepare({status:'local-pilot',catalogMiles:miles,geometry:{type:'LineString',coordinates}});
  assert.equal(F.locate(hairpin,fix([.002,.0001]),now).status,'ambiguous');
});
test('invalid or discontinuous route and mileage disagreement fail closed',()=>{
  assert.throws(()=>F.prepare({...data,catalogMiles:20}));
  assert.throws(()=>F.prepare({...data,geometry:{type:'LineString',coordinates:[[0,0],[1,1]]}}));
  assert.throws(()=>F.prepare({...data,status:'unverified'}));
});
test('pilot still matches published access points and section distance',()=>{
  const catalog=require('../public/catalog.json');
  const river=catalog.rivers.find(r=>r.id===data.riverId), section=river.sections.find(s=>s.id===data.sectionId);
  assert.equal(data.catalogMiles,section.miles);
  assert.deepEqual(data.putIn,section.putInCoords); assert.deepEqual(data.takeOut,section.takeOutCoords);
  assert.ok(F.distance(route.coordinates[0],[data.putIn.lon,data.putIn.lat])<100);
  assert.ok(F.distance(route.coordinates.at(-1),[data.takeOut.lon,data.takeOut.lat])<100);
  assert.equal(data.land.features.length,8);
});
