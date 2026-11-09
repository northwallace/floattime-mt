/* Shared, catalog-driven river search. No external search service or detail fetches. */
(function(root,factory){
  const api=factory();
  if(typeof module==='object' && module.exports)module.exports=api;
  else root.FloatSearch=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  function normalize(value){
    return String(value||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase()
      .replace(/[’']/g,'').replace(/\bst\.?\b/g,'saint').replace(/[^a-z0-9]+/g,' ').trim();
  }
  const words=value=>normalize(value).split(' ').filter(Boolean);
  const matches=(tokens,haystack)=>tokens.every(t=>haystack.some(w=>w.startsWith(t)));
  function createIndex(catalog){
    const states=new Map(catalog.states.map(s=>[s.id,s]));
    return catalog.rivers.map(r=>{
      const state=states.get(r.state);
      if(!state)throw new Error('River has no catalog state');
      // Imported titles sometimes append the entire itinerary. Search access
      // names at section level so two unrelated sections cannot make a match.
      const name=r.name.replace(/\s+—\s+.*\s+to\s+.*/i,'');
      const base=words([name,state.name,state.id,...(r.aliases||[])].join(' '));
      return {river:r,state,name,normalizedName:normalize(name),base,
        sections:r.sections.map(s=>{
          const names=[s.putIn,s.takeOut,...(s.putInAliases||[]),...(s.takeOutAliases||[])];
          return {section:s,access:words(names.join(' ')),accessPhrases:names.map(normalize)};
        })};
    });
  }
  function search(index,query,{state='',limit=12}={}){
    const normalized=normalize(String(query||'').slice(0,180));
    let tokens=words(normalized);
    // A standalone or trailing postal code is a state filter, not a partial
    // word such as "wi" in "Willow". "Mt Hersey" remains an access search.
    const last=tokens[tokens.length-1];
    const inferred=last?.length===2 && index.some(e=>e.state.id.toLowerCase()===last) ? last.toUpperCase() : '';
    if(inferred)tokens=tokens.slice(0,-1);
    const rows=[];
    for(const entry of index){
      if((state && entry.state.id!==state)||(inferred && entry.state.id!==inferred))continue;
      const baseMatch=matches(tokens,entry.base);
      const matchedSections=baseMatch?[]:entry.sections.filter(s=>matches(tokens,entry.base.concat(s.access)));
      const sections=matchedSections.map(s=>s.section);
      if(!baseMatch && !sections.length)continue;
      // A phrase typed as an access name ("River Prairie") is more specific
      // than the same words scattered across a river title and another landing.
      // Keep exact river names first and require two words to avoid boosting
      // generic single terms. Match each endpoint/alias separately.
      const accessPhrase=tokens.length>1 && matchedSections.some(s=>
        s.accessPhrases.some(name=>(' '+name).includes(' '+tokens.join(' '))));
      const score=!tokens.length?0:entry.normalizedName===tokens.join(' ')?120:
        entry.normalizedName.startsWith(tokens.join(' '))?100:accessPhrase?90:baseMatch?80:60;
      // Explain an alias-only result: the catalog's agency label may differ
      // from the local name the visitor typed. Keep original section labels
      // and stable links; aliases do not create another landing or trip.
      const accessMatches=[];
      for(const section of sections){
        const canonical=entry.base.concat(words(section.putIn+' '+section.takeOut));
        let missing=[...new Set(tokens.filter(t=>!matches([t],canonical)))];
        const aliases=[...(section.putInAliases||[]),...(section.takeOutAliases||[])];
        while(missing.length){
          let alias='',best=0;
          for(const candidate of aliases){
            const score=missing.filter(t=>matches([t],words(candidate))).length;
            if(score>best){alias=candidate;best=score;}
          }
          if(!alias)break;
          if(!accessMatches.includes(alias))accessMatches.push(alias);
          missing=missing.filter(t=>!matches([t],words(alias)));
        }
      }
      rows.push({river:entry.river,state:entry.state,name:entry.name,sections,accessMatches,score});
    }
    rows.sort((a,b)=>b.score-a.score||a.name.localeCompare(b.name)||a.state.name.localeCompare(b.state.name)||a.river.id.localeCompare(b.river.id));
    return {total:rows.length,rows:rows.slice(0,Math.max(0,limit)),query:normalized};
  }
  function plannerUrl(row,craft){
    const p=new URLSearchParams({state:row.state.id,river:row.river.id});
    if(craft)p.set('craft',craft);
    return '/?'+p+'#calculator';
  }
  function sectionUrl(row,section){return '/rivers/'+encodeURIComponent(row.river.id)+'#access-'+encodeURIComponent(section.id);}
  function addResult(list,row,{planner=false,craft}={}){
    const li=document.createElement('li'),a=document.createElement('a'),meta=document.createElement('span');
    a.href=planner?plannerUrl(row,craft):'/rivers/'+encodeURIComponent(row.river.id);a.textContent=row.name;
    meta.textContent=row.state.name+' · '+row.river.sections.length+' '+(row.river.sections.length===1?'section':'sections');
    li.append(a,meta);
    if(row.accessMatches?.length){
      const match=document.createElement('span');match.className='search-matched-access';
      match.textContent='Matched access: '+row.accessMatches.slice(0,2).join(' · ');li.append(match);
    }
    for(const s of row.sections.slice(0,2)){
      const link=document.createElement('a');link.className='search-section-link';link.href=sectionUrl(row,s);link.textContent=s.putIn+' → '+s.takeOut;li.append(link);
    }
    list.append(li);
  }
  function mountPlanner(catalog,getCraft){
    const form=document.getElementById('plannerSearchForm');if(!form)return;
    const input=document.getElementById('plannerSearch'),panel=document.getElementById('plannerSearchPanel'),list=document.getElementById('plannerSearchResults'),status=document.getElementById('plannerSearchStatus'),all=document.getElementById('plannerSearchAll');
    const index=createIndex(catalog);let timer;
    document.getElementById('plannerSearchHint').textContent='Search '+catalog.rivers.length+' rivers by name, state, put-in or take-out.';
    function render(){
      const q=input.value.trim();list.replaceChildren();panel.hidden=!q;
      if(!q){status.textContent='';return;}
      const result=search(index,q,{limit:5});
      for(const row of result.rows)addResult(list,row,{planner:true,craft:getCraft?.()});
      status.textContent=result.total?(result.total>result.rows.length?`Showing ${result.rows.length} of ${result.total} matching rivers.`:`${result.total} ${result.total===1?'river':'rivers'} found.`):'No matching rivers yet. Try a different name or request a float.';
      all.hidden=!result.total;all.href='/directory.html?'+new URLSearchParams({q});
    }
    input.addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(render,120);});
    input.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();clearTimeout(timer);panel.hidden=true;status.textContent='';}});
    form.addEventListener('submit',()=>{clearTimeout(timer);}); // Native GET works with or without JavaScript.
  }
  return {normalize,createIndex,search,plannerUrl,sectionUrl,addResult,mountPlanner};
});
