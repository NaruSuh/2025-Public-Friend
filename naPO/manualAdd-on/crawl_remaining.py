#!/usr/bin/env python3
"""
미완료 기초지자체 크롤링
"""

import sys
import os
import json
import time
import traceback
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from council_crawler import get_crawler, ResultSaver

print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs, flush=True)

def crawl_single(code, config, max_pages, output_dir):
    name = config.get('name', code)
    crawler_type = config.get('crawler_type', 'default')
    note = config.get('note', '')

    result = {
        'code': code,
        'name': name,
        'crawler_type': crawler_type,
        'status': 'unknown',
        'meetings': 0,
        'size_bytes': 0,
        'avg_content_len': 0,
        'truncation_count': 0
    }

    if 'SSL' in note or '접근 불가' in note:
        result['status'] = 'skip'
        return result

    try:
        crawler = get_crawler(code)
        if not crawler:
            result['status'] = 'fail'
            return result

        meetings = []
        content_lengths = []
        truncation_count = 0

        for meeting in crawler.crawl(max_pages=max_pages):
            meetings.append(meeting)
            fc_len = len(meeting.full_content) if meeting.full_content else 0
            content_lengths.append(fc_len)
            if 0 < fc_len < 500:
                truncation_count += 1

        if meetings:
            saver = ResultSaver(output_dir)
            md_file = saver.save_markdown(code, meetings)
            saver.save_jsonl(code, meetings)

            result['status'] = 'success'
            result['meetings'] = len(meetings)
            result['size_bytes'] = md_file.stat().st_size if md_file.exists() else 0
            result['avg_content_len'] = sum(content_lengths) / len(content_lengths)
            result['truncation_count'] = truncation_count
        else:
            result['status'] = 'empty'

    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)[:100]

    return result


def main():
    output_dir = "output/basic_minutes"
    max_pages = 5
    workers = 8

    # 기초의회 목록 로드
    with open('basic_councils.yaml') as f:
        data = yaml.safe_load(f)

    all_councils = {}
    for region, councils in data.items():
        if isinstance(councils, list):
            for c in councils:
                all_councils[c['code']] = c

    # 완료된 것 확인
    completed = set()
    basic_dir = Path(output_dir)
    for f in basic_dir.glob('*.md'):
        completed.add(f.stem)

    # 미완료만 필터링
    pending = {k: v for k, v in all_councils.items() if k not in completed}

    print(f"=" * 70)
    print(f"📊 미완료 기초지자체 크롤링")
    print(f"=" * 70)
    print(f"전체: {len(all_councils)}개, 완료: {len(completed)}개, 미완료: {len(pending)}개")
    print(f"시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"=" * 70)

    if not pending:
        print("모두 완료됨!")
        return

    results = []
    success = 0
    fail = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(crawl_single, code, cfg, max_pages, output_dir): (code, cfg)
            for code, cfg in pending.items()
        }

        for i, future in enumerate(as_completed(futures), 1):
            code, cfg = futures[future]
            try:
                result = future.result(timeout=300)
                results.append(result)

                if result['status'] == 'success':
                    success += 1
                    trunc = f" ⚠️{result['truncation_count']}<500" if result['truncation_count'] > 0 else ""
                    safe_print(f"[{i:3d}/{len(pending)}] {result['name']:<16} ✅ {result['meetings']:3d}개 {result['size_bytes']/1024:6.1f}KB{trunc}")
                else:
                    fail += 1
                    safe_print(f"[{i:3d}/{len(pending)}] {result['name']:<16} ❌ {result['status']}")

            except Exception as e:
                fail += 1
                safe_print(f"[{i:3d}/{len(pending)}] {cfg.get('name', code):<16} ❌ timeout")

    # 최종 확인
    final_completed = set()
    for f in basic_dir.glob('*.md'):
        final_completed.add(f.stem)

    total_size = sum(f.stat().st_size for f in basic_dir.glob('*.md'))

    print(f"\n{'=' * 70}")
    print(f"📊 완료")
    print(f"완료: {len(final_completed)}/226개")
    print(f"미완료: {226 - len(final_completed)}개")
    print(f"총 용량: {total_size/1024/1024:.1f}MB")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
