const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const P=require('../public/planner.js');
function harness(fetch){
 const elements=new Map();
 function element(){return {_text:'',_html:'',get textContent(){return this._text;},set textContent(v){this._text=String(v);this._html=String(v).replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));},get innerHTML(){return this._html;},set innerHTML(v){this._html=v;},value:'',checked:false,hidden:false,children:[],parentElement:{hidden:false},handlers:{},addEventListener(name,fn){this.handlers[name]=fn;},add(option){this.children.push(option);if(option.selected)this.value=option.value;},classList:{add(){},remove(){}},querySelector(){return null;},replaceChildren(){this.children=[];},appendChild(c){if(c.parentElement?.children)c.parentElement.children=c.parentElement.children.filter(x=>x!==c);this.children.push(c);c.parentElement=this;},setAttribute(){}};}
 const document={getElementById(id){if(!elements.has(id))elements.set(id,element());return elements.get(id);},createElement:element,createElementNS:element,querySelectorAll(){return [];},querySelector(selector){return this.getElementById(selector);},addEventListener(){}};
 const context=vm.createContext({FloatPlanner:P,FloatRoute:require("../public/river-route.js"),FloatProgress:require("../public/route-progress.js"),FloatFieldPilot:require("../public/field-pilot.js"),setInterval:()=>1,clearInterval:()=>{},fetch,document,AbortSignal,Date,Map,Set,URLSearchParams,URL,console});
 const source=fs.readFileSync(require.resolve('../public/app.js'),'utf8').replace(/init\(\);\s*$/,'');
 vm.runInContext(fs.readFileSync(require.resolve('../public/map-base.js'),'utf8'),context);
 vm.runInContext(source,context);
 return {run:s=>vm.runInContext(s,context),elements,context};
}
const river={id:'test',name:'Test',state:'MT',gauge:'12345678',timezone:'America/Denver',lat:45,lon:-111,refFlowCfs:1000,refSpeedMph:4,sections:[{id:'a',putIn:'A',takeOut:'B',miles:8,difficulty:'Class I',notes:''}]};
test('shared advisories keep full evidence once and a warning on exactly the affected cards',()=>{
 const h=harness();fixture(h);
 const notice={title:'Bridge closure',text:'Use the signed shuttle detour.',sourceUrl:'https://example.gov/notice',sourceName:'Agency',checkedOn:'2026-11-06'};
 const unique={...notice,title:'Blocked landing',text:'Wood <blocks> this landing.'};
 const sections=Array.from({length:5},(_,i)=>({...river.sections[0],id:'s'+i,notices:i<3?[notice]:i===3?[{...notice,text:'Different bridge; different restriction.'}]:[]}));
 sections[0].notices.push(unique);
 h.context.advisorySections=sections;h.run('state.river.sections=advisorySections;renderSections(state.river,null,null)');
 const html=h.elements.get('riverAdvisories').innerHTML;
 assert.equal(h.elements.get('riverAdvisories').hidden,false);
 assert.equal(html.split(notice.text).length-1,1);
 assert.match(html,/id="river-notice-1" tabindex="-1"/);
 assert.match(html,/Source checked 2026-11-06/);assert.match(html,/Applies to 3 stretches/);
 for(let i=0;i<5;i++){
  const card=h.elements.get('sectionCards').children[i].innerHTML;
  if(i<3){assert.match(card,/href="#river-notice-1">Bridge closure/);assert.ok(!card.includes(notice.text));assert.ok(html.includes('href="#section-s'+i+'"'));}
  else assert.doesNotMatch(card,/href="#river-notice/);
 }
 assert.match(h.elements.get('sectionCards').children[0].innerHTML,/Wood &lt;blocks&gt; this landing/);
 assert.match(h.elements.get('sectionCards').children[3].innerHTML,/Different bridge; different restriction/);
 const expanded=html.replace('<details class="advisory-stretches">','<details class="advisory-stretches" open>');
 h.elements.get('riverAdvisories').innerHTML=expanded;
 h.run('renderSections(state.river,null,null)');
 assert.equal(h.elements.get('riverAdvisories').innerHTML,expanded,'refresh must preserve the expanded list and its links');
 h.run('state.river.sections=[{id:"next",putIn:"C",takeOut:"D",miles:2,difficulty:"Class I",notes:""}];renderSections(state.river,null,null)');
 assert.equal(h.elements.get('riverAdvisories').hidden,true);assert.equal(h.elements.get('riverAdvisories').innerHTML,'');
});
test('notice grouping never combines changed evidence or counts one section twice',()=>{
 const n={title:'Closure',text:'Body',sourceUrl:'https://example.gov',sourceName:'Agency',checkedOn:'2026-11-06'};
 for(const key of Object.keys(n)){
  const sections=[{id:'a',notices:[n,n]},{id:'b',notices:[n]},{id:'c',notices:[{...n,[key]:n[key]+' changed'}]}];
  const before=JSON.stringify(sections);assert.deepEqual(P.sharedNotices(sections),[],key);assert.equal(JSON.stringify(sections),before);
 }
 const groups=P.sharedNotices(['a','b','c'].map(id=>({id,notices:[n]})));
 assert.deepEqual(groups,[{notice:n,sectionIds:['a','b','c'],id:'river-notice-1'}]);
});
test('an open planner recovers when a release replaces a hashed river file',async()=>{
 for(const status of [404,410]){
  const requests=[];
  const h=harness(async(url,options)=>{
   requests.push(url);
   if(url==='/catalog/rivers/test.old.json')return {ok:false,status};
   if(url==='/catalog-index.json'){
    assert.equal(options.cache,'no-store');
    return {ok:true,json:async()=>({rivers:[{id:'test',state:'MT',file:'catalog/rivers/test.new.json'}]})};
   }
   assert.equal(url,'/catalog/rivers/test.new.json');
   return {ok:true,json:async()=>river};
  });
  h.run('RIVERS=[{id:"test",state:"MT",file:"catalog/rivers/test.old.json"}]');
  assert.equal((await h.run('riverDetails(RIVERS[0])')).id,'test');
  assert.equal((await h.run('riverDetails(RIVERS[0])')).id,'test');
  assert.deepEqual(requests,['/catalog/rivers/test.old.json','/catalog-index.json','/catalog/rivers/test.new.json']);
 }
});
test('river recovery stops when the new index cannot supply that same river and state',async()=>{
 for(const updated of [{id:'other',state:'MT',file:'new.json'},{id:'test',state:'WI',file:'new.json'},{id:'test',state:'MT',file:'old.json'}]){
  const requests=[];
  const h=harness(async url=>{requests.push(url);return url==='/catalog-index.json'?{ok:true,json:async()=>({rivers:[updated]})}:{ok:false,status:404};});
  await assert.rejects(h.run('riverDetails({id:"test",state:"MT",file:"old.json"})'),/404/);
  assert.deepEqual(requests,['/old.json','/catalog-index.json']);
 }
});
test('a server failure does not trigger a catalog refresh loop',async()=>{
 const requests=[];
 const h=harness(async url=>{requests.push(url);return {ok:false,status:503};});
 await assert.rejects(h.run('riverDetails({id:"test",state:"MT",file:"old.json"})'),/503/);
 assert.deepEqual(requests,['/old.json']);
});
test('reviewed provider override uses a separate cache key and honest source label',async()=>{
 const requests=[];
 const h=harness(async url=>{requests.push(url);return {ok:true,json:async()=>({flow:25.2,at:Date.now(),series:[]})};});
 h.context.flowRiver={...river,flowSource:{provider:'usbr-gp',station:'GLWY',parameter:'Q',name:'North Platte below Glendo'}};
 await h.run('gaugeFor(flowRiver)');await h.run('gaugeFor(flowRiver)');
 assert.deepEqual(requests,['/api/gauge?site=USBR%3AGLWY%3AQ']);
 assert.equal(h.run('gaugeLabel(flowRiver)'),'Reclamation GLWY — North Platte below Glendo');
 assert.equal(h.run('gaugeKey({gauge:"06041000"})'),'06041000');
 h.context.flowRiver.flowSource={provider:'colorado-dwr',station:'ARKSALCO',parameter:'DISCHRG',name:'Arkansas at Salida'};
 await h.run('gaugeFor(flowRiver)');
 assert.equal(requests[1],'/api/gauge?site=CDWR%3AARKSALCO%3ADISCHRG');
 assert.equal(h.run('gaugeLabel(flowRiver)'),'Colorado DWR ARKSALCO — Arkansas at Salida');
});
test('gauge context explains seasonal and historical gaps without injecting markup',()=>{
 const h=harness();h.context.riverWithContext={gaugeContext:{note:'Seasonal <gap>',sourceName:'USGS',sourceUrl:'https://waterdata.usgs.gov/',checkedOn:'2026-10-29'}};
 const html=h.run('gaugeContextHtml(riverWithContext)');
 assert.match(html,/Seasonal &lt;gap&gt;/);assert.match(html,/Checked 2026-10-29/);
 assert.equal(h.run('gaugeContextHtml({})'),'');
});
function fixture(h){h.context.fixture=JSON.parse(JSON.stringify(river));h.run('state.river=fixture;state.craft={id:"raft",mult:1};state.reportsStatus="ready";');}
test('missing and other-river gauges never fetch flow and keep maps and guide times',async()=>{
 for(const relation of ['none','other-river-reference']){
  const requests=[];
  const h=harness(async url=>{requests.push(url);return {ok:true,json:async()=>({current:{},daily:{}})};});fixture(h);
  h.context.relation=relation;
  h.run('STATES=[{id:"MT",agency:"Agency",agencyUrl:"https://example.gov"}];state.river.gaugeRelationship=relation;state.river.timing={mode:"unavailable"};state.river.gaugeName="Other station";if(relation==="none")state.river.gauge=null;state.river.sections[0].mapReleased=true;state.river.sections[0].putInCoords={lat:45,lon:-111};state.river.sections[0].takeOutCoords={lat:45.1,lon:-111};state.river.sections[0].guideTimes=[{min:2,max:3,unit:"hours",conditions:"Guide conditions",sourceName:"Agency",sourceUrl:"https://example.gov"}];');
  await h.run('renderRiver()');
  assert.equal(requests.filter(u=>u.startsWith('/api/gauge')).length,0);
  assert.equal(h.elements.get('flowValue').textContent,'—');
  assert.equal(h.elements.get('waterTemp').textContent,'n/a');
  assert.doesNotMatch(h.elements.get('gaugeName').textContent,/null|undefined|unknown/);
  const html=h.elements.get('sectionCards').children[0].innerHTML;
  assert.match(html,/Live estimate unavailable/);assert.match(html,/Published guide: 2–3 hours/);assert.match(html,/data-map-section/);
  assert.doesNotMatch(html,/Take out ≈|Launch by|~[\d.]+ mph/);
 }
});
test('same-river reference is labelled and never supplies river temperature or ETA',async()=>{
 const now=Date.now();
 const h=harness(async url=>({ok:true,json:async()=>url.startsWith('/api/gauge')?{flow:200,at:now,temp:20,tempAt:now,series:[]}:{current:{},daily:{}}}));fixture(h);
 h.run('STATES=[{id:"MT",agency:"Agency",agencyUrl:"https://example.gov"}];state.river.gaugeRelationship="same-river-reference";');
 await h.run('renderRiver()');
 assert.equal(h.elements.get('flowHeading').textContent,'Reference gauge flow');
 assert.equal(h.elements.get('conditionBadge').textContent,'Reference reading');
 assert.equal(h.elements.get('waterTemp').textContent,'n/a');
 assert.match(h.elements.get('sectionCards').children[0].innerHTML,/reference only/);
});
test('no-data response recovers after cache expiry without enabling uncalibrated timing',async()=>{
 let now=Date.now(),calls=0;
 const h=harness(async url=>({ok:true,json:async()=>url.startsWith('/api/gauge')?(++calls===1?{flow:null,at:null,series:[]}:{flow:300,at:now,series:[]}):{current:{},daily:{}}}));fixture(h);
 h.context.Date=class extends Date {static now(){return now;}};
 h.run('STATES=[{id:"MT",agency:"Agency",agencyUrl:"https://example.gov"}];state.river.timing={mode:"unavailable"};');
 await h.run('renderRiver()');
 assert.match(h.elements.get('gaugeStatus').innerHTML,/Current flow unavailable/);
 await h.run('renderRiver()');assert.equal(calls,1);
 now+=300001;await h.run('renderRiver()');
 assert.equal(calls,2);assert.equal(h.elements.get('flowValue').textContent,'300');assert.equal(h.elements.get('gaugeStatus').hidden,true);
 assert.match(h.elements.get('sectionCards').children[0].innerHTML,/Live estimate unavailable/);
});
test('published trip distances show their source without invented river mile numbers',()=>{
 const h=harness();
 h.context.trip=JSON.parse(fs.readFileSync(require.resolve('../catalog/rivers/russian-river-forestville.json'),'utf8')).sections[0];
 const html=h.run('distanceEvidenceHtml(trip)');
 assert.match(html,/Published trip length: 2 mi/);
 assert.doesNotMatch(html,/River mile|undefined/);
});
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
 assert.match(html,/Live estimate unavailable/);assert.match(html,/Published guide: 2–3 hours/);
 assert.doesNotMatch(html,/Take out ≈|Launch by|~[\d.]+ mph/);
 assert.equal(h.run('conditionFor(state.river,1000).label'),'Live flow');
});
test('sub-hour published guides display minutes without changing the timing model',()=>{
 const h=harness();fixture(h);
 h.run('state.river.timing={mode:"unavailable"};state.river.sections[0].guideTimes=[{min:.75,max:.75,unit:"hours",conditions:"Agency guide",sourceName:"DNR",sourceUrl:"https://example.gov"}];renderSections(state.river,{flow:1000,at:Date.now()},null)');
 let html=h.elements.get('sectionCards').children[0].innerHTML;
 assert.match(html,/Published guide: 45 min/);assert.doesNotMatch(html,/Take out ≈|0.75 hours/);
 h.run('state.river.sections[0].guideTimes[0].min=.5;renderSections(state.river,{flow:1000,at:Date.now()},null)');
 html=h.elements.get('sectionCards').children[0].innerHTML;
 assert.match(html,/Published guide: 30–45 min/);
});
test('published hours and minutes match the server-rendered guide format',()=>{
 const h=harness();fixture(h);
 const cases=JSON.parse(fs.readFileSync(require.resolve('./fixtures/guide-times.json'),'utf8'));
 for(const guide of cases){
  h.context.testGuide={...guide,conditions:'Published guide',sourceName:'Agency',sourceUrl:'https://example.gov'};
  h.run('state.river.timing={mode:"unavailable"};state.river.sections[0].guideTimes=[testGuide];renderSections(state.river,{flow:1000,at:Date.now()},null)');
  const html=h.elements.get('sectionCards').children[0].innerHTML;
  assert.ok(html.includes('Published guide: '+guide.expected),guide.expected);
  assert.doesNotMatch(html,/Take out ≈|Launch by/);
 }
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
 assert.match(html,/Planning distance under review/);assert.doesNotMatch(html,/~4.0 mph|2 hr|8 mi/);assert.match(html,/Distance under review/);
 assert.equal(h.run('P.estimate(state.river,state.river.sections[0],1000,1,0)'),null);
});

