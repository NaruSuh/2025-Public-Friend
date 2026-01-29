#!/usr/bin/env python3
"""
CLIK 포털 검색으로 회의록 전문 크롤링
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
from pathlib import Path
import re
import sys

# 전문 없는 63개 의회
REMAINING = [
    'bonghwa', 'buk_busan', 'buk_gwangju', 'buk_ulsan', 'bupyeong',
    'cheongdo', 'cheongsong', 'dobong', 'dong_busan', 'dongnae',
    'eunpyeong', 'gangneung', 'gangseo', 'gangseo_busan', 'geumjeong',
    'gijang', 'gimje', 'gokseong', 'gongju', 'goseong_gw', 'guri',
    'guro', 'gwangsan', 'gyeongsan', 'hadong', 'hampyeong', 'hapcheon',
    'hongcheon', 'hwacheon', 'imsil', 'jangheung', 'jangseong',
    'jeongeup', 'jindo', 'jung_busan', 'jung_daegu', 'jung_incheon',
    'miryang', 'muan', 'muju', 'namdong', 'namwon', 'namyangju',
    'nonsan', 'pocheon', 'pyeongtaek', 'seo_busan', 'seocho',
    'seongdong', 'seongju', 'seongnam', 'siheung', 'sinan', 'sunchang',
    'suyeong', 'taebaek', 'uiryeong', 'ulleung', 'wando', 'yeoju',
    'yeongdo', 'yeonje', 'yesan'
]

# 의회 한글명 매핑
COUNCIL_NAMES = {
    'bonghwa': '봉화군', 'buk_busan': '부산북구', 'buk_gwangju': '광주북구',
    'buk_ulsan': '울산북구', 'bupyeong': '부평구', 'cheongdo': '청도군',
    'cheongsong': '청송군', 'dobong': '도봉구', 'dong_busan': '부산동구',
    'dongnae': '동래구', 'eunpyeong': '은평구', 'gangneung': '강릉시',
    'gangseo': '서울강서구', 'gangseo_busan': '부산강서구', 'geumjeong': '금정구',
    'gijang': '기장군', 'gimje': '김제시', 'gokseong': '곡성군',
    'gongju': '공주시', 'goseong_gw': '강원고성군', 'guri': '구리시',
    'guro': '구로구', 'gwangsan': '광산구', 'gyeongsan': '경산시',
    'hadong': '하동군', 'hampyeong': '함평군', 'hapcheon': '합천군',
    'hongcheon': '홍천군', 'hwacheon': '화천군', 'imsil': '임실군',
    'jangheung': '장흥군', 'jangseong': '장성군', 'jeongeup': '정읍시',
    'jindo': '진도군', 'jung_busan': '부산중구', 'jung_daegu': '대구중구',
    'jung_incheon': '인천중구', 'miryang': '밀양시', 'muan': '무안군',
    'muju': '무주군', 'namdong': '남동구', 'namwon': '남원시',
    'namyangju': '남양주시', 'nonsan': '논산시', 'pocheon': '포천시',
    'pyeongtaek': '평택시', 'seo_busan': '부산서구', 'seocho': '서초구',
    'seongdong': '성동구', 'seongju': '성주군', 'seongnam': '성남시',
    'siheung': '시흥시', 'sinan': '신안군', 'sunchang': '순창군',
    'suyeong': '수영구', 'taebaek': '태백시', 'uiryeong': '의령군',
    'ulleung': '울릉군', 'wando': '완도군', 'yeoju': '여주시',
    'yeongdo': '영도구', 'yeonje': '연제구', 'yesan': '예산군'
}

OUTPUT_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes")

async def search_clik(page, council_name: str) -> list:
    """CLIK에서 의회 회의록 검색"""
    results = []

    try:
        # CLIK 회의록 통합검색
        search_url = f"https://clik.nanet.go.kr/search/searchList.do?collection=min&query={council_name}의회"
        await page.goto(search_url, timeout=20000, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # 검색 결과에서 링크 추출
        links = await page.query_selector_all('div.list_wrap a, ul.search_list a, table.list a')

        for link in links[:30]:
            try:
                text = await link.inner_text()
                text = text.strip()

                if not text or len(text) < 5:
                    continue

                href = await link.get_attribute('href')
                if href:
                    if not href.startswith('http'):
                        href = f"https://clik.nanet.go.kr{href}"
                    results.append({'title': text, 'url': href})
            except:
                continue

    except Exception as e:
        pass

    return results

async def get_content_from_clik(page, url: str) -> str:
    """CLIK 상세 페이지에서 전문 추출"""
    try:
        await page.goto(url, timeout=15000, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # 회의록 뷰어 또는 본문 영역
        selectors = [
            'div.view_content', 'div.minutes_content', 'pre',
            'div#contentArea', 'iframe', 'div.content'
        ]

        for sel in selectors:
            elem = await page.query_selector(sel)
            if elem:
                if sel == 'iframe':
                    frame = await elem.content_frame()
                    if frame:
                        body = await frame.query_selector('body')
                        if body:
                            text = await body.inner_text()
                            if text and len(text) > 500:
                                return text.strip()
                else:
                    text = await elem.inner_text()
                    if text and len(text) > 500:
                        return text.strip()

        # body 전체
        body = await page.query_selector('body')
        if body:
            text = await body.inner_text()
            lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 30]
            if len(lines) > 20:
                return '\n'.join(lines[:200])

    except:
        pass

    return ""

async def crawl_council(browser, council_code: str) -> int:
    """의회 크롤링"""
    council_name = COUNCIL_NAMES.get(council_code, council_code)

    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        ignore_https_errors=True
    )
    page = await context.new_page()

    records = []

    # CLIK 검색
    search_results = await search_clik(page, council_name)

    for item in search_results[:50]:
        try:
            content = await get_content_from_clik(page, item['url'])

            if content and len(content) > 500:
                record = {
                    "council_code": council_code,
                    "title": item['title'],
                    "detail_url": item['url'],
                    "meeting_id": "",
                    "cells": [item['title']],
                    "crawled_at": datetime.now().isoformat(),
                    "date": "",
                    "full_content": content,
                    "source": "clik_search"
                }
                records.append(record)

        except:
            continue

    await context.close()

    if records:
        output_file = OUTPUT_DIR / f"{council_code}.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        return len(records)

    return 0

async def main():
    print("=" * 60)
    print("CLIK 검색으로 회의록 전문 크롤링")
    print("=" * 60 + "\n")

    start_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end_idx = int(sys.argv[2]) if len(sys.argv) > 2 else len(REMAINING)

    councils = REMAINING[start_idx:end_idx]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        results = {}
        for i, code in enumerate(councils):
            name = COUNCIL_NAMES.get(code, code)
            print(f"[{i+1}/{len(councils)}] {code} ({name})", end=" ", flush=True)
            try:
                count = await crawl_council(browser, code)
                results[code] = count
                print(f"✅ {count}건" if count > 0 else "❌")
            except Exception as e:
                print(f"오류")
                results[code] = 0

            await asyncio.sleep(1)

        await browser.close()

    success = sum(1 for v in results.values() if v > 0)
    total = sum(results.values())
    print(f"\n성공: {success}/{len(councils)} | 총 {total}건")

if __name__ == "__main__":
    asyncio.run(main())
