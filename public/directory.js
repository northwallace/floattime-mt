async function initDirectory(){
try {
const catalog=await (await fetch("/catalog.json",{signal:AbortSignal.timeout(15000)})).json();
const RIVERS=catalog.rivers,STATES=catalog.states;
const stateSelect=document.getElementById('directoryState'), search=document.getElementById('directorySearch'), results=document.getElementById('directoryResults'), status=document.getElementById('directoryStatus'), more=document.getElementById('directoryMore');
const escapeText=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
for(const state of STATES)if(!Array.from(stateSelect.options).some(option=>option.value===state.id))stateSelect.add(new Option(state.name,state.id));
const code=new URLSearchParams(location.search).get('state');if(STATES.some(s=>s.id===code))stateSelect.value=code;
let limit=12;
function render(){const q=search.value.trim().toLowerCase();const rows=RIVERS.filter(r=>(!stateSelect.value||(r.state||'MT')===stateSelect.value)&&[r.name,STATES.find(s=>s.id===(r.state||'MT')).name,...r.sections.flatMap(s=>[s.putIn,s.takeOut])].join(' ').toLowerCase().includes(q));results.innerHTML=rows.slice(0,limit).map(r=>`<li><a href="/rivers/${encodeURIComponent(r.id)}">${escapeText(r.name)}</a><span>${escapeText(STATES.find(s=>s.id===(r.state||'MT')).name)} · ${r.sections.length} ${r.sections.length===1?'stretch':'stretches'}</span></li>`).join('');status.textContent=rows.length?`Showing ${Math.min(limit,rows.length)} of ${rows.length} rivers`:'No matching rivers. Try another search or state.';more.hidden=rows.length<=limit;}
stateSelect.addEventListener('change',()=>{limit=12;render()});search.addEventListener('input',()=>{limit=12;render()});more.addEventListener('click',()=>{limit+=12;render()});render();

} catch {document.getElementById("directoryStatus").textContent="The river catalog could not load. Please reload to try again.";document.getElementById("directoryMore").hidden=true;}
}
initDirectory();
