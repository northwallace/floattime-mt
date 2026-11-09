const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const code=fs.readFileSync(require.resolve('../public/app.js'),'utf8');
const context=vm.createContext({URL});
vm.runInContext(code.match(/function coordinateSourceLabel\(url\) \{[\s\S]*?\n\}/)[0],context);
test('coordinate attribution identifies the source host, not a lookalike or query string',()=>{
  for(const url of ['https://www.openstreetmap.org/node/12112869326','https://www.openstreetmap.org/node/1?x=2'])
    assert.equal(context.coordinateSourceLabel(url),'Location · © OpenStreetMap contributors');
  for(const url of ['https://fwp.mt.gov/map','https://www.openstreetmap.org.example.com/node/1','https://example.com/?url=https://www.openstreetmap.org'])
    assert.equal(context.coordinateSourceLabel(url),'Location source');
});
