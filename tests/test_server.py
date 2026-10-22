import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server

class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.patchers=[patch.object(server,'DATA_DIR',self.temp.name),patch.object(server,'REPORTS_FILE',self.temp.name+'/reports.json'),patch.object(server,'CONTACTS_FILE',self.temp.name+'/contacts.json')]
        for p in self.patchers:p.start()
        self.http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        self.worker=threading.Thread(target=self.http.serve_forever,daemon=True);self.worker.start()
    def tearDown(self):
        self.http.shutdown();self.http.server_close();self.worker.join()
        for p in self.patchers:p.stop()
        self.temp.cleanup()
    def request(self,method,path,body=None):
        c=http.client.HTTPConnection('127.0.0.1',self.http.server_port,timeout=5)
        c.request(method,path,body=json.dumps(body) if body is not None else None,headers={'Content-Type':'application/json'})
        r=c.getresponse();status=r.status;data=r.read();c.close();return status,json.loads(data)
    def test_reports_votes_and_private_metadata(self):
        status,r=self.request('POST','/api/reports',{'riverId':'madison-upper','description':'Test only','type':'strainer'})
        self.assertEqual(status,201)
        self.assertEqual(r['riverId'],'madison-upper')
        self.assertEqual(self.request('POST',f'/api/reports/{r["id"]}/cleared')[0],200)
        self.assertEqual(self.request('POST',f'/api/reports/{r["id"]}/cleared')[0],409)
        r.update(clearedVotes=8,_voters=['private']);server._save_reports([r])
        status,reports=self.request('GET','/api/reports');self.assertEqual(len(reports),1);self.assertNotIn('_voters',reports[0])
    def test_invalid_river_rejected(self):
        self.assertEqual(self.request('POST','/api/reports',{'river':'Invented','description':'Test'})[0],400)

    def test_contact_validation_and_storage(self):
        self.assertEqual(self.request('POST','/api/contact',{
            'name':'River User','email':'not-an-email','message':'Hello'
        })[0],400)
        status,response=self.request('POST','/api/contact',{
            'name':' River User ','email':'RIVER@EXAMPLE.COM','message':' Please add a river. '
        })
        self.assertEqual(status,201)
        self.assertEqual(response,{'ok':True})
        contacts=server._load_contacts()
        self.assertEqual(len(contacts),1)
        self.assertEqual(contacts[0]['email'],'river@example.com')
        self.assertEqual(contacts[0]['message'],'Please add a river.')
    def test_expired_reports_hidden(self):
        server._save_reports([{'id':'abc','createdAt':time.time()-46*86400}])
        self.assertEqual(self.request('GET','/api/reports')[1],[])
