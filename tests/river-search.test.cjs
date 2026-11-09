const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const S=require('../public/river-search.js');
const catalog=JSON.parse(fs.readFileSync(require.resolve('../public/catalog-index.json'),'utf8'));
const index=S.createIndex(catalog);
test('river and state words match in either order and postal codes are filters',()=>{
  assert.ok(S.search(index,'madison MT').rows.every(x=>x.state.id==='MT'));
  assert.deepEqual(S.search(index,'montana madison').rows.map(x=>x.river.id),S.search(index,'madison montana').rows.map(x=>x.river.id));
  const wi=S.search(index,'wi',{limit:1000});assert.equal(wi.total,catalog.rivers.filter(r=>r.state==='WI').length);assert.ok(wi.rows.every(x=>x.state.id==='WI'));
  assert.ok(S.search(index,'madison WI').rows.every(x=>x.state.id==='WI')); // Madison city accesses also exist.
  assert.equal(S.search(index,'WI',{state:'MT'}).total,0);
});
test('landing search identifies real sections, including former agency names',()=>{
  const result=S.search(index,'palisades mt');
  const upper=result.rows.find(x=>x.river.id==='madison-upper');assert.ok(upper);
  assert.ok(upper.sections.length>0 && upper.sections.every(s=>/palisades/i.test(s.putIn+' '+s.takeOut)));
  const renamed=S.createIndex({states:[{id:'WI',name:'Wisconsin'}],rivers:[{id:'renamed',name:'Renamed River',state:'WI',sections:[{id:'a',putIn:'New Landing',takeOut:'End',putInAliases:['Old Landing']}]}]});
  assert.equal(S.search(renamed,'old landing').rows[0].sections[0].putIn,'New Landing');
});
test('two different sections cannot manufacture a matching float',()=>{
  const idx=S.createIndex({states:[{id:'WI',name:'Wisconsin'}],rivers:[{id:'r',name:'River — Apple to Zebra',state:'WI',sections:[{id:'a',putIn:'Apple',takeOut:'Birch'},{id:'b',putIn:'Yew',takeOut:'Zebra'}]}]});
  assert.equal(S.search(idx,'apple zebra').total,0);assert.equal(S.search(idx,'apple birch').total,1);
});
test('a contiguous access phrase outranks scattered words without hiding exact river names',()=>{
  const states=[{id:'WI',name:'Wisconsin'},{id:'MN',name:'Minnesota'}];
  const rivers=[
    {id:'prairie',name:'Prairie River',state:'WI',sections:[{id:'one',putIn:'Start',takeOut:'End'}]},
    {id:'apple',name:'Apple River',state:'WI',sections:[{id:'one',putIn:'Start',takeOut:'Star Prairie Park'}]},
    {id:'eau-claire',name:'Eau Claire River',state:'WI',sections:[{id:'park-end',putIn:'River Prairie Canoe Launch',takeOut:'End'}]},
    {id:'alias',name:'Other River',state:'MN',sections:[{id:'a-b',putIn:'Official Landing',takeOut:'End',putInAliases:['River Prairie Access']}]}];
  const idx=S.createIndex({states,rivers});
  const result=S.search(idx,'River Prairie WI');
  assert.equal(result.rows[0].river.id,'eau-claire');
  assert.equal(result.rows[0].sections[0].id,'park-end');
  assert.equal(result.total,3);
  assert.equal(S.search(idx,'River Prair',{state:'WI'}).rows[0].river.id,'eau-claire');
  assert.equal(S.search(idx,'River Prairie MN').rows[0].river.id,'alias');
  assert.equal(S.search(idx,'Prairie River WI').rows[0].river.id,'prairie');
  const split=S.createIndex({states,rivers:[{id:'split',name:'Test',state:'WI',sections:[{id:'s',putIn:'River',takeOut:'Prairie'}]}]});
  assert.equal(S.search(split,'River Prairie').rows[0].score,60);
});
test('Soldiers Grove local names find the existing access on both adjoining stretches',()=>{
  const expected=['andrew-s-canoe-landing-to-village-park-access','village-park-access-to-village-park-landing-village-of-gays-mills'].sort();
  for(const query of ['Soldiers Grove','Beauford Anderson','Beauford T. Anderson Park']){
    const result=S.search(index,query);
    assert.equal(result.total,1);
    assert.equal(result.rows[0].river.id,'kickapoo-river');
    assert.deepEqual(result.rows[0].sections.map(s=>s.id).sort(),expected);
    assert.ok(result.rows[0].accessMatches.some(a=>/Soldiers Grove|Beauford/.test(a)));
  }
});
test('alias hints explain the matching landing without leaking names from other stretches',()=>{
  const idx=S.createIndex({states:[{id:'WI',name:'Wisconsin'}],rivers:[{id:'r',name:'River',state:'WI',sections:[
    {id:'a',putIn:'Agency One',takeOut:'Agency Two',putInAliases:['Local Start'],takeOutAliases:['Local End']},
    {id:'b',putIn:'Other One',takeOut:'Other Two',putInAliases:['Unrelated Name']}
  ]}]});
  assert.deepEqual(S.search(idx,'Local Start WI').rows[0].accessMatches,['Local Start']);
  assert.deepEqual(S.search(idx,'Local Start Local End').rows[0].accessMatches,['Local Start','Local End']);
  assert.deepEqual(S.search(idx,'Agency One').rows[0].accessMatches,[]);
  assert.deepEqual(S.search(idx,'River').rows[0].accessMatches,[]);
});
test('punctuation, accents, St/Saint and partial names are normalized',()=>{
  assert.equal(S.normalize("St. Cróix / O’Riley"),'saint croix oriley');
  assert.deepEqual(S.search(index,'St. Croix').rows.map(x=>x.river.id),S.search(index,'saint croix').rows.map(x=>x.river.id));
  assert.ok(S.search(index,'kewaun').rows.some(x=>x.river.id==='kewaunee-river'));
  assert.ok(S.search(index,'mt hersey').rows.some(x=>x.river.id==='buffalo-river'));
});
test('empty and unmatched queries have stable counts and bounded results',()=>{
  assert.equal(S.search(index,'',{limit:5}).rows.length,5);assert.equal(S.search(index,'').total,catalog.rivers.length);
  assert.equal(S.search(index,'zzzz-unlisted-water').total,0);assert.equal(S.search(index,'',{limit:0}).rows.length,0);
});
test('new catalog states require no search configuration and link to stable section IDs',()=>{
  const idx=S.createIndex({states:[{id:'NY',name:'New York'}],rivers:[{id:'future-river',name:'Future River',state:'NY',sections:[{id:'one-two',putIn:'One',takeOut:'Two'}]}]});
  const row=S.search(idx,'future NY').rows[0];assert.equal(row.state.id,'NY');
  assert.equal(S.sectionUrl(row,row.river.sections[0]),'/rivers/future-river#access-one-two');
  assert.match(S.plannerUrl(row,'kayak'),/state=NY&river=future-river&craft=kayak#calculator$/);
});
