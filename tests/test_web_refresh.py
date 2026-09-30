"""Failed live collection must never turn a good snapshot into a fresh empty feed."""
import json
from pathlib import Path
import tempfile
import unittest

from web.refresh import COLLECTORS, promote


class RefreshTests(unittest.TestCase):
    def test_invalid_result_retains_previous_snapshot_and_timestamp(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output, staged = root / 'output', root / 'staged'
            output.mkdir(); staged.mkdir()
            name = COLLECTORS['juya'][1]
            existing = output / name
            existing.write_text('{"date":"2026-09-26","items":[{"title":"old"}]}')
            original, timestamp = existing.read_bytes(), existing.stat().st_mtime_ns
            for items in ([], [{'title': 'unsafe', 'url': 'javascript:bad'}]):
                (staged / name).write_text(json.dumps({'items': items, 'generated_at': '2026-09-30T00:00:00Z'}))
                with self.assertRaises(ValueError):
                    promote('juya', staged, output, root / 'backup')
                self.assertEqual(existing.read_bytes(), original)
                self.assertEqual(existing.stat().st_mtime_ns, timestamp)

    def test_new_collection_preserves_edition_date_and_backups(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output, staged = root / 'output', root / 'staged'
            output.mkdir(); staged.mkdir()
            name = COLLECTORS['juya'][1]
            (output / name).write_text('old valid snapshot')
            document = {'date': '2026-09-29', 'generated_at': '2026-09-29T17:00:00Z',
                        'items': [{'title': 'new edition', 'url': 'https://example.com/post'}]}
            (staged / name).write_text(json.dumps(document))
            result = promote('juya', staged, output, root / 'backup')
            self.assertEqual(result['editionDate'], '2026-09-29')
            self.assertEqual(json.loads((output / name).read_text()), document)
            self.assertEqual((root / 'backup' / name).read_text(), 'old valid snapshot')
