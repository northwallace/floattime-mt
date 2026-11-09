async function initDirectory(){
  const stateSelect=document.getElementById('directoryState'),input=document.getElementById('directorySearch'),results=document.getElementById('directoryResults'),status=document.getElementById('directoryStatus'),more=document.getElementById('directoryMore');
  try {
    const response=await fetch('/catalog-index.json',{signal:AbortSignal.timeout(15000)});
    if(!response.ok)throw new Error('Catalog unavailable');
    const catalog=await response.json(),index=FloatSearch.createIndex(catalog);
    for(const state of catalog.states)if(!Array.from(stateSelect.options).some(o=>o.value===state.id))stateSelect.add(new Option(state.name,state.id));
    const params=new URLSearchParams(location.search),code=(params.get('state')||'').toUpperCase();
    if(catalog.states.some(s=>s.id===code))stateSelect.value=code;
    input.value=(params.get('q')||'').slice(0,180);
    let limit=12,timer;
    function render(updateUrl=true){
      const result=FloatSearch.search(index,input.value,{state:stateSelect.value,limit});results.replaceChildren();
      for(const row of result.rows)FloatSearch.addResult(results,row);
      status.textContent=result.total?`Showing ${result.rows.length} of ${result.total} rivers`:'No matching rivers. Try another name or state, or request a float above.';
      more.hidden=result.total<=limit;
      if(updateUrl){
        const url=new URL(location.href);
        for(const [key,value] of [['q',input.value.trim()],['state',stateSelect.value]])value?url.searchParams.set(key,value):url.searchParams.delete(key);
        history.replaceState(null,'',url.pathname+url.search+url.hash);
      }
    }
    stateSelect.addEventListener('change',()=>{clearTimeout(timer);limit=12;render();});
    input.addEventListener('input',()=>{clearTimeout(timer);limit=12;timer=setTimeout(render,120);});
    more.addEventListener('click',()=>{limit+=12;render();});render(false);
  } catch {
    // Preserve the server-rendered river links when JS or the network fails.
    status.textContent='Live search could not load. The river links below are still available; reload to try search again.';
    more.hidden=true;
  }
}
initDirectory();
