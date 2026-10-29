const test=require('node:test'), assert=require('node:assert/strict'), crypto=require('node:crypto'), fs=require('node:fs');
const F=require('../public/field-pilot.js'), G=require('../public/route-progress.js'), P=require('../public/planner.js');
const data=require('../public/field-pilots/greycliff.json');
const river=require('../public/catalog.json').rivers.find(r=>r.id===data.riverId);
const section=river.sections.find(s=>s.id===data.sectionId), route=F.prepare(data,river,section);
const entry=require('../catalog/field_pilots.json').pilots[0], now=Date.now();
const fix=(fraction,extra={})=>{const p=G.pointAt(route,fraction);return {longitude:p[0],latitude:p[1],accuracy:10,timestamp:now,...extra};};
test('actual progress UI responds to GPS, fishing, stale flow, stale GPS, and cleanup',()=>{
  const vm=require('node:vm'), nodes=new Map();
  const element=id=>{if(!nodes.has(id))nodes.set(id,{hidden:true,textContent:''});return nodes.get(id);};
  const state={craft:{id:'raft',label:'Raft / drift boat',mult:1},gauge:{flow:1310,at:now},fishing:false};
  let refresh, cleared=false;
  const context=vm.createContext({$:element,state,P,FloatProgress:G,FISH_MIN_PER_MILE:25,Date,setInterval:fn=>{refresh=fn;return 1;},clearInterval:()=>{cleared=true;}});
  const source=fs.readFileSync('public/app.js','utf8');
  vm.runInContext(source.slice(source.indexOf('function mountFloatProgress('),source.indexOf('async function showLandMap(')),context);
  const controller=context.mountFloatProgress({}, {},data,route,river,section,true);
  assert.equal(element('progressDemo').hidden,true);
  assert.match(element('floatProgressResult').textContent,/Use the location/);
  const gps=fix(.5);controller.update({coords:gps,timestamp:gps.timestamp});
  assert.equal(element('floatProgressResult').textContent,'About 45 min remaining');
  state.fishing=true;refresh();assert.equal(element('floatProgressResult').textContent,'About 1 hr 30 min remaining');
  state.gauge.at=now-121*60000;refresh();assert.match(element('floatProgressResult').textContent,/Distance available; time estimate unavailable/);
  controller.update({coords:gps,timestamp:now-31000});assert.match(element('floatProgressResult').textContent,/fresh location/);
  controller.unavailable();assert.match(element('floatProgressResult').textContent,/Use the location/);
  controller.destroy();assert.equal(element('floatProgress').hidden,true);assert.equal(cleared,true);
});
test('pilot is explicitly selected for just this section and file is unchanged',()=>{
  assert.equal(F.matches(entry,'',river,section),false);
  assert.equal(F.matches(entry,'unknown',river,section),false);
  assert.equal(F.matches(entry,'greycliff',river,{...section,id:'warm-blacks'}),false);
  assert.equal(F.matches(entry,'greycliff',river,section),true);
  assert.equal(entry.sha256,crypto.createHash('sha256').update(fs.readFileSync('public/'+entry.file)).digest('hex'));
});
test('actual primary USGS path progresses to the user-confirmed ramp',()=>{
  assert.ok(route.length/1609.344>4.5 && route.length/1609.344<4.6);
  assert.equal(data.takeOut.lat,45+42/60+16.2/3600);
  assert.equal(data.takeOut.lon,-(111+30/60+58.1/3600));
  for(const fraction of [0,.1,.25,.5,.75,.9]){
    const location=G.locate(route,fix(fraction),now);
    assert.equal(location.status,'on-route'); assert.ok(Math.abs(location.progress-fraction)<.001);
    const estimate=P.estimate(river,{...section,miles:location.remainingMiles},1310,1,0);
    assert.ok(estimate.rawMinutes>0 && estimate.rawMinutes<90);
  }
  assert.equal(G.locate(route,{longitude:data.takeOut.lon,latitude:data.takeOut.lat,accuracy:10,timestamp:now},now).status,'near-takeout');
  // Facility centroid must not accidentally become the field-test destination.
  assert.equal(G.locate(route,{longitude:section.takeOutCoords.lon,latitude:section.takeOutCoords.lat,accuracy:10,timestamp:now},now).status,'off-route');
  assert.equal(section.miles,4); assert.notDeepEqual(data.takeOut,section.takeOutCoords);
});
test('GPS failures cannot produce remaining distance; stale flow cannot produce live timing',()=>{
  for(const [input,status] of [[null,'missing'],[fix(.5,{accuracy:100}),'inaccurate'],[fix(.5,{timestamp:now-31000}),'stale'],[fix(.5,{longitude:-111.3}),'off-route']]){
    const result=G.locate(route,input,now);assert.equal(result.status,status);assert.equal(result.remainingMiles,undefined);
  }
  assert.equal(P.fresh({flow:1310,at:now-121*60000},now),false);
  assert.equal(P.fresh({flow:null,at:now},now),false);
  const miles=G.locate(route,fix(.5),now).remainingMiles;
  const plain=P.estimate(river,{...section,miles},1310,1,0), fishing=P.estimate(river,{...section,miles},1310,1,miles*25);
  assert.ok(Math.abs(fishing.rawMinutes-plain.rawMinutes-miles*25)<.0001);
});
test('changed access, river, distance, reversed line or incorrect destination blocks the pilot',()=>{
  for(const [d,r,s] of [[data,river,{...section,miles:5}],[data,{...river,id:'different'},section],[data,river,{...section,takeOutCoords:{lat:45,lon:-111}}],[{...data,geometry:{...data.geometry,coordinates:[...data.geometry.coordinates].reverse()}},river,section],[{...data,takeOut:{...data.takeOut,lat:46}},river,section]]) assert.throws(()=>F.prepare(d,r,s));
});
