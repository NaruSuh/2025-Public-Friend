#!/usr/bin/env python3
"""
226개 기초지자체 전수조사 크롤링 스크립트
각 의회당 최근 50개 회의록 수집
"""

import sys
import os
import json
import time
import traceback
from datetime import datetime
from pathlib import Path

# 현재 디렉토리를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from council_crawler import load_basic_councils_from_yaml, get_crawler, ResultSaver

def crawl_all_basic_councils(max_pages=5, output_dir="output/basic_minutes"):
    """226개 기초지자체 전수조사"""

    # 기초의회 목록 로드
    basic_councils = load_basic_councils_from_yaml()

    print(f"=" * 80)
    print(f"📊 226개 기초지자체 전수조사 크롤링")
    print(f"=" * 80)
    print(f"대상: {len(basic_councils)}개 기초지자체")
    print(f"페이지당 회의록: 최대 {max_pages * 10}개 (max_pages={max_pages})")
    print(f"출력 디렉토리: {output_dir}")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"=" * 80)

    # 결과 저장 디렉토리
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    saver = ResultSaver(output_dir)

    # 결과 집계
    results_summary = []
    success_count = 0
    fail_count = 0
    total_meetings = 0
    total_size = 0
    truncation_issues = []  # 500자 이하 문제

    # 진행 상태 파일
    progress_file = Path(output_dir) / "_progress.json"
    completed_codes = set()

    # 이전 진행 상태 로드
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            progress_data = json.load(f)
            completed_codes = set(progress_data.get('completed', []))
            print(f"⏩ 이전 진행 상태 로드: {len(completed_codes)}개 완료됨, 이어서 진행")

    # 정렬된 코드 목록
    council_codes = sorted(basic_councils.keys())

    for idx, code in enumerate(council_codes, 1):
        config = basic_councils[code]
        name = config.get('name', code)
        crawler_type = config.get('crawler_type', 'default')
        note = config.get('note', '')

        # 이미 완료된 경우 스킵
        if code in completed_codes:
            print(f"[{idx:3d}/226] {name:<20} ⏭️  이미 완료됨")
            continue

        # SSL 문제 등 알려진 이슈
        if 'SSL' in note or '접근 불가' in note:
            print(f"[{idx:3d}/226] {name:<20} ⚠️  {note}")
            results_summary.append({
                'code': code,
                'name': name,
                'crawler_type': crawler_type,
                'status': 'skip',
                'reason': note,
                'meetings': 0,
                'size_bytes': 0,
                'avg_content_len': 0,
                'min_content_len': 0,
                'truncation_count': 0
            })
            fail_count += 1
            continue

        print(f"[{idx:3d}/226] {name:<20} ({crawler_type:<12}) ", end="", flush=True)

        try:
            crawler = get_crawler(code)
            if not crawler:
                print("❌ 크롤러 생성 실패")
                results_summary.append({
                    'code': code,
                    'name': name,
                    'crawler_type': crawler_type,
                    'status': 'fail',
                    'reason': '크롤러 생성 실패',
                    'meetings': 0,
                    'size_bytes': 0,
                    'avg_content_len': 0,
                    'min_content_len': 0,
                    'truncation_count': 0
                })
                fail_count += 1
                continue

            # 크롤링 실행
            meetings = []
            content_lengths = []
            truncation_count = 0

            for meeting in crawler.crawl(max_pages=max_pages):
                meetings.append(meeting)
                fc_len = len(meeting.full_content) if meeting.full_content else 0
                content_lengths.append(fc_len)

                # 500자 이하 체크 (truncation 문제 감지)
                if fc_len > 0 and fc_len < 500:
                    truncation_count += 1

            if meetings:
                # 저장
                md_file = saver.save_markdown(code, meetings)
                jsonl_file = saver.save_jsonl(code, meetings)

                file_size = md_file.stat().st_size if md_file.exists() else 0
                avg_len = sum(content_lengths) / len(content_lengths) if content_lengths else 0
                min_len = min(content_lengths) if content_lengths else 0

                print(f"✅ {len(meetings):3d}개 | {file_size/1024:7.1f}KB | avg:{avg_len:,.0f}자", end="")

                if truncation_count > 0:
                    print(f" | ⚠️ {truncation_count}개 <500자")
                    truncation_issues.append({
                        'code': code,
                        'name': name,
                        'crawler_type': crawler_type,
                        'truncation_count': truncation_count,
                        'total': len(meetings),
                        'min_len': min_len
                    })
                else:
                    print()

                results_summary.append({
                    'code': code,
                    'name': name,
                    'crawler_type': crawler_type,
                    'status': 'success',
                    'reason': '',
                    'meetings': len(meetings),
                    'size_bytes': file_size,
                    'avg_content_len': avg_len,
                    'min_content_len': min_len,
                    'truncation_count': truncation_count
                })

                success_count += 1
                total_meetings += len(meetings)
                total_size += file_size

                # 진행 상태 저장
                completed_codes.add(code)
                with open(progress_file, 'w') as f:
                    json.dump({
                        'completed': list(completed_codes),
                        'last_update': datetime.now().isoformat()
                    }, f)
            else:
                print(f"⚠️  회의록 0개")
                results_summary.append({
                    'code': code,
                    'name': name,
                    'crawler_type': crawler_type,
                    'status': 'empty',
                    'reason': '회의록 없음',
                    'meetings': 0,
                    'size_bytes': 0,
                    'avg_content_len': 0,
                    'min_content_len': 0,
                    'truncation_count': 0
                })
                fail_count += 1

            # Rate limiting
            time.sleep(0.5)

        except Exception as e:
            print(f"❌ 오류: {str(e)[:50]}")
            results_summary.append({
                'code': code,
                'name': name,
                'crawler_type': crawler_type,
                'status': 'error',
                'reason': str(e)[:100],
                'meetings': 0,
                'size_bytes': 0,
                'avg_content_len': 0,
                'min_content_len': 0,
                'truncation_count': 0
            })
            fail_count += 1

            # 오류 로그
            with open(Path(output_dir) / "_errors.log", 'a') as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"[{datetime.now()}] {code} - {name}\n")
                f.write(traceback.format_exc())

    # 최종 결과 저장
    summary_file = Path(output_dir) / "_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_councils': len(basic_councils),
            'success_count': success_count,
            'fail_count': fail_count,
            'total_meetings': total_meetings,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / 1024 / 1024,
            'truncation_issues': truncation_issues,
            'results': results_summary
        }, f, ensure_ascii=False, indent=2)

    # 최종 보고
    print(f"\n{'=' * 80}")
    print(f"📊 전수조사 완료")
    print(f"{'=' * 80}")
    print(f"성공: {success_count}개 / 실패: {fail_count}개")
    print(f"총 회의록: {total_meetings:,}개")
    print(f"총 용량: {total_size/1024/1024:.1f}MB")
    print(f"평균 용량/의회: {total_size/success_count/1024:.1f}KB" if success_count > 0 else "")

    if truncation_issues:
        print(f"\n⚠️  500자 미만 truncation 의심: {len(truncation_issues)}개 의회")
        for issue in truncation_issues[:10]:
            print(f"   - {issue['name']}: {issue['truncation_count']}/{issue['total']}개 (min: {issue['min_len']}자)")

    print(f"\n결과 저장: {summary_file}")
    print(f"완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return results_summary

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='226개 기초지자체 전수조사')
    parser.add_argument('--max-pages', type=int, default=5, help='페이지 수 (기본: 5, 약 50개)')
    parser.add_argument('--output', type=str, default='output/basic_minutes', help='출력 디렉토리')
    args = parser.parse_args()

    crawl_all_basic_councils(max_pages=args.max_pages, output_dir=args.output)