test('satellite sources authenticate only to Esri and respect both tile grids',()=>{
 const h=harness();h.context.testKey='public-test&key';
 assert.equal(h.run('satelliteMapStyle(testKey)').sources['imagery-labels'],undefined);
 const style=h.run('satelliteMapStyle(testKey, {labels:true})');
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
 assert.throws(()=>h.run('prepareSectionRoute(record,river,{...section,routeReview:"New portage question"})'),/needs review/);
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

test('Wyoming maps draw reviewed paths without Montana land layers or GPS timing',async()=>{
 const record=require('../public/routes/north-platte-gray-reef-casper--gray-reef-to-lusby.json');
 const catalog=require('../public/catalog.json');const layers=[],sources=[];
 const h=harness(async url=>({ok:true,json:async()=>url==='/api/map-config'?{arcgisApiKey:'test-key',routes:[{riverId:record.riverId,sectionId:record.sectionId,file:'route.json'}]}:record}));
 h.context.riverFixture=catalog.rivers.find(r=>r.id===record.riverId);
 h.context.navigator={};h.context.location={href:'http://localhost/'};h.context.history={replaceState(){}};
 for(const id of ['landMapPanel','landMap']){const e=h.context.document.getElementById(id);e.clientWidth=1000;e.scrollIntoView=()=>{};e.querySelector=()=>h.context.document.createElement('h3');}
 const chain=class {setLngLat(){return this;}setDOMContent(){return this;}setPopup(){return this;}addTo(){return this;}on(){return this;}};
 h.context.mapStub={Map:class {addControl(){}getContainer(){return {clientWidth:1000,querySelector(){return null;}};}on(){}off(){}once(event,fn){if(event==='load')fn();}addSource(id){sources.push(id);}addLayer(layer){layers.push(layer);}remove(){}},LngLatBounds:class{extend(){}},NavigationControl:class{},GeolocateControl:chain,AttributionControl:class{},Popup:chain,Marker:chain};
 h.run('loadMapLibrary=async()=>mapStub;state.river=riverFixture;state.craft={id:"raft",mult:1};');
 await h.run('showLandMap(state.river.sections.find(s=>s.id==="gray-reef-to-lusby"))');
 assert.ok(sources.includes('pilot-river'));assert.equal(sources.includes('mt-trust-land'),false);
 assert.ok(layers.some(l=>l.id==='pilot-river-line'&&l.paint['line-dasharray']));
 assert.equal(h.elements.get('landMapRouteEvidence').hidden,false);
 assert.match(h.elements.get('landMapStatus').textContent,/Approximate river line shown dashed/);
 assert.equal(h.run('state.progress'),null);
});

test('changing state during initial river load discards stale details and linked map',async()=>{
 let releaseDetail, detailStarted;
 const waiting=new Promise(resolve=>{detailStarted=resolve;});
 const oldRiver={...river,id:'old',state:'MT',file:'old.json',sections:[{...river.sections[0],mapReleased:true}]};
 const catalog={rivers:[oldRiver,{...river,id:'new',state:'ID',file:'new.json'}],states:[{id:'MT',name:'Montana',slug:'montana'},{id:'ID',name:'Idaho',slug:'idaho'}],craft:[{id:'raft',label:'Raft',mult:1}]};
 const h=harness(async url=>{
  if(url==='/catalog-index.json')return {ok:true,json:async()=>catalog};
  if(url==='/old.json'){detailStarted();return new Promise(resolve=>{releaseDetail=()=>resolve({ok:true,json:async()=>oldRiver});});}
  throw Error('Unexpected request '+url);
 });
 h.context.Option=class {constructor(text,value){this.textContent=text;this.value=value;}};
 h.context.location={href:'http://localhost/?river=old&state=MT&section=a&map=1',search:'?river=old&state=MT&section=a&map=1'};
 h.context.history={replaceState(){}};
 h.run('renderRiver=()=>{};renderReports=()=>{};loadReports=()=>{};let openedMap=false;showLandMap=()=>{openedMap=true;};');
 const pending=h.run('init()');await waiting;
 const stateSelect=h.elements.get('stateSelect');
 assert.equal(stateSelect.disabled,false);
 stateSelect.value='ID';stateSelect.handlers.change();
 releaseDetail();await pending;
 assert.equal(h.run('state.river'),null);
 assert.equal(h.run('openedMap'),false);
 assert.deepEqual(h.elements.get('riverSelect').children.map(o=>o.value),['','new']);
});

test('unresolved access or mileage holds guide times as well as live estimates',()=>{
 for(const field of ['accessReview','distanceReview']){
  const h=harness();fixture(h);h.context.hold=field;
  h.run('state.river.sections[0][hold]="Unresolved landing";state.river.sections[0].guideTimes=[{min:2,max:3,unit:"hours",conditions:"Earlier guide",sourceName:"Agency",sourceUrl:"https://example.gov"}];renderSections(state.river,{flow:1000,at:Date.now()},null)');
  const html=h.elements.get('sectionCards').children[0].innerHTML;
  assert.match(html,/Unresolved landing/);assert.doesNotMatch(html,/Published guide:|~[\d.]+ mph/);
 }
});

test('an open map survives card refreshes and is parked when closed or no longer reviewed',()=>{
 const h=harness();fixture(h);
 h.context.location={href:'http://localhost/?river=test&section=a&map=1'};h.context.history={replaceState(){}};
 const panel=h.context.document.getElementById('landMapPanel');
 let resized=0,removed=0;
 h.context.liveMap={resize(){resized++;},remove(){removed++;}};
 h.run('state.river.sections[0].mapReleased=true;state.landMapSection="a";state.landMap=liveMap;renderSections(state.river,null,null)');
 const first=h.elements.get('sectionCards').children.at(-1);
 assert.equal(panel.parentElement,first);
 h.run('state.fishing=true;renderSections(state.river,null,null)');
 assert.notEqual(panel.parentElement,first);
 assert.equal(panel.parentElement,h.elements.get('sectionCards').children.at(-1));
 assert.equal(h.run('state.landMap'),h.context.liveMap);
 assert.equal(resized,2);assert.equal(removed,0);
 h.run('state.river.sections[0].mapReleased=false;renderSections(state.river,null,null)');
 assert.equal(panel.parentElement,h.elements.get('landMapHome'));
 assert.equal(panel.hidden,true);assert.equal(removed,1);
 assert.equal(h.run('state.landMapSection'),null);
});

test('state shortcuts filter the planner, preserve craft and respect modified clicks',async()=>{
 const h=harness(async()=>({ok:true,json:async()=>({rivers:[{...river,file:'test.json'},{...river,id:'id-river',state:'ID',file:'id.json'}],states:[{id:'MT',name:'Montana',slug:'montana'},{id:'ID',name:'Idaho',slug:'idaho'}],craft:[{id:'raft',label:'Raft',mult:1},{id:'kayak',label:'Kayak',mult:1.25}]})}));
 const link=h.context.document.createElement('a');link.dataset={plannerState:'ID'};link.closest=()=>null;
 h.context.document.querySelectorAll=()=>[link];
 h.context.Option=class {constructor(text,value){this.textContent=text;this.value=value;}};
 h.context.location={href:'http://localhost/?craft=kayak',search:'?craft=kayak'};
 let lastUrl,prevented=false,focused=false,scrolled=false;
 h.context.history={replaceState(a,b,url){lastUrl=url;h.context.location.href=new URL(url,h.context.location.href).href;}};
 h.context.document.getElementById('riverSelect').focus=()=>{focused=true;};
 h.context.document.getElementById('calculator').scrollIntoView=()=>{scrolled=true;};
 h.run('renderReports=()=>{};loadReports=()=>{};');await h.run('init()');
 link.handlers.click({button:0,ctrlKey:true,preventDefault(){throw Error('Must preserve open-in-new-tab behavior');}});
 assert.equal(h.elements.get('stateSelect').value,'');
 link.handlers.click({button:0,preventDefault(){prevented=true;}});
 assert.ok(prevented&&focused&&scrolled);
 assert.equal(h.elements.get('stateSelect').value,'ID');
 assert.deepEqual(h.elements.get('riverSelect').children.map(o=>o.value),['','id-river']);
 assert.equal(h.run('state.river'),null);
 assert.match(lastUrl,/craft=kayak/);assert.match(lastUrl,/state=ID/);assert.match(lastUrl,/#calculator$/);
});

test('approximate access invites an endpoint-specific correction without downgrading a precise landing',()=>{
 const h=harness();fixture(h);
 h.run('state.river.sections[0].putInAccess={status:"verified"};state.river.sections[0].takeOutAccess={status:"access-verified"};');
 let html=h.run('approximateAccessHelp(state.river,state.river.sections[0])');
 assert.match(html,/endpoint=takeOut/);assert.doesNotMatch(html,/endpoint=putIn/);
 assert.match(html,/Suggestions are reviewed before pins change/);
 h.run('state.river.sections[0].takeOutAccess.status="verified"');
 assert.equal(h.run('approximateAccessHelp(state.river,state.river.sections[0])'),'');
});
