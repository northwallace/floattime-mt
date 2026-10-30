import http.client,json,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch
import server
from tools import serve_review

class PrivateReviewTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.patchers=[patch.object(server,'DATA_DIR',self.temp.name),patch.object(server,'FEEDBACK_FILE',self.temp.name+'/feedback.json'),patch.object(server,'_feedback_attempts',{})]
  for p in self.patchers:p.start()
  self.http=server.ThreadingHTTPServer(('127.0.0.1',0),serve_review.ReviewHandler);self.thread=threading.Thread(target=self.http.serve_forever,daemon=True);self.thread.start()
 def tearDown(self):
  self.http.shutdown();self.http.server_close();self.thread.join()
  for p in self.patchers:p.stop()
  self.temp.cleanup()
 def req(self,path,body=None,headers=None):
  c=http.client.HTTPConnection('127.0.0.1',self.http.server_port);c.request('POST' if body is not None else 'GET',path,body=json.dumps(body) if body is not None else None,headers={'Content-Type':'application/json',**(headers or {})});r=c.getresponse();status=r.status;value=r.read();c.close();return status,json.loads(value)
 def test_private_review_rejects_remote_host_and_cross_origin_writes(self):
  self.assertEqual(self.req('/api/private-review',headers={'Host':'attacker.example'})[0],403)
  status,data=self.req('/api/private-review');self.assertEqual(status,200)
  body={'id':data['sections'][0]['id'],'status':'reviewed','note':'Test note'}
  self.assertEqual(self.req('/api/private-review/decision',body)[0],403)
  self.assertEqual(self.req('/api/private-review/decision',body,{'X-Review-Token':data['token'],'Origin':'https://attacker.example'})[0],403)
  before=Path(server.PUBLIC,'catalog.json').read_bytes()
  self.assertEqual(self.req('/api/private-review/decision',body,{'X-Review-Token':data['token']})[0],201)
  self.assertEqual(before,Path(server.PUBLIC,'catalog.json').read_bytes())
 def test_typed_pin_reaches_review_with_canonical_access_and_no_auto_publication(self):
  body={'type':'access-suggestion','riverId':'blackfoot','sectionId':'johnsrud-weigh-station','category':'map-location','message':'Test only','location':{'lat':46.91,'lon':-113.7,'pinType':'parking','endpoint':'putIn','method':'manual','status':'verified'}}
  status,response=self.req('/api/feedback',body);self.assertEqual(status,201)
  _,queue=self.req('/api/private-review');entry=next(e for e in queue['submissions'] if e['id']==response['id'])
  self.assertEqual(entry['location']['status'],'community-reported');self.assertEqual(entry['location']['pinType'],'parking');self.assertTrue(entry['accessId'].startswith('acc-'));self.assertEqual(entry['status'],'pending')
  for location in [None,{}, {**body['location'],'lat':True},{**body['location'],'pinType':'verified'}]:
   self.assertEqual(self.req('/api/feedback',{**body,'location':location})[0],400)
