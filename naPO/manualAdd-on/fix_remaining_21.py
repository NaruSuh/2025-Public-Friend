#!/usr/bin/env python3
"""
21개 남은 문제 의회 Playwright 크롤링
- 웹 검색으로 확인한 정확한 URL 사용
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
from pathlib import Path
import re

# 21개 의회 및 정확한 URL
COUNCIL_URLS = {
    "bonghwa": {
        "urls": [
            "https://www.bonghwa.go.kr/open.content/council/proceedings/congressional.record/",
            "https://www.bonghwa.go.kr/open.content/council/proceedings/",
        ],
        "name": "봉화군의회"
    },
    "boseong": {
        "urls": [
            "https://www.bscouncil.go.kr/main/",
            "http://www.bscouncil.go.kr/korean/meeting/",
        ],
        "name": "보성군의회"
    },
    "buan": {
        "urls": [
            "https://buancouncil.go.kr/",
            "http://www.buancouncil.go.kr/korean/meeting/",
        ],
        "name": "부안군의회"
    },
    "buk_gwangju": {
        "urls": [
            "https://www.bukgu.gwangju.kr/council/",
            "https://council.bukgu.gwangju.kr/",
        ],
        "name": "광주북구의회"
    },
    "cheongsong": {
        "urls": [
            "https://www.cscouncil.go.kr/",
            "http://www.cscouncil.go.kr/korean/meeting/",
        ],
        "name": "청송군의회"
    },
    "chilgok": {
        "urls": [
            "https://council.chilgok.go.kr/",
            "https://council.chilgok.go.kr/korean/meeting/",
        ],
        "name": "칠곡군의회"
    },
    "damyang": {
        "urls": [
            "http://dycouncil.go.kr/",
            "http://dycouncil.go.kr/korean/meeting/",
        ],
        "name": "담양군의회"
    },
    "gangjin": {
        "urls": [
            "https://www.gjcouncil.go.kr/",
            "http://www.gjcouncil.go.kr/korean/meeting/",
        ],
        "name": "강진군의회"
    },
    "gokseong": {
        "urls": [
            "https://www.gscouncil.go.kr/",
            "http://www.gscouncil.go.kr/korean/meeting/",
        ],
        "name": "곡성군의회"
    },
    "gurye": {
        "urls": [
            "https://www.grcouncil.go.kr/",
            "http://www.grcouncil.go.kr/korean/meeting/",
        ],
        "name": "구례군의회"
    },
    "hadong": {
        "urls": [
            "https://www.hdcouncil.go.kr/",
            "http://www.hdcouncil.go.kr/korean/meeting/",
        ],
        "name": "하동군의회"
    },
    "hapcheon": {
        "urls": [
            "https://www.hccl.go.kr/",
            "https://www.hccl.go.kr/source/korean/meeting/minute.jsp",
        ],
        "name": "합천군의회"
    },
    "hoengseong": {
        "urls": [
            "https://hsg.go.kr/council/index.do",
            "https://hsg.go.kr/council/contents.do?key=1447",
        ],
        "name": "횡성군의회"
    },
    "jung_busan": {
        "urls": [
            "https://council.bsjunggu.go.kr/",
            "https://council.bsjunggu.go.kr/korean/meeting/",
        ],
        "name": "부산중구의회"
    },
    "jung_daegu": {
        "urls": [
            "https://council.jung.daegu.kr/",
            "http://council.jung.daegu.kr/korean/meeting/",
        ],
        "name": "대구중구의회"
    },
    "muan": {
        "urls": [
            "https://www.macouncil.go.kr/",
            "http://www.macouncil.go.kr/korean/meeting/",
        ],
        "name": "무안군의회"
    },
    "nam_gwangju": {
        "urls": [
            "https://council.namgu.gwangju.kr/",
            "https://www.namgu.gwangju.kr/council/",
        ],
        "name": "광주남구의회"
    },
    "seongju": {
        "urls": [
            "https://www.sjcouncil.go.kr/",
            "https://www.sjcouncil.go.kr/content/minutes/mntsList.html",
        ],
        "name": "성주군의회"
    },
    "taean": {
        "urls": [
            "https://council.taean.go.kr/main/",
            "https://council.taean.go.kr/main/index.php?m_cd=36",
        ],
        "name": "태안군의회"
    },
    "wanju": {
        "urls": [
            "https://council.wanju.go.kr/",
            "https://council.wanju.go.kr/board?depth_1=46&depth_2=68",
        ],
        "name": "완주군의회"
    },
    "yeongyang": {
        "urls": [
            "https://www.yycouncil.go.kr/",
            "http://www.yycouncil.go.kr/korean/meeting/",
        ],
        "name": "영양군의회"
    },
}

OUTPUT_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes")

async def extract_minutes(page, council_code: str, url: str, name: str) -> list:
    """페이지에서 회의록 추출"""
    records = []

    try:
        # 모든 링크 추출
        links = await page.query_selector_all('a')

        for link in links:
            try:
                text = await link.inner_text()
                text = text.strip()

                if not text or len(text) < 5:
                    continue

                # 메뉴/네비게이션 텍스트 필터링
                skip_patterns = [
                    "회의록검색", "전자회의록", "영상회의록", "HOME", "로그인",
                    "회원가입", "검색", "바로가기", "사이트맵", "전체메뉴",
                    "개인정보", "이용약관", "저작권", "찾아오시는", "연락처",
                    "본문바로가기", "주메뉴", "하위메뉴", "조례제정절차",
                    "게시판", "공지사항", "의회소식", "보도자료",
                    "의원소개", "의장인사말", "역대의장", "의원현황",
                    "조직", "연혁", "시설안내", "오시는길"
                ]

                if any(p in text for p in skip_patterns):
                    continue

                # 회의록 패턴 매칭
                minute_patterns = [
                    r'제\s*\d+\s*회',           # 제XXX회
                    r'\d{4}년',                   # 2024년
                    r'(본회의|위원회|정례회|임시회)',
                    r'\d+차\s*(본회의|위원회)',
                    r'회의록\s*제?\d+호',
                ]

                is_minute = False
                for pattern in minute_patterns:
                    if re.search(pattern, text):
                        is_minute = True
                        break

                if not is_minute:
                    continue

                href = await link.get_attribute('href')
                if href and not href.startswith('http'):
                    if href.startswith('/'):
                        base = '/'.join(url.split('/')[:3])
                        href = base + href
                    elif not href.startswith('javascript'):
                        href = url.rsplit('/', 1)[0] + '/' + href

                if href and 'javascript' in href.lower():
                    href = url

                # 중복 체크
                if any(r['title'] == text for r in records):
                    continue

                record = {
                    "council_code": council_code,
                    "title": text,
                    "detail_url": href or url,
                    "meeting_id": "",
                    "cells": [text],
                    "crawled_at": datetime.now().isoformat(),
                    "date": "",
                    "source": "playwright_v2"
                }
                records.append(record)

            except Exception:
                continue

        # 테이블 행에서도 추출 시도
        rows = await page.query_selector_all('table tbody tr, div.board_list li, ul.list_type li')
        for row in rows:
            try:
                link = await row.query_selector('a')
                if not link:
                    continue

                text = await link.inner_text()
                text = text.strip()

                if len(text) < 5 or any(r['title'] == text for r in records):
                    continue

                # 숫자 포함 체크 (회차 표시)
                if not re.search(r'\d', text):
                    continue

                href = await link.get_attribute('href')
                if href and not href.startswith('http'):
                    if href.startswith('/'):
                        base = '/'.join(url.split('/')[:3])
                        href = base + href

                if href and 'javascript' in href.lower():
                    href = url

                record = {
                    "council_code": council_code,
                    "title": text,
                    "detail_url": href or url,
                    "meeting_id": "",
                    "cells": [text],
                    "crawled_at": datetime.now().isoformat(),
                    "date": "",
                    "source": "playwright_v2_table"
                }
                records.append(record)

            except Exception:
                continue

    except Exception as e:
        print(f"    추출 오류: {e}")

    return records

async def crawl_council(browser, council_code: str, info: dict) -> int:
    """단일 의회 크롤링"""
    name = info["name"]
    urls = info["urls"]

    print(f"\n크롤링: {name} ({council_code})")

    all_records = []

    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ignore_https_errors=True
    )
    page = await context.new_page()

    for url in urls:
        try:
            print(f"  URL: {url[:50]}...")
            response = await page.goto(url, timeout=20000, wait_until="domcontentloaded")

            if response and response.status == 200:
                await asyncio.sleep(2)
                records = await extract_minutes(page, council_code, url, name)

                if records:
                    print(f"    추출: {len(records)}건")
                    all_records.extend(records)

                if len(all_records) >= 5:
                    break
            else:
                print(f"    응답: {response.status if response else 'None'}")

        except Exception as e:
            print(f"    오류: {str(e)[:40]}")
            continue

    await context.close()

    # 중복 제거
    unique = []
    seen = set()
    for r in all_records:
        if r['title'] not in seen:
            seen.add(r['title'])
            unique.append(r)

    # 저장
    if unique:
        output_file = OUTPUT_DIR / f"{council_code}.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for record in unique:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        print(f"  ✅ 저장: {len(unique)}건")
        return len(unique)
    else:
        print(f"  ❌ 데이터 없음")
        return 0

async def main():
    print("=" * 60)
    print("21개 남은 의회 재크롤링")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        results = {}
        for council_code, info in COUNCIL_URLS.items():
            try:
                count = await crawl_council(browser, council_code, info)
                results[council_code] = count
            except Exception as e:
                print(f"  {council_code} 전체 실패: {e}")
                results[council_code] = 0

            await asyncio.sleep(1)

        await browser.close()

    # 결과 요약
    print("\n" + "=" * 60)
    print("크롤링 결과")
    print("=" * 60)

    success = [k for k, v in results.items() if v >= 5]
    partial = [k for k, v in results.items() if 0 < v < 5]
    failed = [k for k, v in results.items() if v == 0]

    print(f"\n✅ 성공 ({len(success)}개):")
    for c in success:
        print(f"  - {c}: {results[c]}건")

    print(f"\n⚠️  부분 ({len(partial)}개):")
    for c in partial:
        print(f"  - {c}: {results[c]}건")

    print(f"\n❌ 실패 ({len(failed)}개): {failed}")
    print(f"\n총 추출: {sum(results.values())}건")

if __name__ == "__main__":
    asyncio.run(main())
