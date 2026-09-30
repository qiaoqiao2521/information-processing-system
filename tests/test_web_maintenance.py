"""Test deployment failure recovery and retention against isolated release directories."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from web.maintain import OWNER, activate, collection_status, maintain, prune_releases
from web.refresh import COLLECTORS, DEFAULT_SOURCES


class MaintenanceTests(unittest.TestCase):
    def test_x_is_available_on_demand_but_not_scheduled(self):
        self.assertIn('x', COLLECTORS)
        self.assertNotIn('x', DEFAULT_SOURCES)
        result=collection_status([{'source':'x','status':'paused'}], '2026-09-30T01:00:00Z')
        self.assertIn('暂停', result['sources']['x']['message'])

    def test_public_status_never_exposes_internal_error(self):
        result=collection_status([{'source':'x','status':'failed','error':'/root/private Google challenge: internal-traceback secret-value'}], '2026-09-30T01:00:00Z')
        payload=json.dumps(result)
        self.assertNotIn('/root',payload)
        self.assertNotIn('secret-value',payload)
        self.assertEqual(result['sources']['x']['status'],'failed')
        self.assertIn('Google',result['sources']['x']['message'])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'releases').mkdir()
        self.old = self.release('00-manual')
        (self.root / 'current').symlink_to(self.old)

    def release(self, name, managed=False):
        path = self.root / 'releases' / name
        path.mkdir()
        (path / 'release.json').write_text(json.dumps({'id': name, 'managedBy': OWNER if managed else None}))
        return path

    def test_health_failure_restores_previous_release_and_restarts(self):
        new = self.release('01-new', True)
        restart = Mock()
        verify = Mock(side_effect=[RuntimeError('unhealthy'), None])
        with self.assertRaisesRegex(RuntimeError, 'unhealthy'):
            activate(self.root, new, {'id': '01-new'}, restart, verify)
        self.assertEqual((self.root / 'current').resolve(), self.old)
        self.assertEqual(restart.call_count, 2)
        self.assertEqual(verify.call_args.args[0]['id'], '00-manual')

    def test_retention_only_removes_owned_unprotected_versions(self):
        for number in range(1, 6):
            self.release(f'{number:02d}-auto', True)
        protected = self.root / 'releases' / '01-auto'
        prune_releases(self.root, {self.old, protected}, keep=2)
        self.assertEqual({p.name for p in (self.root / 'releases').iterdir()},
                         {'00-manual', '01-auto', '04-auto', '05-auto'})

    @patch('web.maintain.build_release')
    @patch('web.maintain.refresh_sources', return_value=[{'source': 'juya', 'status': 'failed'}])
    def test_all_sources_failed_does_not_publish(self, refresh, build):
        with self.assertRaisesRegex(RuntimeError, 'All sources failed'):
            maintain(self.root)
        build.assert_not_called()
        self.assertEqual((self.root / 'current').resolve(), self.old)
        report = json.loads((self.root / 'maintenance-last-run.json').read_text())
        self.assertEqual(report['status'], 'failed')
