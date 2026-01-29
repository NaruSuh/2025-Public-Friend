#!/usr/bin/env python3
"""
CLIK(국회도서관 지방의회 의정정보) 회의록 전문 크롤링
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
from pathlib import Path
import re

# 88개 의회 목록
COUNCILS = [
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

# 의회 한글명 매핑
COUNCIL_NAMES = {
    'asan': '아산시', 'bonghwa': '봉화군', 'boryeong': '보령시', 'boseong': '보성군',
    'buan': '부안군', 'buk_busan': '부산북구', 'buk_gwangju': '광주북구',
    'buk_ulsan': '울산북구', 'busanjin': '부산진구', 'cheongdo': '청도군',
    'cheongsong': '청송군', 'cheorwon': '철원군', 'chilgok': '칠곡군',
    'damyang': '담양군', 'dobong': '도봉구', 'dong_busan': '부산동구',
    'dong_gwangju': '광주동구', 'dongnae': '동래구', 'gangjin': '강진군',
    'gangneung': '강릉시', 'gangseo': '강서구', 'gangseo_busan': '부산강서구',
    'geumjeong': '금정구', 'gimje': '김제시', 'gochang': '고창군',
    'goheung': '고흥군', 'gokseong': '곡성군', 'gongju': '공주시',
    'goseong_gw': '고성군', 'gunsan': '군산시', 'guri': '구리시',
    'guro': '구로구', 'gurye': '구례군', 'gwangsan': '광산구',
    'gyeongsan': '경산시', 'hadong': '하동군', 'hampyeong': '함평군',
    'hanam': '하남시', 'hapcheon': '합천군', 'hoengseong': '횡성군',
    'hongcheon': '홍천군', 'hwacheon': '화천군', 'imsil': '임실군',
    'jangheung': '장흥군', 'jangseong': '장성군', 'jeju': '제주도',
    'jeongeup': '정읍시', 'jeonju': '전주시', 'jindo': '진도군',
    'jung_busan': '부산중구', 'jung_daegu': '대구중구', 'jung_incheon': '인천중구',
    'miryang': '밀양시', 'muan': '무안군', 'muju': '무주군',
    'nam_gwangju': '광주남구', 'namdong': '남동구', 'namwon': '남원시',
    'namyangju': '남양주시', 'nonsan': '논산시', 'pocheon': '포천시',
    'pyeongtaek': '평택시', 'seo_busan': '부산서구', 'seocho': '서초구',
    'seongdong': '성동구', 'seongju': '성주군', 'seongnam': '성남시',
    'seosan': '서산시', 'siheung': '시흥시', 'sinan': '신안군',
    'sunchang': '순창군', 'taean': '태안군', 'taebaek': '태백시',
    'uijeongbu': '의정부시', 'uiryeong': '의령군', 'ulleung': '울릉군',
    'wando': '완도군', 'wanju': '완주군', 'yanggu': '양구군',
    'yangju': '양주시', 'yeoju': '여주시', 'yeongcheon': '영천시',
    'yeongdo': '영도구', 'yeonggwang': '영광군', 'yeongwol': '영월군',
    'yeongyang': '영양군', 'yeonje': '연제구', 'yesan': '예산군'
}

OUTPUT_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes")

async def search_clik_minutes(page, council_name: str) -> list:
    """CLIK에서 의회 회의록 검색"""
    records = []

    try:
        # CLIK 회의록 검색
        search_url = f"https://clik.nanet.go.kr/search/searchMinutesList.do?searchWord={council_name}의회"
        await page.goto(search_url, timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # 검색 결과 링크들 수집
        links = await page.query_selector_all('div.search_list a, table.list_table a')

        for link in links[:60]:
            try:
                title = await link.inner_text()
                title = title.strip()

                if not title or len(title) < 5:
                    continue

                href = await link.get_attribute('href')
                if not href:
                    continue

                if not href.startswith('http'):
                    href = f"https://clik.nanet.go.kr{href}"

                records.append({
                    "title": title,
                    "url": href
                })

            except:
                continue

    except Exception as e:
        print(f"    검색 오류: {e}")

    return records

async def get_minute_fulltext(page, url: str) -> str:
    """회의록 상세 페이지에서 전문 추출"""
    try:
        await page.goto(url, timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # CLIK 회의록 뷰어에서 본문 추출
        selectors = [
            'div.minutes_content',
            'div.view_content',
            'div#contentArea',
            'pre',
            'div.content',
            'iframe',
        ]

        for selector in selectors:
            elem = await page.query_selector(selector)
            if elem:
                if selector == 'iframe':
                    # iframe 내용 추출
                    frame = await elem.content_frame()
                    if frame:
                        body = await frame.query_selector('body')
                        if body:
                            text = await body.inner_text()
                            if text and len(text) > 200:
                                return text.strip()
                else:
                    text = await elem.inner_text()
                    if text and len(text) > 200:
                        return text.strip()

        # 전체 body에서 추출
        body = await page.query_selector('body')
        if body:
            text = await body.inner_text()
            # 짧은 줄 제거 (메뉴 등)
            lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 20]
            if len(lines) > 10:
                return '\n'.join(lines)

    except Exception as e:
        pass

    return ""

async def crawl_council(browser, council_code: str) -> int:
    """단일 의회 크롤링"""
    council_name = COUNCIL_NAMES.get(council_code, council_code)
    print(f"크롤링: {council_code} ({council_name})", end=" ")

    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        ignore_https_errors=True
    )
    page = await context.new_page()

    # CLIK에서 검색
    search_results = await search_clik_minutes(page, council_name)

    records = []
    for item in search_results[:50]:
        try:
            full_content = await get_minute_fulltext(page, item['url'])

            record = {
                "council_code": council_code,
                "title": item['title'],
                "detail_url": item['url'],
                "meeting_id": "",
                "cells": [item['title']],
                "crawled_at": datetime.now().isoformat(),
                "date": "",
                "full_content": full_content,
                "source": "clik"
            }
            records.append(record)

        except Exception:
            continue

    await context.close()

    # 저장
    if records:
        valid = [r for r in records if r.get('full_content') and len(r['full_content']) > 100]

        if valid:
            output_file = OUTPUT_DIR / f"{council_code}.jsonl"
            with open(output_file, 'w', encoding='utf-8') as f:
                for r in valid:
                    f.write(json.dumps(r, ensure_ascii=False) + '\n')
            print(f"✅ {len(valid)}건")
            return len(valid)
        else:
            print(f"⚠️  전문 없음")
            return 0
    else:
        print("❌ 검색결과 없음")
        return 0

async def main():
    print("=" * 60)
    print("CLIK 회의록 전문 크롤링")
    print("=" * 60 + "\n")

    # 처음 5개만 테스트
    test_councils = COUNCILS[:5]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        results = {}
        for council_code in test_councils:
            try:
                count = await crawl_council(browser, council_code)
                results[council_code] = count
            except Exception as e:
                print(f"예외: {e}")
                results[council_code] = 0

            await asyncio.sleep(2)

        await browser.close()

    print("\n" + "=" * 60)
    print(f"결과: {sum(1 for v in results.values() if v > 0)}/{len(test_councils)} 성공")

if __name__ == "__main__":
    asyncio.run(main())
