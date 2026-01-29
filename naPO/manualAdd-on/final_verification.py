#!/usr/bin/env python3
"""
최종 검증 스크립트
- 243개 전체 의회 데이터 품질 확인
"""

import json
from pathlib import Path
from collections import defaultdict

BASIC_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes")
METRO_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/metro_minutes")

def count_records(file_path):
    """파일의 레코드 수 카운트"""
    count = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    count += 1
    except:
        pass
    return count

def check_quality(file_path):
    """파일의 데이터 품질 체크"""
    records = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except:
                        pass
    except:
        pass

    if not records:
        return {"count": 0, "quality": "empty", "sample": ""}

    # 메뉴 링크인지 실제 회의록인지 확인
    menu_keywords = ["회의록검색", "전자회의록", "영상회의록", "본회의/위원회",
                    "조례제정", "행정감사", "게시판", "참여마당"]

    menu_count = 0
    for r in records:
        title = r.get("title", "")
        if any(kw in title for kw in menu_keywords):
            menu_count += 1

    # 품질 판정
    if menu_count == len(records):
        quality = "menu_only"
    elif menu_count > len(records) / 2:
        quality = "mostly_menu"
    elif len(records) < 5:
        quality = "few_records"
    else:
        quality = "good"

    sample_title = records[0].get("title", "")[:50] if records else ""

    return {
        "count": len(records),
        "quality": quality,
        "sample": sample_title
    }

def main():
    print("=" * 70)
    print("전체 243개 의회 최종 검증")
    print("=" * 70)

    # 기초의회 검사
    print("\n[기초의회]")
    basic_files = list(BASIC_DIR.glob("*.jsonl"))
    basic_results = defaultdict(list)
    basic_total = 0

    for f in sorted(basic_files):
        info = check_quality(f)
        basic_results[info["quality"]].append((f.stem, info["count"], info["sample"]))
        basic_total += info["count"]

    print(f"파일 수: {len(basic_files)}개")
    print(f"총 레코드: {basic_total}건")

    # 광역의회 검사
    print("\n[광역의회]")
    metro_files = list(METRO_DIR.glob("*.jsonl"))
    metro_results = defaultdict(list)
    metro_total = 0

    for f in sorted(metro_files):
        info = check_quality(f)
        metro_results[info["quality"]].append((f.stem, info["count"], info["sample"]))
        metro_total += info["count"]

    print(f"파일 수: {len(metro_files)}개")
    print(f"총 레코드: {metro_total}건")

    # 품질별 분류
    print("\n" + "=" * 70)
    print("품질별 분류")
    print("=" * 70)

    all_results = {}
    for k, v in basic_results.items():
        all_results[k] = all_results.get(k, []) + v
    for k, v in metro_results.items():
        all_results[k] = all_results.get(k, []) + v

    good_councils = all_results.get("good", [])
    few_records = all_results.get("few_records", [])
    menu_only = all_results.get("menu_only", [])
    mostly_menu = all_results.get("mostly_menu", [])
    empty = all_results.get("empty", [])

    print(f"\n✅ 양호 (good): {len(good_councils)}개")

    print(f"\n⚠️  레코드 부족 (<5건): {len(few_records)}개")
    for name, count, sample in few_records[:10]:
        print(f"   - {name}: {count}건 | {sample[:30]}...")
    if len(few_records) > 10:
        print(f"   ... 외 {len(few_records) - 10}개")

    print(f"\n❌ 메뉴만 있음: {len(menu_only)}개")
    for name, count, sample in menu_only:
        print(f"   - {name}: {count}건 | {sample[:30]}...")

    print(f"\n⚠️  메뉴 다수: {len(mostly_menu)}개")
    for name, count, sample in mostly_menu:
        print(f"   - {name}: {count}건 | {sample[:30]}...")

    print(f"\n❌ 빈 파일: {len(empty)}개")
    for name, count, sample in empty:
        print(f"   - {name}")

    # 최종 요약
    print("\n" + "=" * 70)
    print("최종 요약")
    print("=" * 70)
    total_files = len(basic_files) + len(metro_files)
    total_records = basic_total + metro_total
    success_count = len(good_councils) + len(few_records)  # 데이터가 있는 것

    print(f"\n총 의회 수: {total_files}개")
    print(f"총 레코드 수: {total_records}건")
    print(f"데이터 있는 의회: {success_count}개 ({100*success_count/total_files:.1f}%)")
    print(f"문제 의회: {len(menu_only) + len(empty)}개")

    # 문제 의회 리스트
    if menu_only or empty:
        print("\n[재처리 필요 의회]")
        for name, _, _ in menu_only + empty:
            print(f"  - {name}")

if __name__ == "__main__":
    main()
