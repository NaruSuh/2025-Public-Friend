#!/usr/bin/env python3
"""
243개 전체 의회 전수조사
- 모든 파일 존재 여부
- 레코드 수
- 데이터 품질 (메뉴 링크 vs 실제 회의록)
- 첫 번째 레코드 샘플
"""

import json
from pathlib import Path
import re

BASIC_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes")
METRO_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/metro_minutes")

# 메뉴/네비게이션 키워드 (이것만 있으면 문제)
MENU_KEYWORDS = [
    "회의록검색", "최근회의록", "전자회의록", "영상회의록",
    "본회의/위원회", "조례제정", "조례제정절차", "행정감사",
    "게시판", "참여마당", "의회에 바란다", "청원", "진정",
    "행정감사/조사", "행정사무감사", "의원소개", "의장인사말"
]

# 실제 회의록 패턴
MINUTE_PATTERNS = [
    r'제\s*\d+\s*회',           # 제XXX회
    r'\d{4}년\s*\d+월',         # 2024년 12월
    r'\d+차\s*(본회의|위원회)',  # 3차 본회의
    r'(본회의|위원회|정례회|임시회).*\d',  # 본회의 + 숫자
    r'\d{4}\.\d{2}\.\d{2}',     # 2025.12.19
]

def is_menu_only(title: str) -> bool:
    """제목이 메뉴 링크인지 확인"""
    title_clean = title.strip()

    # 메뉴 키워드만 있는지 확인
    for kw in MENU_KEYWORDS:
        if kw == title_clean or title_clean.startswith(kw):
            # 하지만 실제 회의록 패턴이 있으면 OK
            for pattern in MINUTE_PATTERNS:
                if re.search(pattern, title_clean):
                    return False
            return True

    return False

def is_actual_minute(title: str) -> bool:
    """제목이 실제 회의록인지 확인"""
    for pattern in MINUTE_PATTERNS:
        if re.search(pattern, title):
            return True
    return False

def analyze_file(file_path: Path) -> dict:
    """파일 분석"""
    result = {
        "name": file_path.stem,
        "exists": file_path.exists(),
        "count": 0,
        "titles": [],
        "menu_count": 0,
        "minute_count": 0,
        "quality": "unknown",
        "first_title": "",
        "issue": ""
    }

    if not file_path.exists():
        result["quality"] = "missing"
        result["issue"] = "파일 없음"
        return result

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    title = data.get("title", "").strip()
                    result["titles"].append(title)
                    result["count"] += 1

                    if is_menu_only(title):
                        result["menu_count"] += 1
                    if is_actual_minute(title):
                        result["minute_count"] += 1

                except json.JSONDecodeError:
                    continue
    except Exception as e:
        result["quality"] = "error"
        result["issue"] = str(e)
        return result

    if result["count"] == 0:
        result["quality"] = "empty"
        result["issue"] = "레코드 없음"
    elif result["count"] < 5:
        if result["minute_count"] > 0:
            result["quality"] = "few_but_valid"
            result["issue"] = f"{result['count']}건 (실제 회의록 {result['minute_count']}건)"
        else:
            result["quality"] = "few_records"
            result["issue"] = f"{result['count']}건만 있음"
    elif result["menu_count"] == result["count"]:
        result["quality"] = "menu_only"
        result["issue"] = "메뉴 링크만 있음"
    elif result["menu_count"] > result["count"] * 0.5:
        result["quality"] = "mostly_menu"
        result["issue"] = f"메뉴 {result['menu_count']}/{result['count']}건"
    elif result["minute_count"] == 0:
        result["quality"] = "no_minutes"
        result["issue"] = "회의록 패턴 없음"
    else:
        result["quality"] = "good"

    if result["titles"]:
        result["first_title"] = result["titles"][0][:60]

    return result

