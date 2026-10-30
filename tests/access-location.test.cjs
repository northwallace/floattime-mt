const {test}=require('node:test');
const assert=require('node:assert/strict');
const A=require('../public/access-location.js');
test('coordinate input accepts pairs and explicit Google links; rejects guesses',()=>{
 assert.deepEqual(A.parse('46.123, -114.456'),{lat:46.123,lon:-114.456});
 assert.deepEqual(A.parse('https://maps.google.com/@46.123,-114.456,18z'),{lat:46.123,lon:-114.456});
 assert.deepEqual(A.parse('https://www.google.com/maps/place/x/data=!3d46.123!4d-114.456'),{lat:46.123,lon:-114.456});
 for(const v of ['90, 0','NaN, 45','46, -200','https://maps.app.goo.gl/short','parking lot'])assert.throws(()=>A.parse(v));
});
