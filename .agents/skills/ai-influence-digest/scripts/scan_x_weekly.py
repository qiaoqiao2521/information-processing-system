#!/usr/bin/env python3
"""Project adapter: browser Google search + optional Jina; no opencli or X API."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from tools.knowledge_pipeline.acquisition.fetch_x_google import main

if __name__ == '__main__':
    manifest = main()
    document = json.loads(manifest.read_text())
    candidates = [{**row, 'handle': row['author'].lstrip('@'),
                   'text': row.get('content') or row.get('summary'),
                   'fetched_at': document['generated_at']} for row in document['items']]
    (manifest.parent / 'candidates.json').write_text(json.dumps(candidates, ensure_ascii=False, indent=2))
    (manifest.parent / 'candidates.md').write_text('\n\n'.join(
        f"## {row['title']}\n{row['url']}\n\n{row['text']}\n\n状态：{row['content_status']}" for row in candidates))
