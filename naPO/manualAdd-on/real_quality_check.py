#!/usr/bin/env python3
"""
실제 데이터 품질 검사
- full_content 필드 확인
- 실제 회의록 내용 존재 여부
"""

import json
from pathlib import Path

BASIC_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes")
METRO_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/metro_minutes")

def check_file(file_path: Path) -> dict:
    """파일 데이터 품질 확인"""
    result = {
        "name": file_path.stem,
        "count": 0,
        "has_full_content": 0,
        "full_content_length": 0,
        "has_date": 0,
        "sample_title": "",
        "sample_content_preview": "",
        "quality": "unknown"
    }

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    result["count"] += 1

                    # full_content 확인
                    fc = data.get("full_content", "")
                    if fc and len(fc) > 100:
                        result["has_full_content"] += 1
                        result["full_content_length"] += len(fc)

                    # content_preview 확인
                    cp = data.get("content_preview", "")
                    if cp and len(cp) > 50:
                        result["has_full_content"] += 1

                    # date 확인
                    date = data.get("date", "") or data.get("meeting_date", "")
                    if date:
                        result["has_date"] += 1

                    # 첫 번째 샘플
                    if result["count"] == 1:
                        result["sample_title"] = data.get("title", "")[:50]
                        if fc:
                            result["sample_content_preview"] = fc[:100]
                        elif cp:
                            result["sample_content_preview"] = cp[:100]

                except:
                    pass
    except:
        pass

    # 품질 판정
    if result["count"] == 0:
        result["quality"] = "empty"
    elif result["has_full_content"] > 0:
        result["quality"] = "excellent"  # 실제 내용 있음
    elif result["count"] >= 5:
        result["quality"] = "good"  # 목록만 있지만 충분함
    else:
        result["quality"] = "minimal"

    return result

def main():
    print("=" * 80)
    print("실제 데이터 품질 검사")
    print("=" * 80)

    all_results = []

    # 기초의회
    basic_files = sorted(BASIC_DIR.glob("*.jsonl"))
    for f in basic_files:
        r = check_file(f)
        r["type"] = "basic"
        all_results.append(r)

    # 광역의회
    metro_files = sorted(METRO_DIR.glob("*.jsonl"))
    for f in metro_files:
        r = check_file(f)
        r["type"] = "metro"
        all_results.append(r)

    # 통계
    total = len(all_results)
    total_records = sum(r["count"] for r in all_results)
    total_full_content = sum(r["has_full_content"] for r in all_results)
    total_content_length = sum(r["full_content_length"] for r in all_results)

    excellent = [r for r in all_results if r["quality"] == "excellent"]
    good = [r for r in all_results if r["quality"] == "good"]
    minimal = [r for r in all_results if r["quality"] == "minimal"]
    empty = [r for r in all_results if r["quality"] == "empty"]

    print(f"\n총 의회 수: {total}개")
    print(f"총 레코드 수: {total_records}건")
    print(f"full_content 있는 레코드: {total_full_content}건")
    print(f"총 회의록 텍스트 길이: {total_content_length:,}자")

    print(f"\n✅ 최우수 (full_content 있음): {len(excellent)}개")
    print(f"✅ 양호 (5건 이상 목록): {len(good)}개")
    print(f"⚠️  최소 (5건 미만): {len(minimal)}개")
    print(f"❌ 빈 파일: {len(empty)}개")

    # 최소 품질 의회 상세
    if minimal:
        print(f"\n[최소 품질 의회 상세]")
        for r in minimal:
            print(f"  - {r['name']}: {r['count']}건 | {r['sample_title'][:30]}...")

    # 빈 파일
    if empty:
        print(f"\n[빈 파일]")
        for r in empty:
            print(f"  - {r['name']}")

    # 최우수 샘플
    print(f"\n[최우수 품질 샘플 (full_content 있음)]")
    for r in excellent[:10]:
        avg_len = r["full_content_length"] // max(r["has_full_content"], 1)
        print(f"  - {r['name']}: {r['count']}건, 평균 {avg_len:,}자/건")

    # 최종 요약
    print("\n" + "=" * 80)
    print("최종 결론")
    print("=" * 80)

    success = len(excellent) + len(good)
    print(f"\n✅ 정상 데이터 의회: {success}개 ({100*success/total:.1f}%)")
    print(f"⚠️  최소 데이터 의회: {len(minimal)}개 ({100*len(minimal)/total:.1f}%)")
    print(f"❌ 문제 의회: {len(empty)}개")

if __name__ == "__main__":
    main()