def main():
    print("=" * 80)
    print("243개 전체 의회 전수조사")
    print("=" * 80)

    all_results = []

    # 기초의회
    print("\n[1] 기초의회 검사 중...")
    basic_files = sorted(BASIC_DIR.glob("*.jsonl"))
    for f in basic_files:
        result = analyze_file(f)
        result["type"] = "basic"
        all_results.append(result)

    # 광역의회
    print("[2] 광역의회 검사 중...")
    metro_files = sorted(METRO_DIR.glob("*.jsonl"))
    for f in metro_files:
        result = analyze_file(f)
        result["type"] = "metro"
        all_results.append(result)

    # 통계 계산
    total = len(all_results)
    total_records = sum(r["count"] for r in all_results)

    good = [r for r in all_results if r["quality"] == "good"]
    few_valid = [r for r in all_results if r["quality"] == "few_but_valid"]
    few_records = [r for r in all_results if r["quality"] == "few_records"]
    menu_only = [r for r in all_results if r["quality"] == "menu_only"]
    mostly_menu = [r for r in all_results if r["quality"] == "mostly_menu"]
    no_minutes = [r for r in all_results if r["quality"] == "no_minutes"]
    empty = [r for r in all_results if r["quality"] == "empty"]
    missing = [r for r in all_results if r["quality"] == "missing"]
    error = [r for r in all_results if r["quality"] == "error"]

    # 결과 출력
    print("\n" + "=" * 80)
    print("전수조사 결과")
    print("=" * 80)

    print(f"\n총 의회 수: {total}개")
    print(f"총 레코드 수: {total_records}건")

    print(f"\n✅ 양호 (good): {len(good)}개")
    print(f"✅ 소수지만 유효 (few_but_valid): {len(few_valid)}개")

    if few_records:
        print(f"\n⚠️  레코드 부족: {len(few_records)}개")
        for r in few_records:
            print(f"   - {r['name']}: {r['issue']} | {r['first_title'][:40]}...")

    if menu_only:
        print(f"\n❌ 메뉴만 있음: {len(menu_only)}개")
        for r in menu_only:
            print(f"   - {r['name']}: {r['issue']} | {r['first_title'][:40]}...")

    if mostly_menu:
        print(f"\n⚠️  메뉴 다수: {len(mostly_menu)}개")
        for r in mostly_menu:
            print(f"   - {r['name']}: {r['issue']} | {r['first_title'][:40]}...")

    if no_minutes:
        print(f"\n⚠️  회의록 패턴 없음: {len(no_minutes)}개")
        for r in no_minutes[:20]:  # 최대 20개만
            print(f"   - {r['name']}: {r['count']}건 | {r['first_title'][:40]}...")
        if len(no_minutes) > 20:
            print(f"   ... 외 {len(no_minutes) - 20}개")

    if empty:
        print(f"\n❌ 빈 파일: {len(empty)}개")
        for r in empty:
            print(f"   - {r['name']}")

    if missing:
        print(f"\n❌ 파일 없음: {len(missing)}개")
        for r in missing:
            print(f"   - {r['name']}")

    if error:
        print(f"\n❌ 오류: {len(error)}개")
        for r in error:
            print(f"   - {r['name']}: {r['issue']}")

    # 최종 요약
    success = len(good) + len(few_valid)
    problem = len(menu_only) + len(empty) + len(missing) + len(error)

    print("\n" + "=" * 80)
    print("최종 요약")
    print("=" * 80)
    print(f"\n✅ 정상 데이터: {success}개 ({100*success/total:.1f}%)")
    print(f"⚠️  주의 필요: {len(few_records) + len(mostly_menu) + len(no_minutes)}개")
    print(f"❌ 심각한 문제: {problem}개")

    # 상세 리스트 출력 (전체)
    print("\n" + "=" * 80)
    print("전체 의회 상세 목록")
    print("=" * 80)

    for i, r in enumerate(all_results, 1):
        status = "✅" if r["quality"] in ["good", "few_but_valid"] else "⚠️" if r["quality"] in ["few_records", "no_minutes"] else "❌"
        print(f"{i:3}. [{r['type']:5}] {status} {r['name']:20} | {r['count']:4}건 | {r['quality']:15} | {r['first_title'][:35]}...")

if __name__ == "__main__":
    main()
