/* Shared route geometry. No GPS, networking or permissions. */
(function(root){
  'use strict';
  const R=6371008.8, MI=1609.344, rad=Math.PI/180;
  function validPoint(p){return Array.isArray(p)&&p.length===2&&p.every(Number.isFinite)&&Math.abs(p[0])<=180&&Math.abs(p[1])<=85;}
  function distance(a,b){const x=a[1]*rad,y=b[1]*rad;return 2*R*Math.asin(Math.min(1,Math.sqrt(Math.sin((y-x)/2)**2+Math.cos(x)*Math.cos(y)*Math.sin((b[0]-a[0])*rad/2)**2)));}
  function prepare(data,{displayOnly=false}={}){
    const overview=data?.scope==='river-course-overview';
    if(overview&&(!displayOnly||data.status!=='reviewed'||data.features?.display!==true||data.features?.remainingTime!==false||data.features?.distanceEstimate!==false||!data.overview?.note))throw Error('River-course overview is for display only');
    const distanceReview=data?.overview?.planningDistanceReview;
    if(distanceReview!==undefined&&(!overview||!displayOnly||data.features?.landOverlay!==false||typeof distanceReview!=='string'||!distanceReview.trim()))throw Error('Planning distance review requires a display-only overview');
    const c=data?.geometry?.coordinates;
    if(!['local-pilot','reviewed'].includes(data?.status)||data.geometry.type!=='LineString'||!Array.isArray(c)||c.length<2||c.length>20000||!c.every(validPoint))throw Error('Invalid pilot route');
    const reviewed=data.overview?.longSourceSegments ?? [];
    if(!Array.isArray(reviewed)||new Set(reviewed).size!==reviewed.length||reviewed.some(i=>!Number.isInteger(i)||i<0||i>=c.length-1))throw Error('Invalid reviewed source segments');
    if(reviewed.length&&(!overview||!displayOnly||data.features?.landOverlay!==false))throw Error('Long source segments are for display only');
    const cumulative=[0],longSegments=[];
    for(let i=1;i<c.length;i++){
      const d=distance(c[i-1],c[i]);
      if(d<=.001||d>(reviewed.includes(i-1)?2000:1000))throw Error('Route contains a gap');
      if(d>1000)longSegments.push(i-1);
      cumulative.push(cumulative[i-1]+d);
    }
    if(longSegments.length!==reviewed.length||longSegments.some(i=>!reviewed.includes(i)))throw Error('Reviewed source segments do not match geometry');
    const length=cumulative.at(-1);
    if(!Number.isFinite(data.catalogMiles)||data.catalogMiles<=0||(!distanceReview&&Math.abs(length/MI-data.catalogMiles)/data.catalogMiles>(overview ? .20 : .05)))throw Error('Route mileage needs review');
    return {coordinates:c,cumulative,length,...(overview?{displayOnly:true}:{})};
  }
  function pointAt(route,fraction){
    const target=Math.max(0,Math.min(1,fraction))*route.length;
    let i=1;while(i<route.cumulative.length-1&&route.cumulative[i]<target)i++;
    const t=(target-route.cumulative[i-1])/(route.cumulative[i]-route.cumulative[i-1]);
    return route.coordinates[i-1].map((v,j)=>v+(route.coordinates[i][j]-v)*t);
  }
  const api={prepare,pointAt,distance,validPoint};
  if(typeof module==='object'&&module.exports)module.exports=api;else root.FloatRoute=api;
})(typeof globalThis!=='undefined'?globalThis:this);
