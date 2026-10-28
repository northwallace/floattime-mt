/* Shared route geometry. No GPS, networking or permissions. */
(function(root){
  'use strict';
  const R=6371008.8, MI=1609.344, rad=Math.PI/180;
  function validPoint(p){return Array.isArray(p)&&p.length===2&&p.every(Number.isFinite)&&Math.abs(p[0])<=180&&Math.abs(p[1])<=85;}
  function distance(a,b){const x=a[1]*rad,y=b[1]*rad;return 2*R*Math.asin(Math.min(1,Math.sqrt(Math.sin((y-x)/2)**2+Math.cos(x)*Math.cos(y)*Math.sin((b[0]-a[0])*rad/2)**2)));}
  function prepare(data){
    const c=data?.geometry?.coordinates;
    if(!['local-pilot','reviewed'].includes(data?.status)||data.geometry.type!=='LineString'||!Array.isArray(c)||c.length<2||c.length>20000||!c.every(validPoint))throw Error('Invalid pilot route');
    const cumulative=[0];
    for(let i=1;i<c.length;i++){const d=distance(c[i-1],c[i]);if(d<=0||d>1000)throw Error('Route contains a gap');cumulative.push(cumulative[i-1]+d);}
    const length=cumulative.at(-1);
    if(!Number.isFinite(data.catalogMiles)||data.catalogMiles<=0||Math.abs(length/MI-data.catalogMiles)/data.catalogMiles>.05)throw Error('Route mileage needs review');
    return {coordinates:c,cumulative,length};
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
