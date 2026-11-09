const test=require('node:test'),assert=require('node:assert/strict');
const R=require('../public/river-route.js'),GPS=require('../public/route-progress.js');
const data=require('../public/routes/jefferson-upper--silver-star-parsons.json');
test('partial river courses can render without becoming GPS routes',()=>{
  assert.throws(()=>R.prepare(data),/display only/);
  assert.throws(()=>GPS.prepare(data),/display only/);
  const route=R.prepare(data,{displayOnly:true});
  assert.ok(route.length/1609.344>9.4&&route.length/1609.344<9.5);
  const p=R.pointAt(route,.5),fix={longitude:p[0],latitude:p[1],accuracy:5,timestamp:1000};
  assert.deepEqual(GPS.locate(route,fix,1000),{status:'display-only'});
});
test('display mode does not enable future features or unlimited mileage differences',()=>{
  for(const key of ['remainingTime','distanceEstimate']){
    assert.throws(()=>R.prepare({...data,features:{...data.features,[key]:true}},{displayOnly:true}));
  }
  assert.throws(()=>R.prepare({...data,catalogMiles:20},{displayOnly:true}),/mileage/);
  assert.throws(()=>R.prepare({...data,geometry:{type:'LineString',coordinates:[[0,0],[1,1]]}},{displayOnly:true}),/gap/);
});
