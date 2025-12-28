#!/usr/bin/env python3
"""
226개 기초지자체 전수조사 크롤링 스크립트 (병렬 처리)
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from council_crawler import load_basic_councils_from_yaml, get_crawler, ResultSaver

# 스레드 안전한 출력
print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs, flush=True)

def crawl_single_council(code, config, max_pages, output_dir):
    """단일 의회 크롤링"""
    name = config.get('name', code)
    crawler_type = config.get('crawler_type', 'default')
    note = config.get('note', '')

    result = {
        'code': code,
        'name': name,
        'crawler_type': crawler_type,
        'status': 'unknown',
        'reason': '',
        'meetings': 0,
        'size_bytes': 0,
        'avg_content_len': 0,
        'min_content_len': 0,
        'truncation_count': 0
    }

    # SSL 문제 등 알려진 이슈
    if 'SSL' in note or '접근 불가' in note:
        result['status'] = 'skip'
        result['reason'] = note
        return result

    try:
        crawler = get_crawler(code)
        if not crawler:
            result['status'] = 'fail'
            result['reason'] = '크롤러 생성 실패'
            return result

        # 크롤링 실행
        meetings = []
        content_lengths = []
        truncation_count = 0

        for meeting in crawler.crawl(max_pages=max_pages):
            meetings.append(meeting)
            fc_len = len(meeting.full_content) if meeting.full_content else 0
            content_lengths.append(fc_len)

            if fc_len > 0 and fc_len < 500:
                truncation_count += 1

        if meetings:
            saver = ResultSaver(output_dir)
            md_file = saver.save_markdown(code, meetings)
            saver.save_jsonl(code, meetings)

            file_size = md_file.stat().st_size if md_file.exists() else 0
            avg_len = sum(content_lengths) / len(content_lengths) if content_lengths else 0
            min_len = min(content_lengths) if content_lengths else 0

            result['status'] = 'success'
            result['meetings'] = len(meetings)
            result['size_bytes'] = file_size
            result['avg_content_len'] = avg_len
            result['min_content_len'] = min_len
            result['truncation_count'] = truncation_count
        else:
            result['status'] = 'empty'
            result['reason'] = '회의록 없음'

    except Exception as e:
        result['status'] = 'error'
        result['reason'] = str(e)[:200]

    return result


def crawl_all_parallel(max_pages=5, output_dir="output/basic_minutes", workers=10):
    """병렬 크롤링"""
    basic_councils = load_basic_councils_from_yaml()

    print(f"=" * 80)
    print(f"📊 226개 기초지자체 전수조사 (병렬 {workers} workers)")
    print(f"=" * 80)
    print(f"대상: {len(basic_councils)}개")
    print(f"시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"=" * 80)

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 진행 상태
    progress_file = Path(output_dir) / "_progress.json"
    completed_codes = set()
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            completed_codes = set(json.load(f).get('completed', []))
        print(f"⏩ 이전 진행: {len(completed_codes)}개 완료됨")

    # 미완료 의회만 필터링
    pending = [(code, cfg) for code, cfg in basic_councils.items() if code not in completed_codes]
    print(f"대기: {len(pending)}개")

    results = []
    success = 0
    fail = 0
    total_meetings = 0
    total_size = 0
    truncation_issues = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(crawl_single_council, code, cfg, max_pages, output_dir): (code, cfg)
            for code, cfg in pending
        }

        for i, future in enumerate(as_completed(futures), 1):
            code, cfg = futures[future]
            try:
                result = future.result(timeout=300)
                results.append(result)

                status_icon = {
                    'success': '✅',
                    'fail': '❌',
                    'error': '❌',
                    'skip': '⏭️',
                    'empty': '⚠️'
                }.get(result['status'], '?')

                if result['status'] == 'success':
                    success += 1
                    total_meetings += result['meetings']
                    total_size += result['size_bytes']

                    trunc_warn = ""
                    if result['truncation_count'] > 0:
                        trunc_warn = f" ⚠️{result['truncation_count']}<500"
                        truncation_issues.append(result)

                    safe_print(f"[{i:3d}/{len(pending)}] {result['name']:<16} {status_icon} {result['meetings']:3d}개 {result['size_bytes']/1024:6.1f}KB{trunc_warn}")

                    # 진행 저장
                    completed_codes.add(code)
                    with open(progress_file, 'w') as f:
                        json.dump({'completed': list(completed_codes), 'ts': datetime.now().isoformat()}, f)
                else:
                    fail += 1
                    safe_print(f"[{i:3d}/{len(pending)}] {result['name']:<16} {status_icon} {result['reason'][:30]}")

            except Exception as e:
                fail += 1
                safe_print(f"[{i:3d}/{len(pending)}] {cfg.get('name', code):<16} ❌ timeout/error")

    # 이전 완료된 것도 포함
    for code in completed_codes:
        if code in basic_councils and not any(r['code'] == code for r in results):
            # 파일에서 정보 읽기
            md_file = Path(output_dir) / f"{code}.md"
            if md_file.exists():
                success += 1
                total_size += md_file.stat().st_size

    # 최종 저장
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total': len(basic_councils),
        'success': success,
        'fail': fail,
        'total_meetings': total_meetings,
        'total_size_mb': total_size / 1024 / 1024,
        'truncation_issues': truncation_issues,
        'results': results
    }

    with open(Path(output_dir) / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 80}")
    print(f"📊 완료: 성공 {success} / 실패 {fail}")
    print(f"총 회의록: {total_meetings:,}개")
    print(f"총 용량: {total_size/1024/1024:.1f}MB")
    if truncation_issues:
        print(f"⚠️ 500자 미만 의심: {len(truncation_issues)}개")
    print(f"{'=' * 80}")

    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-pages', type=int, default=5)
    parser.add_argument('--output', default='output/basic_minutes')
    parser.add_argument('--workers', type=int, default=10)
    args = parser.parse_args()

    crawl_all_parallel(args.max_pages, args.output, args.workers)
