import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import urllib.error
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
sys.path.insert(0, str(Path(__file__).parents[1] / 'tools/aihot'))
import upstream_api as m
import upstream_reader as reader


def item(key='one', score=68):
    return {'id':key,'title':'Title','summary':'Upstream summary','selected':True,'score':score,
            'publishedAt':datetime.now(timezone.utc).isoformat(), 'links':{'aihot':'https://aihot.news/items/'+key},
            'attribution':{'name':'AIHOT','url':'https://aihot.news/items/'+key}}


def seed(root, items=None, cursor='old'):
    m.atomic_json(root/'selected-state.json',{'cursor':cursor,'items':items or {'one':item()},'removed':[],
        'fetchedAt':(m.now()-timedelta(hours=1)).isoformat(),'complete':True,'privateOnly':True})


class Response:
    status=200;headers={'ETag':'"test"'}
    def __init__(self,url,value):self.url=url;self.value=value
    def __enter__(self):return self
    def __exit__(self,*_):pass
    def geturl(self):return self.url
    def read(self,_):return json.dumps(self.value).encode()


class ApiTests(unittest.TestCase):
    def test_corrections_and_deselection_commit_with_cursor(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);seed(r,{'one':item(),'two':item('two')});api=m.ApiCache(r)
            api.get=lambda *a,**kw:{'schemaVersion':1,'cursor':'new','count':2,'hasMore':False,'changes':[
                {'op':'upsert','item':item('one',90)},{'op':'remove','id':'two'}]}
            out=api.selected();state=json.loads((r/'selected-state.json').read_text())
            self.assertEqual(out['changes'],2);self.assertEqual(state['cursor'],'new')
            self.assertEqual(state['items']['one']['score'],90);self.assertNotIn('two',state['items'])
            self.assertIn('two',state['removed'])
    def test_invalid_page_never_advances_cursor_or_mutates_good_state(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);seed(r);before=(r/'selected-state.json').read_bytes();api=m.ApiCache(r)
            api.get=lambda *a,**kw:{'cursor':'bad','count':2,'hasMore':False,'changes':[
                {'op':'remove','id':'one'},{'op':'upsert','item':item('two',1000)}]}
            with self.assertRaises(ValueError):api.selected()
            self.assertEqual((r/'selected-state.json').read_bytes(),before)
    def test_failed_second_page_resumes_from_committed_first_page(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);seed(r);api=m.ApiCache(r);calls=[]
            def get(path,*a,**kw):
                calls.append(path)
                if len(calls)==2:raise OSError('offline')
                return {'cursor':'middle','count':1,'hasMore':True,'changes':[{'op':'remove','id':'one'}]}
            api.get=get
            with self.assertRaises(OSError):api.selected()
            state=json.loads((r/'selected-state.json').read_text())
            self.assertEqual(state['cursor'],'middle');self.assertFalse(state['complete']);self.assertFalse(state['items'])
    def test_expired_cursor_reseeds_bounded_recent_items(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);seed(r);api=m.ApiCache(r);calls=[]
            def get(path,*a,**kw):
                calls.append(path)
                if len(calls)==1:raise urllib.error.HTTPError(path,409,'expired',{},None)
                if 'snapshot' in path:return {'cursor':'fresh','items':[]}
                if '/items?' in path:return {'items':[item('fresh')]}
                return {'cursor':'fresh-final','count':0,'hasMore':False,'changes':[]}
            api.get=get;self.assertTrue(api.selected()['reset'])
            self.assertEqual(json.loads((r/'selected-state.json').read_text())['cursor'],'fresh-final')
    def test_etag_and_resource_removal(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);api=m.ApiCache(r,lambda req,**kw:Response(req.full_url,{'schemaVersion':1,'items':[]}))
            api.get('/api/v1/hot-topics','hot');path=r/'hot.json'
            def unchanged(req,**kw):
                self.assertEqual(req.get_header('If-none-match'),'"test"')
                raise urllib.error.HTTPError(req.full_url,304,'unchanged',{},None)
            api.opener=unchanged;self.assertEqual(api.get('/api/v1/hot-topics','hot',force=True)['items'],[])
            def gone(req,**kw):raise urllib.error.HTTPError(req.full_url,410,'gone',{},None)
            api.opener=gone
            with self.assertRaises(urllib.error.HTTPError):api.get('/api/v1/hot-topics','hot',force=True)
            self.assertFalse(path.exists())
    def test_story_identity_from_actual_links_and_old_items_bound(self):
        self.assertEqual(m.story_id('https://aihot.virxact.com/story/123-abc'),'123-abc')
        with self.assertRaises(ValueError):m.story_id('https://evil.example/story/123')
        old=item('old');old['publishedAt']=(m.now()-timedelta(days=8)).isoformat()
        self.assertEqual(m.bounded({'old':old}),{})

    def test_malformed_resource_does_not_replace_good_cache(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);api=m.ApiCache(r,lambda req,**kw:Response(req.full_url,{'schemaVersion':1,'items':[]}))
            api.get('/api/v1/hot-topics','hot');before=(r/'hot.json').read_bytes()
            api.opener=lambda req,**kw:Response(req.full_url,{'schemaVersion':1,'items':'broken'})
            with self.assertRaises(ValueError):api.get('/api/v1/hot-topics','hot',force=True)
            self.assertEqual((r/'hot.json').read_bytes(),before)

    def test_rate_limit_stops_remaining_requests(self):
        with tempfile.TemporaryDirectory() as d:
            error=urllib.error.HTTPError('https://aihot.news/feed.xml',429,'rate limited',{},None)
            with patch.object(reader,'sync',side_effect=error) as sync, patch.object(m.ApiCache,'get') as get, patch.object(m.ApiCache,'selected') as selected:
                out=reader.refresh(Path(d),pause=0)
            self.assertEqual(sync.call_count,1);get.assert_not_called();selected.assert_not_called()
            self.assertEqual(out['errors'][0]['http'],429)
            self.assertTrue(all(e['error']=='SkippedAfterRateLimit' for e in out['errors'][1:]))

    def test_corrected_category_and_deselection_leave_all_feed_intact(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);(r/'api').mkdir();updated={**item(),'category':'industry'}
            seed(r/'api',{'one':updated});state=json.loads((r/'api/selected-state.json').read_text());state['removed']=['two']
            m.atomic_json(r/'api/selected-state.json',state)
            original={'items':[item(),item('two')]}
            for name in ('selected','ai-models','all'):m.atomic_json(r/(name+'.json'),original)
            def get(path,*a,**kw):
                return {'items':[]} if 'hot-topics' in path else {'report':{'date':'2026-10-01'}}
            with patch.object(reader,'sync',return_value={}),patch.object(m.ApiCache,'selected',return_value={}),patch.object(m.ApiCache,'get',side_effect=get):
                self.assertFalse(reader.refresh(r,pause=0)['errors'])
            self.assertEqual([i['id'] for i in json.loads((r/'selected.json').read_text())['items']],['one'])
            self.assertFalse(json.loads((r/'ai-models.json').read_text())['items'])
            self.assertEqual(json.loads((r/'all.json').read_text()),original)
