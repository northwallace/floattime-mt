const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const P=require('../public/planner.js');
function harness(fetch){
 const elements=new Map();
 function element(){return {_text:'',_html:'',get textContent(){return this._text;},set textContent(v){this._text=String(v);this._html=String(v).replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));},get innerHTML(){return this._html;},set innerHTML(v){this._html=v;},value:'',checked:false,hidden:false,children:[],replaceChildren(){this.children=[];},appendChild(c){this.children.push(c);},setAttribute(){}};}
 const document={getElementById(id){if(!elements.has(id))elements.set(id,element());return elements.get(id);},createElement:element,createElementNS:element};
 const context=vm.createContext({FloatPlanner:P,FloatRoute:require("../public/river-route.js"),FloatProgress:require("../public/route-progress.js"),setInterval:()=>1,clearInterval:()=>{},fetch,document,AbortSignal,Date,Map,Set,URLSearchParams,URL,console});
 const source=fs.readFileSync(require.resolve('../public/app.js'),'utf8').replace(/init\(\);\s*$/,'');
 vm.runInContext(source,context);
 return {run:s=>vm.runInContext(s,context),elements,context};
}
const river={id:'test',name:'Test',state:'MT',gauge:'12345678',timezone:'America/Denver',lat:45,lon:-111,refFlowCfs:1000,refSpeedMph:4,sections:[{id:'a',putIn:'A',takeOut:'B',miles:8,difficulty:'Class I',notes:''}]};
function fixture(h){h.context.fixture=JSON.parse(JSON.stringify(river));h.run('state.river=fixture;state.craft={id:"raft",mult:1};state.reportsStatus="ready";');}
test('gauge proxy response preserves current flow and graph',async()=>{
 const now=Date.now();
 const h=harness(async()=>({ok:true,json:async()=>({flow:200,at:now,temp:10,tempAt:now,series:[{t:now-60000,q:100},{t:now,q:200}],source:'USGS Water Data API'})}));
 fixture(h); const result=await h.run('gaugeFor(state.river)');assert.equal(result.flow,200);assert.equal(result.at,now);assert.equal(result.series.length,2);assert.equal(result.series[0].q,100);
});
test('stale reading keeps routes but never shows a calculated duration',()=>{
 const h=harness();fixture(h);h.run('renderSections(state.river,{flow:1000,at:Date.now()-121*60000},null)');
 const html=h.elements.get('sectionCards').children[0].innerHTML;assert.match(html,/No recent, positive flow/);assert.doesNotMatch(html,/2 hr/);assert.match(html,/A/);
});
test('fresh flow with unavailable calibration shows guides without calculated finish or launch advice',()=>{
 const h=harness();fixture(h);h.run('state.river.timing={mode:"unavailable"};state.river.refFlowCfs=null;state.river.refSpeedMph=null;state.river.sections[0].guideTimes=[{min:2,max:3,unit:"hours",conditions:"Published guide conditions",sourceName:"Agency guide",sourceUrl:"https://example.gov/guide"}];state.fishing=true;document.getElementById("putInTime").value="10:00";renderSections(state.river,{flow:1000,at:Date.now()},new Date(Date.now()+36000000))');
 const html=h.elements.get('sectionCards').children[0].innerHTML;
 assert.match(html,/A live float-time estimate is not available/);assert.match(html,/Published guide: 2–3 hours/);
 assert.doesNotMatch(html,/Take out ≈|Launch by|~[\d.]+ mph/);
 assert.equal(h.run('conditionFor(state.river,1000).label'),'Live flow');
});
test('fishing on long routes keeps total hours and rounds days up',()=>{
 const h=harness();fixture(h);h.run('state.river.sections[0].miles=60;state.fishing=true;renderSections(state.river,{flow:1000,at:Date.now()},null)');
 const html=h.elements.get('sectionCards').children[0].innerHTML;assert.match(html,/40 hr/);assert.match(html,/At least 6 floating days/);assert.doesNotMatch(html,/Take out ≈/);
});
test('Class III tube never gets an estimate',()=>{
 const h=harness();fixture(h);h.run('state.river.sections[0].difficulty="Class III–IV";state.craft.id="tube";renderSections(state.river,{flow:1000,at:Date.now()},null)');
 assert.match(h.elements.get('sectionCards').children[0].innerHTML,/no tube or recreational/);
});
test('failed reports stay explicitly unavailable',async()=>{
 const h=harness(async()=>({ok:false,status:503}));await h.run('loadReports()');assert.match(h.elements.get('reportsList').innerHTML,/does not mean the river is clear/);
});
test('failed votes are not marked as successful locally',async()=>{
 const h=harness(async()=>({ok:false,status:500}));await h.run('vote("id","confirm")');assert.equal(h.run('state.votedIds.has("id")'),false);assert.match(h.elements.get('reportStatus').textContent,/Vote failed/);
});
test('distance conflicts block estimates and show an explicit review notice',()=>{
 const h=harness();fixture(h);h.run('state.river.sections[0].distanceReview="Endpoint mileage conflict";renderSections(state.river,{flow:1000,at:Date.now()},null)');
 const html=h.elements.get('sectionCards').children[0].innerHTML;
 assert.match(html,/Distance and endpoints under review/);assert.doesNotMatch(html,/~4.0 mph|2 hr/);
 assert.equal(h.run('P.estimate(state.river,state.river.sections[0],1000,1,0)'),null);
});

