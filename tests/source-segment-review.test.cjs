const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const route=require('../public/river-route.js');
const source=JSON.parse(fs.readFileSync(path.join(__dirname,'../public/routes/root-river-mn--hokah-highway26.json'),'utf8'));
test('reviewed long source segment renders only as an overview',()=>{
  const prepared=route.prepare(source,{displayOnly:true});assert.equal(prepared.displayOnly,true);assert.ok(prepared.length>4000);
  assert.throws(()=>route.prepare(source));
  for(const flag of ['remainingTime','distanceEstimate','landOverlay']){const r=structuredClone(source);r.features[flag]=true;assert.throws(()=>route.prepare(r,{displayOnly:true}));}
});
test('long-segment metadata cannot excuse arbitrary gaps or ordinary routes',()=>{
  for(const change of ['missing','duplicate','wrong','negative','float','extra','ordinary','over-cap','zero-length']){
    const r=structuredClone(source);
    if(change==='missing')delete r.overview.longSourceSegments;
    if(change==='duplicate')r.overview.longSourceSegments=[35,35];
    if(change==='wrong')r.overview.longSourceSegments=[34];
    if(change==='negative')r.overview.longSourceSegments=[-1];
    if(change==='float')r.overview.longSourceSegments=[35.5];
    if(change==='extra')r.overview.longSourceSegments=[35,36];
    if(change==='ordinary')r.scope='landing-to-landing';
    if(change==='over-cap')r.geometry.coordinates[36][0]+=.03;
    if(change==='zero-length')r.geometry.coordinates[1]=r.geometry.coordinates[0];
    assert.throws(()=>route.prepare(r,{displayOnly:true}),change);
  }
});
