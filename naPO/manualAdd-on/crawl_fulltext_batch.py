#!/usr/bin/env python3
"""
88개 의회 회의록 전문 크롤링
- CLIK 포털 또는 각 의회 사이트에서 실제 회의록 전문 추출
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
from pathlib import Path
import re

# full_content 없는 의회 목록
NO_CONTENT_COUNCILS = [
    'asan', 'bonghwa', 'boryeong', 'boseong', 'buan', 'buk_busan', 'buk_gwangju',
    'buk_ulsan', 'busanjin', 'cheongdo', 'cheongsong', 'cheorwon', 'chilgok',
    'damyang', 'dobong', 'dong_busan', 'dong_gwangju', 'dongnae', 'gangjin',
    'gangneung', 'gangseo', 'gangseo_busan', 'geumjeong', 'gimje', 'gochang',
    'goheung', 'gokseong', 'gongju', 'goseong_gw', 'gunsan', 'guri', 'guro',
    'gurye', 'gwangsan', 'gyeongsan', 'hadong', 'hampyeong', 'hanam', 'hapcheon',
    'hoengseong', 'hongcheon', 'hwacheon', 'imsil', 'jangheung', 'jangseong',
    'jeju', 'jeongeup', 'jeonju', 'jindo', 'jung_busan', 'jung_daegu',
    'jung_incheon', 'miryang', 'muan', 'muju', 'nam_gwangju', 'namdong',
    'namwon', 'namyangju', 'nonsan', 'pocheon', 'pyeongtaek', 'seo_busan',
    'seocho', 'seongdong', 'seongju', 'seongnam', 'seosan', 'siheung', 'sinan',
    'sunchang', 'taean', 'taebaek', 'uijeongbu', 'uiryeong', 'ulleung', 'wando',
    'wanju', 'yanggu', 'yangju', 'yeoju', 'yeongcheon', 'yeongdo', 'yeonggwang',
    'yeongwol', 'yeongyang', 'yeonje', 'yesan'
]

# 의회별 CLIK 코드 매핑
CLIK_CODES = {
    'asan': '4420000', 'bonghwa': '4772000', 'boryeong': '4418000',
    'boseong': '4678000', 'buan': '4568000', 'buk_busan': '2617000',
    'buk_gwangju': '2902000', 'buk_ulsan': '3114000', 'busanjin': '2623000',
    'cheongdo': '4737000', 'cheongsong': '4772500', 'cheorwon': '3238000',
    'chilgok': '4785000', 'damyang': '4671000', 'dobong': '1132000',
    'dong_busan': '2614000', 'dong_gwangju': '2905000', 'dongnae': '2626000',
    'gangjin': '4681000', 'gangneung': '3215000', 'gangseo': '1150000',
    'gangseo_busan': '2644000', 'geumjeong': '2641000', 'gimje': '4554000',
    'gochang': '4567000', 'goheung': '4677000', 'gokseong': '4672000',
    'gongju': '4415000', 'goseong_gw': '3282500', 'gunsan': '4513000',
    'guri': '4131000', 'guro': '1153000', 'gurye': '4673000',
    'gwangsan': '2920000', 'gyeongsan': '4729000', 'hadong': '4883000',
    'hampyeong': '4687000', 'hanam': '4179000', 'hapcheon': '4889000',
    'hoengseong': '3272000', 'hongcheon': '3271000', 'hwacheon': '3281000',
    'imsil': '4563000', 'jangheung': '4680000', 'jangseong': '4686000',
    'jeju': '5011000', 'jeongeup': '4556000', 'jeonju': '4511000',
    'jindo': '4689000', 'jung_busan': '2611000', 'jung_daegu': '2711000',
    'jung_incheon': '2814000', 'miryang': '4827000', 'muan': '4684000',
    'muju': '4562000', 'nam_gwangju': '2904000', 'namdong': '2820000',
    'namwon': '4519000', 'namyangju': '4136000', 'nonsan': '4423000',
    'pocheon': '4165000', 'pyeongtaek': '4122000', 'seo_busan': '2653000',
    'seocho': '1165000', 'seongdong': '1120000', 'seongju': '4780000',
    'seongnam': '4113000', 'seosan': '4421000', 'siheung': '4139000',
    'sinan': '4688000', 'sunchang': '4564000', 'taean': '4425000',
    'taebaek': '3219000', 'uijeongbu': '4115000', 'uiryeong': '4872000',
    'ulleung': '4790000', 'wando': '4680500', 'wanju': '4550000',
    'yanggu': '3282000', 'yangju': '4163000', 'yeoju': '4180000',
    'yeongcheon': '4723000', 'yeongdo': '2620000', 'yeonggwang': '4683000',
    'yeongwol': '3275000', 'yeongyang': '4776000', 'yeonje': '2647000',
    'yesan': '4424000'
}

OUTPUT_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes")

async def get_minute_content(page, url: str) -> str:
    """회의록 상세 페이지에서 전문 추출"""
    try:
        await page.goto(url, timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # 다양한 선택자로 본문 추출 시도
        selectors = [
            'div.content_view',
            'div.view_content',
            'div.board_view',
            'div.minutes_content',
            'div.detail_content',
            'article',
            'div.con_box',
            'div#content',
            'table.view_table',
            'pre',
        ]

        for selector in selectors:
            elem = await page.query_selector(selector)
            if elem:
                text = await elem.inner_text()
                if text and len(text) > 200:
                    return text.strip()

        # 전체 body에서 추출
        body = await page.query_selector('body')
        if body:
            text = await body.inner_text()
            # 메뉴 등 제거
            lines = text.split('\n')
            content_lines = []
            for line in lines:
                line = line.strip()
                if len(line) > 20:  # 짧은 메뉴 텍스트 제외
                    content_lines.append(line)
            if len(content_lines) > 10:
                return '\n'.join(content_lines[:500])  # 최대 500줄

    except Exception as e:
        pass

    return ""

async def crawl_clik_minutes(page, council_code: str, clik_code: str) -> list:
    """CLIK에서 회의록 목록 및 내용 크롤링"""
    records = []

    try:
        # CLIK 회의록 검색 페이지
        url = f"https://clik.nanet.go.kr/search/searchMinutes.do?lclasCode={clik_code}"
        await page.goto(url, timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # 회의록 목록 추출
        rows = await page.query_selector_all('table tbody tr')
        if not rows:
            rows = await page.query_selector_all('div.list_type ul li')

        count = 0
        for row in rows[:50]:  # 최대 50건
            try:
                link = await row.query_selector('a')
                if not link:
                    continue

                title = await link.inner_text()
                title = title.strip()

                if not title or len(title) < 5:
                    continue

                href = await link.get_attribute('href')
                if href:
                    if not href.startswith('http'):
                        href = f"https://clik.nanet.go.kr{href}"

                    # 상세 페이지에서 전문 추출
                    full_content = await get_minute_content(page, href)

                    record = {
                        "council_code": council_code,
                        "title": title,
                        "detail_url": href,
                        "meeting_id": "",
                        "cells": [title],
                        "crawled_at": datetime.now().isoformat(),
                        "date": "",
                        "full_content": full_content if full_content else "",
                        "source": "clik_fulltext"
                    }
                    records.append(record)
                    count += 1

                    if count >= 50:
                        break

            except Exception:
                continue

    except Exception as e:
        print(f"  CLIK 오류: {e}")

    return records

async def crawl_council_site(page, council_code: str) -> list:
    """각 의회 사이트에서 직접 크롤링"""
    records = []

    # 의회별 URL 패턴
    url_patterns = {
        'asan': 'https://council.asan.go.kr',
        'bonghwa': 'https://www.bonghwa.go.kr/council',
        'jeju': 'https://record.council.jeju.kr',
        'jeonju': 'https://council.jeonju.go.kr',
        'seongnam': 'https://council.seongnam.go.kr',
        # 추가 의회들...
    }

    base_url = url_patterns.get(council_code)
    if not base_url:
        return records

    minute_paths = [
        '/minutes/list',
        '/meeting/minute',
        '/board/minute',
        '/contents/minute',
    ]

    for path in minute_paths:
        try:
            url = f"{base_url}{path}"
            await page.goto(url, timeout=20000, wait_until="domcontentloaded")
            await asyncio.sleep(2)

            links = await page.query_selector_all('table tbody tr a, div.list a')
            count = 0

            for link in links[:50]:
                try:
                    title = await link.inner_text()
                    title = title.strip()

                    if not title or len(title) < 5:
                        continue

                    href = await link.get_attribute('href')
                    if href:
                        if not href.startswith('http'):
                            href = f"{base_url}{href}" if href.startswith('/') else url

                        # 전문 추출
                        full_content = await get_minute_content(page, href)

                        record = {
                            "council_code": council_code,
                            "title": title,
                            "detail_url": href,
                            "meeting_id": "",
                            "cells": [title],
                            "crawled_at": datetime.now().isoformat(),
                            "date": "",
                            "full_content": full_content if full_content else "",
                            "source": "direct_fulltext"
                        }
                        records.append(record)
                        count += 1

                        if count >= 50:
                            break

                except Exception:
                    continue

            if records:
                break

        except Exception:
            continue

    return records

async def crawl_council(browser, council_code: str) -> int:
    """단일 의회 크롤링"""
    print(f"\n크롤링: {council_code}")

    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        ignore_https_errors=True
    )
    page = await context.new_page()

    records = []

    # 1. CLIK에서 시도
    clik_code = CLIK_CODES.get(council_code)
    if clik_code:
        records = await crawl_clik_minutes(page, council_code, clik_code)

    # 2. CLIK에서 못 찾으면 직접 접근
    if len(records) < 10:
        direct_records = await crawl_council_site(page, council_code)
        if len(direct_records) > len(records):
            records = direct_records

    await context.close()

    # 저장
    if records:
        # full_content 있는 것만 필터링
        valid_records = [r for r in records if r.get('full_content') and len(r['full_content']) > 100]

        if valid_records:
            output_file = OUTPUT_DIR / f"{council_code}.jsonl"
            with open(output_file, 'w', encoding='utf-8') as f:
                for record in valid_records:
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')
            print(f"  ✅ 저장: {len(valid_records)}건 (전문 포함)")
            return len(valid_records)
        else:
            print(f"  ⚠️  전문 없음")
            return 0
    else:
        print(f"  ❌ 데이터 없음")
        return 0

async def main():
    print("=" * 60)
    print("88개 의회 회의록 전문 크롤링")
    print("=" * 60)

    # 처음 10개만 테스트
    test_councils = NO_CONTENT_COUNCILS[:10]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        results = {}
        for council_code in test_councils:
            try:
                count = await crawl_council(browser, council_code)
                results[council_code] = count
            except Exception as e:
                print(f"  {council_code} 실패: {e}")
                results[council_code] = 0

            await asyncio.sleep(2)

        await browser.close()

    # 결과 요약
    print("\n" + "=" * 60)
    print("크롤링 결과")
    print("=" * 60)

    success = [k for k, v in results.items() if v >= 10]
    partial = [k for k, v in results.items() if 0 < v < 10]
    failed = [k for k, v in results.items() if v == 0]

    print(f"\n✅ 성공: {len(success)}개")
    print(f"⚠️  부분: {len(partial)}개")
    print(f"❌ 실패: {len(failed)}개")

if __name__ == "__main__":
    asyncio.run(main())
