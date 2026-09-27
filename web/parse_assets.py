#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
source_file = Path(os.environ.get(
    'MEDIA_STUDIO_CONTENT_ASSETS',
    repo_root.parent / 'muqiao-media-studio' / 'reports' / 'media-studio-15-content-assets.md',
))
content = source_file.read_text(encoding='utf-8')
sections = re.split(r'### 素材\s+(\d+)｜([^\n]+)', content)
items = []

for i in range(1, len(sections), 3):
    idx = sections[i]
    title_raw = sections[i+1].strip()
    body = sections[i+2]
    
    id_m = re.search(r'-\s+\*\*素材 ID：\*\*\s*`([^`]+)`', body)
    format_m = re.search(r'-\s+\*\*内容形态：\*\*\s*([^\n]+)', body)
    viral_title_m = re.search(r'-\s+\*自媒体抓手标题\*：([^\n]+)', body)
    tech_title_m = re.search(r'-\s+\*专业技术标题\*：([^\n]+)', body)
    prompt_m = re.search(r'-\s+\*\*(?:媒体工作站视觉 Prompt|视觉生图 Prompt)[^\n]*?\*\*\s*[:：]?\s*(?:>\s*)?`([^`]+)`', body)
    source_m = re.search(r'-\s+\*\*溯源链接：\*\*\s*`?([^`\n]+)`?', body)
    
    # Extract core facts
    facts = []
    facts_block = re.search(r'-\s+\*\*核心事实增量：\*\*(.*?)(?=-\s+\*\*|$)', body, re.DOTALL)
    if facts_block:
        facts_text = facts_block.group(1)
        for line in facts_text.strip().split('\n'):
            line = line.strip().lstrip('-').lstrip('*').strip()
            if line:
                facts.append(line)

    items.append({
        'id': id_m.group(1) if id_m else f'asset-{idx}',
        'index': idx,
        'category': title_raw.split('：')[0] if '：' in title_raw else '精编选题',
        'rawTitle': title_raw,
        'format': format_m.group(1).strip() if format_m else '短视频/图文',
        'viralTitle': viral_title_m.group(1).strip().replace('《', '').replace('》', '') if viral_title_m else title_raw,
        'techTitle': tech_title_m.group(1).strip().replace('《', '').replace('》', '') if tech_title_m else title_raw,
        'prompt': prompt_m.group(1).strip() if prompt_m else '',
        'source': source_m.group(1).strip() if source_m else '',
        'facts': facts,
        'rawBody': body.strip()
    })

out_file = repo_root / 'web' / 'data' / 'media_assets.json'
out_file.parent.mkdir(parents=True, exist_ok=True)
out_file.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Successfully parsed and saved {len(items)} items to {out_file}')
