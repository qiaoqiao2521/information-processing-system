"""Exercise the actual HTTP bridge without writing to either daily database."""
import importlib.util
import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / 'web' / 'server.py'
spec = importlib.util.spec_from_file_location('intelligence_hub_server', MODULE_PATH)
hub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hub)


class StudioStub(BaseHTTPRequestHandler):
    received = []

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.received.append(body)
        data = json.dumps({'job': {'id': 'job-123'}}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_args):
        pass


class BridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.studio = HTTPServer(('127.0.0.1', 0), StudioStub)
        cls.hub = HTTPServer(('127.0.0.1', 0), hub.IntelligenceHubHandler)
        hub.MEDIA_STUDIO_API_URL = f'http://127.0.0.1:{cls.studio.server_port}/api/media'
        for server in (cls.studio, cls.hub):
            threading.Thread(target=server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        for server in (cls.hub, cls.studio):
            server.shutdown()
            server.server_close()

    def dispatch(self, data):
        request = urllib.request.Request(
            f'http://127.0.0.1:{self.hub.server_port}/api/studio/dispatch',
            data=json.dumps(data).encode(),
            headers={'Content-Type': 'application/json'},
        )
        return urllib.request.urlopen(request)

    def test_forwards_stable_key_and_kind_model(self):
        StudioStub.received.clear()
        payload = {'prompt': 'test prompt', 'provider': 'stub', 'kind': 'video', 'idempotencyKey': 'request_12345678'}
        for _ in range(2):
            with self.dispatch(payload) as response:
                self.assertTrue(json.load(response)['success'])
        self.assertEqual(len(StudioStub.received), 2)
        self.assertEqual({r['idempotencyKey'] for r in StudioStub.received}, {'request_12345678'})
        self.assertEqual(StudioStub.received[0]['model'], 'default-video')

    def test_rejects_missing_key_without_forwarding(self):
        StudioStub.received.clear()
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.dispatch({'prompt': 'test prompt', 'kind': 'image'})
        self.assertEqual(error.exception.code, 400)
        self.assertEqual(StudioStub.received, [])


if __name__ == '__main__':
    unittest.main()
