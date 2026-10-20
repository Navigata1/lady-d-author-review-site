const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const expected=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../source/finalization/book-inventory.json')));
assert.equal(expected.length,6);
assert.deepEqual(expected.map(r=>`${r.volume}:${r.journal}`).sort(),[1,2,3].flatMap(v=>[`${v}:false`,`${v}:true`]).sort());
function assertInventory(build){
 assert.equal(build.status,'PASS','PDF build has not passed');
 assert(Array.isArray(build.results));assert.equal(build.results.length,6,'Exactly six books are required');
 assert.deepEqual(build.results.map(r=>`${r.volume}:${r.journal}`).sort(),expected.map(r=>`${r.volume}:${r.journal}`).sort(),'Missing, duplicate, or unexpected books');
 for(const item of expected){
  const actual=build.results.find(r=>r.volume===item.volume&&r.journal===item.journal);
  for(const key of ['html','pdf','pages'])assert.equal(actual[key],item[key],`Unexpected ${key}`);
  assert.match(actual.sha256,/^[a-f0-9]{64}$/);assert(actual.bytes>0);
 }
 return build.results;
}
module.exports={expected,assertInventory};
