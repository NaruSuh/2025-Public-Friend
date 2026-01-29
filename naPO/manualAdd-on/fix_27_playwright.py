#!/usr/bin/env python3
"""
27개 문제 의회 Playwright 재크롤링 스크립트
- 각 의회 사이트에 직접 접근하여 실제 회의록 추출
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
from pathlib import Path
import re

# 27개 문제 의회 및 회의록 URL
COUNCIL_URLS = {
    "bonghwa": [
        "http://council.bonghwa.go.kr/kr/meeting/meeting_list01.do",
        "https://council.bonghwa.go.kr/kr/meeting/meeting_list.do",
    ],
    "boseong": [
        "https://council.boseong.go.kr/board/minutes/list",
        "https://council.boseong.go.kr/contents/minutes",
    ],
    "buan": [
        "https://council.buan.go.kr/record/list.do",
        "https://council.buan.go.kr/contents/minute",
    ],
    "buk_gwangju": [
        "https://council.bukgu.gwangju.kr/meeting/minute.do",
        "https://council.bukgu.gwangju.kr/kr/sub03/sub01.do",
    ],
    "cheongsong": [
        "https://council.cs.go.kr/kr/minutes/minutesList.do",
        "http://council.cs.go.kr/board/minute/list",
    ],
    "chilgok": [
        "https://council.chilgok.go.kr/kr/board/minute.do",
        "https://council.chilgok.go.kr/contents/minutes",
    ],
    "damyang": [
        "https://council.damyang.go.kr/kr/meeting/list.do",
        "https://council.damyang.go.kr/board/minute",
    ],
    "gangjin": [
        "https://council.gangjin.go.kr/kr/board/minute.do",
        "https://council.gangjin.go.kr/meeting/list",
    ],
    "goheung": [
        "https://council.goheung.go.kr/kr/board/minute.do",
        "https://council.goheung.go.kr/meeting/minute/list",
    ],
    "gokseong": [
        "https://council.gokseong.go.kr/kr/meeting/minute.do",
        "https://council.gokseong.go.kr/board/minute/list",
    ],
    "gurye": [
        "https://council.gurye.go.kr/kr/board/minute.do",
        "https://council.gurye.go.kr/meeting/minute",
    ],
    "hadong": [
        "https://council.hadong.go.kr/kr/meeting/minute.do",
        "https://council.hadong.go.kr/board/minute/list",
    ],
    "hapcheon": [
        "https://council.hc.go.kr/kr/board/minute.do",
        "https://council.hapcheon.go.kr/meeting/list",
    ],
    "hoengseong": [
        "https://council.hsg.go.kr/kr/board/minute.do",
        "http://www.hscouncil.go.kr/board/minute",
    ],
    "imsil": [
        "https://council.imsil.go.kr/kr/board/minute.do",
        "https://council.imsil.go.kr/meeting/minute/list",
    ],
    "jung_busan": [
        "https://council.bsjunggu.go.kr/kr/sub03/sub01.do",
        "https://council.bsjunggu.go.kr/board/minute",
    ],
    "jung_daegu": [
        "https://council.jung.daegu.kr/kr/board/minute.do",
        "https://council.jung.daegu.kr/meeting/list",
    ],
    "muan": [
        "https://council.muan.go.kr/kr/board/minute.do",
        "https://council.muan.go.kr/meeting/minute",
    ],
    "nam_gwangju": [
        "https://council.namgu.gwangju.kr/kr/sub03/sub01.do",
        "https://council.namgu.gwangju.kr/board/minute/list",
    ],
    "seongju": [
        "https://www.sjcouncil.go.kr/content/minutes/mntsList.html",
        "https://www.sjcouncil.go.kr/portal/F30000/boardList",
    ],
    "sunchang": [
        "https://www.sunchangcouncil.go.kr/main/portal/minute",
        "https://www.sunchangcouncil.go.kr/board/minute/list",
    ],
    "taean": [
        "https://council.taean.go.kr/kr/board/minute.do",
        "https://council.taean.go.kr/meeting/minute/list",
    ],
    "wando": [
        "http://www.wdcc.or.kr:8088/minute/list.do",
        "http://www.wdcc.or.kr/board/minute",
    ],
    "wanju": [
        "https://council.wanju.go.kr/board?depth_1=46",
        "https://council.wanju.go.kr/meeting/minute",
    ],
    "yanggu": [
        "http://www.ygcl.go.kr/portal/F30000/F30100/boardList",
        "http://www.ygcl.go.kr/board/minute/list",
    ],
    "yeongyang": [
        "https://council.yyg.go.kr/kr/board/minute.do",
        "https://council.yyg.go.kr/meeting/list",
    ],
}

OUTPUT_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes")

async def extract_minutes_from_page(page, council_code: str, url: str) -> list:
    """페이지에서 회의록 목록 추출"""
    records = []

    try:
        # 테이블 기반 추출 시도
        rows = await page.query_selector_all('table tbody tr')
        if not rows:
            rows = await page.query_selector_all('div.board_list li')
        if not rows:
            rows = await page.query_selector_all('ul.list li')

        for row in rows:
            try:
                # 링크와 제목 추출
                link_elem = await row.query_selector('a')
                if not link_elem:
                    continue

                title = await link_elem.inner_text()
                title = title.strip()

                # 메뉴 링크 필터링
                skip_keywords = ["회의록검색", "전자회의록", "영상회의록", "본회의/위원회",
                                "조례제정", "행정감사", "게시판", "로그인", "회원가입",
                                "HOME", "검색", "바로가기"]
                if any(kw in title for kw in skip_keywords):
                    continue

                if len(title) < 5:
                    continue

                href = await link_elem.get_attribute('href')
                if href and not href.startswith('http'):
                    if href.startswith('/'):
                        base = '/'.join(url.split('/')[:3])
                        href = base + href
                    else:
                        href = url.rsplit('/', 1)[0] + '/' + href

                # 날짜 추출 시도
                date_str = ""
                date_elem = await row.query_selector('td:nth-child(3)')
                if date_elem:
                    date_str = await date_elem.inner_text()
                    date_str = date_str.strip()

                record = {
                    "council_code": council_code,
                    "title": title,
                    "detail_url": href or url,
                    "meeting_id": "",
                    "cells": [title],
                    "crawled_at": datetime.now().isoformat(),
                    "date": date_str,
                    "source": "playwright_direct"
                }
                records.append(record)

            except Exception:
                continue

        # 제목으로 보이는 요소들 추출 (백업)
        if len(records) < 3:
            all_links = await page.query_selector_all('a')
            for link in all_links:
                try:
                    text = await link.inner_text()
                    text = text.strip()

                    # 회의록 제목 패턴 매칭
                    patterns = [
                        r'제\d+회.*?(본회의|위원회|정례회|임시회)',
                        r'\d{4}년.*?(본회의|위원회)',
                        r'(본회의|위원회).*?회의록',
                    ]

                    is_minutes = False
                    for pattern in patterns:
                        if re.search(pattern, text):
                            is_minutes = True
                            break

                    if is_minutes and len(text) > 5:
                        href = await link.get_attribute('href')
                        if href and not href.startswith('http'):
                            if href.startswith('/'):
                                base = '/'.join(url.split('/')[:3])
                                href = base + href

                        # 중복 체크
                        if not any(r['title'] == text for r in records):
                            record = {
                                "council_code": council_code,
                                "title": text,
                                "detail_url": href or url,
                                "meeting_id": "",
                                "cells": [text],
                                "crawled_at": datetime.now().isoformat(),
                                "date": "",
                                "source": "playwright_pattern"
                            }
                            records.append(record)

                except Exception:
                    continue

    except Exception as e:
        print(f"    추출 오류: {e}")

    return records

async def crawl_council(browser, council_code: str, urls: list) -> int:
    """단일 의회 크롤링"""
    print(f"\n크롤링: {council_code}")

    all_records = []
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ignore_https_errors=True
    )
    page = await context.new_page()

    for url in urls:
        try:
            print(f"  시도: {url}")
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(2)

            records = await extract_minutes_from_page(page, council_code, url)
            if records:
                print(f"    추출: {len(records)}건")
                all_records.extend(records)

            if len(all_records) >= 5:
                break

        except Exception as e:
            print(f"    실패: {str(e)[:50]}")
            continue

    await context.close()

    # 중복 제거
    unique_records = []
    seen_titles = set()
    for r in all_records:
        if r['title'] not in seen_titles:
            seen_titles.add(r['title'])
            unique_records.append(r)

    # 저장
    if unique_records:
        output_file = OUTPUT_DIR / f"{council_code}.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for record in unique_records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        print(f"  저장: {len(unique_records)}건")
    else:
        print(f"  데이터 없음")

    return len(unique_records)

async def main():
    print("=" * 60)
    print("27개 문제 의회 Playwright 재크롤링")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        results = {}
        for council_code, urls in COUNCIL_URLS.items():
            try:
                count = await crawl_council(browser, council_code, urls)
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

    success = {k: v for k, v in results.items() if v >= 5}
    partial = {k: v for k, v in results.items() if 0 < v < 5}
    failed = {k: v for k, v in results.items() if v == 0}

    print(f"\n✅ 성공 ({len(success)}개): {list(success.keys())}")
    print(f"⚠️  부분 ({len(partial)}개): {list(partial.keys())}")
    print(f"❌ 실패 ({len(failed)}개): {list(failed.keys())}")
    print(f"\n총 추출: {sum(results.values())}건")

if __name__ == "__main__":
    asyncio.run(main())
