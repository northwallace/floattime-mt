/* Pure local GPS-to-river projection. No storage, network or location permission. */
(function(root){
  'use strict';
  const G=typeof module==='object'&&module.exports ? require('./river-route.js') : root.FloatRoute;
  const {prepare,pointAt,distance,validPoint}=G;
  const R=6371008.8,MI=1609.344,rad=Math.PI/180;
  function locate(route,fix,now=Date.now()){
    if(!fix||!validPoint([fix.longitude,fix.latitude]))return {status:'missing'};
    if(!Number.isFinite(fix.timestamp)||now-fix.timestamp>30000||fix.timestamp-now>5000)return {status:'stale'};
    if(!Number.isFinite(fix.accuracy)||fix.accuracy<0||fix.accuracy>50)return {status:'inaccurate'};
    const sx=R*rad*Math.cos(fix.latitude*rad),sy=R*rad;
    const candidates=[];
    for(let i=1;i<route.coordinates.length;i++){
      const a=route.coordinates[i-1],b=route.coordinates[i];
      const ax=(a[0]-fix.longitude)*sx,ay=(a[1]-fix.latitude)*sy,bx=(b[0]-fix.longitude)*sx,by=(b[1]-fix.latitude)*sy;
      const dx=bx-ax,dy=by-ay,t=Math.max(0,Math.min(1,-(ax*dx+ay*dy)/(dx*dx+dy*dy)));
      const offset=Math.hypot(ax+t*dx,ay+t*dy),along=route.cumulative[i-1]+t*(route.cumulative[i]-route.cumulative[i-1]);
      candidates.push({offset,along});
    }
    candidates.sort((a,b)=>a.offset-b.offset); const best=candidates[0];
    if(best.offset>75)return {status:'off-route',offsetMeters:best.offset};
    // Adjacent bends can be spatially close but hundreds of river metres apart.
    if(candidates.some(c=>c.offset<=best.offset+Math.max(20,fix.accuracy)&&Math.abs(c.along-best.along)>400))return {status:'ambiguous'};
    return {status:route.length-best.along<130?'near-takeout':'on-route',remainingMiles:(route.length-best.along)/MI,progress:best.along/route.length,offsetMeters:best.offset};
  }
  const api={prepare,pointAt,locate,distance};
  if(typeof module==='object'&&module.exports)module.exports=api;else root.FloatProgress=api;
})(typeof globalThis!=='undefined'?globalThis:this);
