#!/usr/bin/env python3
"""
부산시 자치구 의회 회의록 전문 크롤링
- minutes.XXX.go.kr 패턴 사용
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
from pathlib import Path
import re
import sys

# 부산시 자치구 의회 회의록 시스템 URL
BUSAN_COUNCILS = {
    'buk_busan': 'https://minutes.bsbukgu.go.kr:8443/minutes/assembly/sub/late.html',
    'dong_busan': 'https://minutes.bsdonggu.go.kr:8443/minutes/assembly/sub/late.html',
    'dongnae': 'https://minutes.dongnae.go.kr:8443/minutes/assembly/sub/late.html',
    'gangseo_busan': 'https://minutes.bsgangseo.go.kr:8443/minutes/assembly/sub/late.html',
    'geumjeong': 'https://minutes.geumjeong.go.kr:8443/minutes/assembly/sub/late.html',
    'gijang': 'https://minutes.gijang.go.kr:8443/minutes/assembly/sub/late.html',
    'jung_busan': 'https://minutes.bsjunggu.go.kr:8443/minutes/assembly/sub/late.html',
    'seo_busan': 'https://minutes.bsseogu.go.kr:8443/minutes/assembly/sub/late.html',
    'suyeong': 'https://minutes.suyeong.go.kr:8443/minutes/assembly/sub/late.html',
    'yeongdo': 'https://minutes.yeongdo.go.kr:8443/minutes/assembly/sub/late.html',
}

OUTPUT_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes")

async def extract_content(page) -> str:
    """페이지에서 회의록 전문 추출"""
    # iframe 확인
    for frame in page.frames:
        if frame != page.main_frame:
            try:
                body = await frame.query_selector('body')
                if body:
                    text = await body.inner_text()
                    if text and len(text) > 1000:
                        return text.strip()
            except:
                pass

    # 본문 선택자
    selectors = [
        'div.view_content', 'div.content_view', 'pre', 'article',
        'div#contentArea', 'div.popCon', 'div.minutes_content',
        'table.view_table', 'div.board_view'
    ]

    for sel in selectors:
        try:
            elem = await page.query_selector(sel)
            if elem:
                text = await elem.inner_text()
                if text and len(text) > 500:
                    return text.strip()
        except:
            pass

    # body 전체
    try:
        body = await page.query_selector('body')
        if body:
            text = await body.inner_text()
            lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 30]
            if len(lines) > 30:
                return '\n'.join(lines[:300])
    except:
        pass

    return ""

async def crawl_council(browser, council_code: str, url: str) -> int:
    """의회 크롤링"""
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        ignore_https_errors=True
    )
    page = await context.new_page()

    records = []
    base_url = '/'.join(url.split('/')[:3])

    try:
        await page.goto(url, timeout=20000, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # 회의록 링크 찾기
        links = await page.query_selector_all('a')
        minute_items = []

        for link in links:
            try:
                text = await link.inner_text()
                text = text.strip()

                if 5 < len(text) < 150 and re.search(r'(제\d+회|본회의|위원회|정례회|임시회|\d차)', text):
                    href = await link.get_attribute('href')
                    onclick = await link.get_attribute('onclick')

                    if href and 'javascript' not in href.lower() and href != '#':
                        if not href.startswith('http'):
                            href = base_url + (href if href.startswith('/') else '/' + href)
                        minute_items.append({'title': text, 'url': href, 'onclick': None})
                    elif onclick:
                        minute_items.append({'title': text, 'url': url, 'onclick': onclick})
            except:
                continue

        # 상세 페이지 크롤링
        for item in minute_items[:50]:
            try:
                if item.get('onclick'):
                    await page.evaluate(item['onclick'])
                    await asyncio.sleep(2)
                else:
                    await page.goto(item['url'], timeout=12000, wait_until="domcontentloaded")
                    await asyncio.sleep(1)

                content = await extract_content(page)

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
                        "source": "busan_minutes"
                    }
                    records.append(record)

            except:
                continue

    except Exception as e:
        pass

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
    print("부산시 자치구 의회 회의록 전문 크롤링")
    print("=" * 60 + "\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        results = {}
        for code, url in BUSAN_COUNCILS.items():
            print(f"크롤링: {code}", end=" ", flush=True)
            try:
                count = await crawl_council(browser, code, url)
                results[code] = count
                print(f"✅ {count}건" if count > 0 else "❌")
            except Exception as e:
                print(f"오류: {str(e)[:20]}")
                results[code] = 0

            await asyncio.sleep(1)

        await browser.close()

    success = sum(1 for v in results.values() if v > 0)
    total = sum(results.values())
    print(f"\n성공: {success}/{len(BUSAN_COUNCILS)} | 총 {total}건")

if __name__ == "__main__":
    asyncio.run(main())
