#!/usr/bin/env python3
"""full_content 없는 의회 목록 찾기"""

import json
from pathlib import Path

BASIC_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes")
METRO_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/metro_minutes")

def check_file(file_path: Path) -> bool:
    """full_content 있는지 확인"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    fc = data.get("full_content", "")
                    cp = data.get("content_preview", "")
                    if (fc and len(fc) > 100) or (cp and len(cp) > 100):
                        return True
                except:
                    pass
    except:
        pass
    return False

no_content = []

for f in sorted(BASIC_DIR.glob("*.jsonl")):
    if not check_file(f):
        no_content.append(f.stem)

for f in sorted(METRO_DIR.glob("*.jsonl")):
    if not check_file(f):
        no_content.append(f.stem)

print(f"full_content 없는 의회: {len(no_content)}개")
print(no_content)
