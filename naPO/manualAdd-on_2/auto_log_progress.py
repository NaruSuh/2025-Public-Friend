#!/usr/bin/env python3
"""
진행 상황 자동 기록 스크립트
- 1시간마다 PROGRESS.md에 자동 기록
- cron 또는 백그라운드로 실행
"""

import json
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output" / "minutes"
PROGRESS_MD = BASE_DIR / "PROGRESS.md"
LOG_FILE = BASE_DIR / "data" / "progress_history.jsonl"


def get_current_status():
    """현재 상태 수집"""
    status = {
        "timestamp": datetime.now().isoformat(),
        "total_count": 0,
        "current_position": 0,
        "collected_count": 0,
        "council_count": 0,
        "total_size_mb": 0,
    }

    # progress.json에서 읽기
    progress_file = DATA_DIR / "progress.json"
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            progress = json.load(f)
        status["total_count"] = progress.get("total_count", 0)
        status["current_position"] = progress.get("last_start_count", 0)

    # collected_docids.txt 카운트
    docids_file = DATA_DIR / "collected_docids.txt"
    if docids_file.exists():
        with open(docids_file, 'r') as f:
            status["collected_count"] = sum(1 for _ in f)

    # 의회별 파일 현황
    if OUTPUT_DIR.exists():
        files = list(OUTPUT_DIR.glob("*.jsonl"))
        status["council_count"] = len(files)
        status["total_size_mb"] = sum(f.stat().st_size for f in files) / (1024**2)

    return status


def append_to_history(status):
    """히스토리 파일에 추가"""
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(status, ensure_ascii=False) + '\n')


def update_progress_md(status):
    """PROGRESS.md 업데이트"""
    if not PROGRESS_MD.exists():
        return

    with open(PROGRESS_MD, 'r') as f:
        content = f.read()

    # 진행 상황 섹션 찾아서 업데이트
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    pct = (status["current_position"] / status["total_count"] * 100) if status["total_count"] > 0 else 0

    new_entry = f"- {timestamp} - {status['collected_count']:,}건 수집 ({pct:.1f}%), {status['council_count']}개 의회, {status['total_size_mb']:.1f}MB\n"

    # "### 2024-12-29" 다음 줄에 추가
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith("### 2024-12-29") or line.startswith("### 2025-"):
            # 해당 날짜 섹션의 마지막 항목 다음에 추가
            j = i + 1
            while j < len(lines) and lines[j].startswith("- "):
                j += 1
            lines.insert(j, new_entry.strip())
            break

    # 마지막 업데이트 날짜 변경
    for i, line in enumerate(lines):
        if line.startswith("*마지막 업데이트:"):
            lines[i] = f"*마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
            break

    with open(PROGRESS_MD, 'w') as f:
        f.write('\n'.join(lines))


def run_once():
    """한 번 실행"""
    status = get_current_status()
    append_to_history(status)
    update_progress_md(status)

    pct = (status["current_position"] / status["total_count"] * 100) if status["total_count"] > 0 else 0
    print(f"[{status['timestamp']}] {status['collected_count']:,}건 ({pct:.1f}%) - {status['total_size_mb']:.1f}MB")


def run_daemon(interval_minutes=60):
    """데몬 모드로 실행 (기본 1시간 간격)"""
    print(f"진행 상황 자동 기록 시작 (간격: {interval_minutes}분)")
    while True:
        try:
            run_once()
        except Exception as e:
            print(f"오류: {e}")
        time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='진행 상황 자동 기록')
    parser.add_argument('--daemon', action='store_true', help='데몬 모드 (1시간 간격)')
    parser.add_argument('--interval', type=int, default=60, help='기록 간격 (분)')
    args = parser.parse_args()

    if args.daemon:
        run_daemon(args.interval)
    else:
        run_once()