test('satellite sources authenticate only to Esri and respect both tile grids',()=>{
 const h=harness();h.context.testKey='public-test&key';
 const style=h.run('satelliteMapStyle(testKey)');
 assert.equal(style.sources['world-imagery'].tileSize,256);
 assert.equal(style.sources['imagery-labels'].tileSize,512);
 for(const source of Object.values(style.sources)){
  const url=new URL(source.tiles[0]);
  assert.ok(['ibasemaps-api.arcgis.com','static-map-tiles-api.arcgis.com'].includes(url.hostname));
  assert.equal(url.searchParams.get('token'),'public-test&key');
  assert.match(source.attribution,/Esri/);
 }
 assert.throws(()=>h.run('satelliteMapStyle("")'),/not configured/);
});

test('progress controller uses GPS, current gauge and fishing; clears on errors and cleanup',()=>{
 const h=harness();fixture(h);
 h.context.pilot=require('../public/route-pilots/blackfoot-johnsrud-weigh-station.json');
 h.run('state.gauge={flow:1000,at:Date.now()}; const route=FloatProgress.prepare(pilot); const controller=mountFloatProgress({}, {}, pilot, route, state.river, state.river.sections[0]); const point=FloatProgress.pointAt(route,.5); controller.update({coords:{longitude:point[0],latitude:point[1],accuracy:10},timestamp:Date.now()});');
 const result=h.elements.get('floatProgressResult');
 assert.match(result.textContent,/About 1 hr 15 min remaining/);
 h.run('state.fishing=true; controller.refresh()');
 assert.match(result.textContent,/About 3 hr 30 min remaining/);
 h.run('state.gauge.at=0; controller.refresh()'); assert.match(result.textContent,/time estimate unavailable/);
 h.run('controller.unavailable()'); assert.match(result.textContent,/Use the location button/);
 h.run('controller.destroy()'); assert.equal(h.elements.get('floatProgress').hidden,true);
 assert.equal(h.elements.get('progressDemoStart').onclick,null);
});

test('map route review is independent of GPS and rejects stale endpoint snapshots',()=>{
 const h=harness();
 h.context.record=require('../public/routes/blackfoot--johnsrud-weigh-station.json');
 h.context.catalog=require('../public/catalog.json');
 h.run('const river=catalog.rivers.find(r=>r.id===record.riverId); const section=river.sections.find(s=>s.id===record.sectionId);');
 assert.ok(h.run('prepareSectionRoute(record,river,section).length')>16000);
 h.run('const changed=JSON.parse(JSON.stringify(record));changed.putIn.lon+=.001;');
 assert.throws(()=>h.run('prepareSectionRoute(changed,river,section)'),/endpoints/);
 h.run('changed.putIn=record.putIn;changed.status="candidate";');
 assert.throws(()=>h.run('prepareSectionRoute(changed,river,section)'),/not reviewed/);
 assert.equal(h.run('record.features.remainingTime'),false);
});

test('access review suppresses times and map even when fresh flow and coordinates exist',async()=>{
 const h=harness();fixture(h);h.run('state.river.sections[0].accessReview="Take-out needs review";state.river.sections[0].mapReleased=false;state.river.sections[0].mapPilot=true;state.river.sections[0].putInCoords={lat:45,lon:-111};state.river.sections[0].takeOutCoords={lat:45.1,lon:-111.1};renderSections(state.river,{flow:1000,at:Date.now()},null)');
 const html=h.elements.get('sectionCards').children[0].innerHTML;
 assert.match(html,/Take-out needs review/);assert.doesNotMatch(html,/data-map-section|~[\d.]+ mph|2 hr/);
 await h.run('showLandMap(state.river.sections[0])');assert.equal(h.run('state.landMapSection'),null);
});
test('unreleased state map cannot be opened through direct map function',async()=>{
 const h=harness();fixture(h);h.run('state.river.state="WA";state.river.sections[0].mapReleased=false;state.river.sections[0].mapPilot=true');
 await h.run('showLandMap(state.river.sections[0])');assert.equal(h.run('state.landMapSection'),null);
});
