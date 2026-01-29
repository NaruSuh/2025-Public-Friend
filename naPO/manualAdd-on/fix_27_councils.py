#!/usr/bin/env python3
"""
27개 문제 의회 재크롤링 스크립트
- 메뉴 링크만 추출된 의회들을 CLIK 포털에서 실제 회의록 데이터로 재크롤링
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
from datetime import datetime
from pathlib import Path
import re

# 문제가 있는 27개 의회 목록
PROBLEM_COUNCILS = [
    "bonghwa", "boseong", "buan", "buk_gwangju", "cheongsong",
    "chilgok", "damyang", "gangjin", "goheung", "gokseong",
    "gurye", "hadong", "hapcheon", "hoengseong", "imsil",
    "jung_busan", "jung_daegu", "muan", "nam_gwangju",
    "seongju", "sunchang", "taean", "wando", "wanju",
    "yanggu", "yeongyang"
]

# CLIK 포털 의회 코드 매핑 (council_code -> CLIK assemblyId)
CLIK_MAPPING = {
    "bonghwa": "3724051",      # 봉화군의회
    "boseong": "4678051",      # 보성군의회
    "buan": "4568051",         # 부안군의회
    "buk_gwangju": "2902051",  # 광주 북구의회
    "cheongsong": "3723051",   # 청송군의회
    "chilgok": "3709051",      # 칠곡군의회
    "damyang": "4671051",      # 담양군의회
    "gangjin": "4681051",      # 강진군의회
    "goheung": "4677051",      # 고흥군의회
    "gokseong": "4672051",     # 곡성군의회
    "gurye": "4673051",        # 구례군의회
    "hadong": "4883051",       # 하동군의회
    "hapcheon": "4889051",     # 합천군의회
    "hoengseong": "3272051",   # 횡성군의회
    "imsil": "4563051",        # 임실군의회
    "jung_busan": "2106051",   # 부산 중구의회
    "jung_daegu": "2201051",   # 대구 중구의회
    "muan": "4686051",         # 무안군의회
    "nam_gwangju": "2904051",  # 광주 남구의회
    "seongju": "3720051",      # 성주군의회
    "sunchang": "4564051",     # 순창군의회
    "taean": "4482051",        # 태안군의회
    "wando": "4680051",        # 완도군의회
    "wanju": "4550051",        # 완주군의회
    "yanggu": "3282051",       # 양구군의회
    "yeongyang": "3722051",    # 영양군의회
}

OUTPUT_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes")

async def fetch_clik_minutes(session, council_code: str, assembly_id: str) -> list:
    """CLIK 포털에서 회의록 목록 가져오기"""
    records = []

    # CLIK 회의록 검색 API
    base_url = "https://clik.nanet.go.kr/search/minute.do"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    }

    try:
        # 페이지별로 크롤링 (최대 5페이지)
        for page in range(1, 6):
            params = {
                "assemblyId": assembly_id,
                "pageIndex": str(page),
                "pageSize": "20"
            }

            async with session.get(base_url, params=params, headers=headers, timeout=30) as resp:
                if resp.status != 200:
                    print(f"  [{council_code}] 페이지 {page} 실패: {resp.status}")
                    break

                html = await resp.text()
                soup = BeautifulSoup(html, 'html.parser')

                # 회의록 목록 파싱
                rows = soup.select('table.board_list tbody tr')
                if not rows:
                    # 다른 선택자 시도
                    rows = soup.select('div.list_type01 ul li')

                if not rows:
                    rows = soup.select('table tbody tr')

                page_records = 0
                for row in rows:
                    try:
                        # 제목 추출
                        title_elem = row.select_one('a') or row.select_one('td:nth-child(2)')
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        if not title or len(title) < 3:
                            continue

                        # 메뉴 링크가 아닌 실제 회의록인지 확인
                        skip_keywords = ["회의록검색", "전자회의록", "영상회의록", "본회의/위원회",
                                        "조례제정", "행정감사", "게시판", "제안 통"]
                        if any(kw in title for kw in skip_keywords):
                            continue

                        # 링크 추출
                        link = title_elem.get('href', '')
                        if link and not link.startswith('http'):
                            link = f"https://clik.nanet.go.kr{link}"

                        # 날짜 추출
                        date_elem = row.select_one('td:nth-child(3)') or row.select_one('.date')
                        date_str = date_elem.get_text(strip=True) if date_elem else ""

                        record = {
                            "council_code": council_code,
                            "title": title,
                            "detail_url": link or f"https://clik.nanet.go.kr/search/minute.do?assemblyId={assembly_id}",
                            "meeting_id": "",
                            "cells": [title],
                            "crawled_at": datetime.now().isoformat(),
                            "date": date_str,
                            "source": "CLIK"
                        }
                        records.append(record)
                        page_records += 1

                    except Exception as e:
                        continue

                print(f"  [{council_code}] 페이지 {page}: {page_records}건")

                if page_records == 0:
                    break

    except Exception as e:
        print(f"  [{council_code}] CLIK 크롤링 오류: {e}")

    return records

async def try_direct_council_site(session, council_code: str) -> list:
    """의회 사이트 직접 접근 시도"""
    records = []

    # 의회별 URL 패턴
    url_patterns = {
        "bonghwa": "https://council.bonghwa.go.kr",
        "boseong": "https://council.boseong.go.kr",
        "buan": "https://council.buan.go.kr",
        "buk_gwangju": "https://council.bukgu.gwangju.kr",
        "cheongsong": "https://council.cs.go.kr",
        "chilgok": "https://council.chilgok.go.kr",
        "damyang": "https://council.damyang.go.kr",
        "gangjin": "https://council.gangjin.go.kr",
        "goheung": "https://council.goheung.go.kr",
        "gokseong": "https://council.gokseong.go.kr",
        "gurye": "https://council.gurye.go.kr",
        "hadong": "https://council.hadong.go.kr",
        "hapcheon": "https://council.hapcheon.go.kr",
        "hoengseong": "https://council.hsg.go.kr",
        "imsil": "https://council.imsil.go.kr",
        "jung_busan": "https://council.junggu.busan.kr",
        "jung_daegu": "https://council.jung.daegu.kr",
        "muan": "https://council.muan.go.kr",
        "nam_gwangju": "https://council.namgu.gwangju.kr",
        "seongju": "https://www.sjcouncil.go.kr",
        "sunchang": "https://www.sunchangcouncil.go.kr",
        "taean": "https://council.taean.go.kr",
        "wando": "https://council.wando.go.kr",
        "wanju": "https://council.wanju.go.kr",
        "yanggu": "https://www.ygcl.go.kr",
        "yeongyang": "https://council.yyg.go.kr",
    }

    base_url = url_patterns.get(council_code)
    if not base_url:
        return records

    # 회의록 페이지 경로들
    minute_paths = [
        "/board/minutes/list",
        "/contents/minutes",
        "/meeting/minute/list",
        "/portal/minutes",
        "/minutes/list",
        "/ebook/minute",
        "/minutes",
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    for path in minute_paths:
        try:
            url = f"{base_url}{path}"
            async with session.get(url, headers=headers, timeout=15, ssl=False) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # 테이블에서 회의록 추출
                    rows = soup.select('table tbody tr')
                    for row in rows:
                        cols = row.select('td')
                        if len(cols) >= 2:
                            title_elem = row.select_one('a')
                            if title_elem:
                                title = title_elem.get_text(strip=True)
                                if title and len(title) > 5:
                                    link = title_elem.get('href', '')
                                    if link and not link.startswith('http'):
                                        link = f"{base_url}{link}"

                                    record = {
                                        "council_code": council_code,
                                        "title": title,
                                        "detail_url": link or url,
                                        "meeting_id": "",
                                        "cells": [title],
                                        "crawled_at": datetime.now().isoformat(),
                                        "date": "",
                                        "source": "direct"
                                    }
                                    records.append(record)

                    if records:
                        print(f"  [{council_code}] 직접 접근 성공: {len(records)}건")
                        return records

        except Exception:
            continue

    return records

async def crawl_council(session, council_code: str) -> int:
    """단일 의회 크롤링"""
    print(f"\n크롤링 시작: {council_code}")

    records = []

    # 1. CLIK 포털에서 시도
    assembly_id = CLIK_MAPPING.get(council_code)
    if assembly_id:
        records = await fetch_clik_minutes(session, council_code, assembly_id)

    # 2. CLIK에서 못 찾으면 직접 접근 시도
    if len(records) < 3:
        direct_records = await try_direct_council_site(session, council_code)
        if len(direct_records) > len(records):
            records = direct_records

    # 3. 결과 저장
    if records:
        output_file = OUTPUT_DIR / f"{council_code}.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        print(f"  [{council_code}] 저장 완료: {len(records)}건")
    else:
        print(f"  [{council_code}] 데이터 없음")

    return len(records)

async def main():
    print("=" * 60)
    print("27개 문제 의회 재크롤링 시작")
    print("=" * 60)

    connector = aiohttp.TCPConnector(limit=5, ssl=False)
    timeout = aiohttp.ClientTimeout(total=60)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        results = {}

        for council_code in PROBLEM_COUNCILS:
            count = await crawl_council(session, council_code)
            results[council_code] = count
            await asyncio.sleep(1)  # 서버 부하 방지

    # 결과 요약
    print("\n" + "=" * 60)
    print("크롤링 결과 요약")
    print("=" * 60)

    success = [k for k, v in results.items() if v >= 5]
    partial = [k for k, v in results.items() if 0 < v < 5]
    failed = [k for k, v in results.items() if v == 0]

    print(f"\n성공 (5건 이상): {len(success)}개")
    for c in success:
        print(f"  - {c}: {results[c]}건")

    print(f"\n부분 성공 (1-4건): {len(partial)}개")
    for c in partial:
        print(f"  - {c}: {results[c]}건")

    print(f"\n실패 (0건): {len(failed)}개")
    for c in failed:
        print(f"  - {c}")

    total = sum(results.values())
    print(f"\n총 추출 건수: {total}건")

if __name__ == "__main__":
    asyncio.run(main())
