const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
function form(query) {
 const elements = new Map();
 function element(id) {
  if (!elements.has(id)) elements.set(id,{value:id==='locationEndpoint'?'putIn':id==='feedbackType'?'float-request':'',textContent:'',hidden:false,handlers:{},addEventListener(type,fn){this.handlers[type]=fn;},replaceChildren(){this.value='';},add(){},appendChild(){},selectedOptions:[{text:'Landing'}]});
  return elements.get(id);
 }
 const context = vm.createContext({document:{getElementById:element},location:{search:query,href:'http://localhost/feedback.html'+query},history:{replaceState(){}},crypto:{randomUUID:()=> 'local-test'},URLSearchParams,URL,Date,AbortSignal,Option:class {constructor(text,value){this.text=text;this.value=value;}},fetch:()=>new Promise(()=>{})});
 vm.runInContext(fs.readFileSync(require.resolve('../public/feedback.js'),'utf8'),context);
 return {element};
}
test('a landing link selects only a valid endpoint and never pre-populates coordinates',()=>{
 for(const [input,expected] of [['takeOut','takeOut'],['putIn','putIn'],['bad-input','putIn']]){
  const f=form('?type=access-suggestion&endpoint='+input+'&lat=45&lon=-112');
  assert.equal(f.element('locationEndpoint').value,expected);
  assert.equal(f.element('locationLat').value,'');assert.equal(f.element('locationLon').value,'');
 }
});
test('switching river, section or endpoint clears a proposed location instead of reassigning it',()=>{
 for(const field of ['feedbackRiver','feedbackSection','locationEndpoint']){
  const f=form('?type=access-suggestion&endpoint=takeOut');
  f.element('locationLat').value='45.8';f.element('locationLon').value='-112.1';f.element('locationLink').value='45.8,-112.1';
  f.element(field).handlers.change();
  for(const id of ['locationLat','locationLon','locationLink'])assert.equal(f.element(id).value,'');
  assert.equal(f.element('locationMap').hidden,true);
 }
});
