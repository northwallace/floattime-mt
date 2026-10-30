/* Location evidence parsing is pure; submissions remain unreviewed. */
(function(root){
  'use strict';
  function valid(lat,lon){return Number.isFinite(lat)&&Number.isFinite(lon)&&Math.abs(lat)<=85&&Math.abs(lon)<=180;}
  function parse(text){
    const value=String(text).trim();
    const pair=value.match(/^(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$/) || value.match(/(?:@|[?&](?:q|query|ll)=)(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)/) || value.match(/!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)/);
    if(!pair||!valid(+pair[1],+pair[2]))throw Error('Enter latitude, longitude or a full map link containing coordinates.');
    return {lat:+pair[1],lon:+pair[2]};
  }
  const api={valid,parse};
  if(typeof module==='object'&&module.exports)module.exports=api;else root.AccessLocation=api;
})(typeof globalThis!=='undefined'?globalThis:this);
