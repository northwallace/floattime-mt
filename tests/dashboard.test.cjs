const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const P=require('../public/planner.js');
function harness(fetch){
 const elements=new Map();
 function element(){return {textContent:'',innerHTML:'',value:'',checked:false,hidden:false,children:[],replaceChildren(){this.children=[];},appendChild(c){this.children.push(c);},setAttribute(){}};}
 const document={getElementById(id){if(!elements.has(id))elements.set(id,element());return elements.get(id);},createElement:element,createElementNS:element};
 const context=vm.createContext({FloatPlanner:P,fetch,document,AbortSignal,Date,Map,Set,URLSearchParams,URL,console});
 const source=fs.readFileSync(require.resolve('../public/app.js'),'utf8').replace(/init\(\);\s*$/,'');
 vm.runInContext(source,context);
 return {run:s=>vm.runInContext(s,context),elements,context};
}
const river={id:'test',name:'Test',state:'MT',gauge:'12345678',timezone:'America/Denver',lat:45,lon:-111,refFlowCfs:1000,refSpeedMph:4,sections:[{id:'a',putIn:'A',takeOut:'B',miles:8,difficulty:'Class I',notes:''}]};
function fixture(h){h.context.fixture=JSON.parse(JSON.stringify(river));h.run('state.river=fixture;state.craft={id:"raft",mult:1};state.reportsStatus="ready";');}
test('gauge parsing rejects missing data, sorts timestamps, and preserves graph',async()=>{
 const now=Date.now(); const iso=n=>new Date(n).toISOString();
 const h=harness(async()=>({ok:true,json:async()=>({value:{timeSeries:[{variable:{variableCode:[{value:'00060'}],noDataValue:-999999},values:[{value:[{value:'200',dateTime:iso(now)},{value:'100',dateTime:iso(now-60000)},{value:'-999999',dateTime:iso(now+1)}]}]}]}})}));
 fixture(h); const result=await h.run('gaugeFor(state.river)');assert.equal(result.flow,200);assert.equal(result.at,now);assert.equal(result.series.length,2);assert.equal(result.series[0].q,100);
});
test('stale reading keeps routes but never shows a calculated duration',()=>{
 const h=harness();fixture(h);h.run('renderSections(state.river,{flow:1000,at:Date.now()-121*60000},null)');
 const html=h.elements.get('sectionCards').children[0].innerHTML;assert.match(html,/No recent, positive flow/);assert.doesNotMatch(html,/2 hr/);assert.match(html,/A/);
});
test('fishing on long routes keeps total hours and rounds days up',()=>{
 const h=harness();fixture(h);h.run('state.river.sections[0].miles=60;state.fishing=true;renderSections(state.river,{flow:1000,at:Date.now()},null)');
 const html=h.elements.get('sectionCards').children[0].innerHTML;assert.match(html,/50 hr/);assert.match(html,/At least 8 floating days/);assert.doesNotMatch(html,/Take out ≈/);
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
