#!/usr/bin/env python3
"""
수집 진행 상황 확인 스크립트
"""

import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output" / "minutes"

def check_status():
    """진행 상황 확인"""
    print("=" * 60)
    print("CLIK API 회의록 수집 현황")
    print("=" * 60)

    # 진행 상황 파일 확인
    progress_file = DATA_DIR / "progress.json"
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            progress = json.load(f)

        total = progress.get('total_count', 0)
        last_start = progress.get('last_start_count', 1)
        last_updated = progress.get('last_updated', 'N/A')

        if total > 0:
            pct = last_start / total * 100
            print(f"\n[진행 상황]")
            print(f"  전체: {total:,}건")
            print(f"  현재 위치: {last_start:,}건")
            print(f"  진행률: {pct:.1f}%")
            print(f"  마지막 업데이트: {last_updated}")
    else:
        print("\n진행 상황 파일 없음 (아직 시작 안함)")

    # 수집된 DOCID 수
    docids_file = DATA_DIR / "collected_docids.txt"
    if docids_file.exists():
        with open(docids_file, 'r') as f:
            docid_count = sum(1 for _ in f)
        print(f"\n[수집된 문서]")
        print(f"  DOCID 수: {docid_count:,}건")
    else:
        docid_count = 0

    # 의회별 파일 현황
    print(f"\n[저장된 파일]")
    if OUTPUT_DIR.exists():
        files = list(OUTPUT_DIR.glob("*.jsonl"))
        total_records = 0
        total_size = 0

        council_stats = []
        for f in files:
            with open(f, 'r') as fp:
                count = sum(1 for _ in fp)
            size = f.stat().st_size
            total_records += count
            total_size += size
            council_stats.append((f.stem, count, size))

        print(f"  의회 수: {len(files)}개")
        print(f"  총 레코드: {total_records:,}건")
        print(f"  총 용량: {total_size / (1024**2):.1f} MB")

        # 상위 10개 의회
        if council_stats:
            print(f"\n[상위 10개 의회 (레코드 수)]")
            council_stats.sort(key=lambda x: x[1], reverse=True)
            for name, count, size in council_stats[:10]:
                print(f"  - {name}: {count:,}건 ({size/1024:.1f} KB)")
    else:
        print("  저장된 파일 없음")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    check_status()
