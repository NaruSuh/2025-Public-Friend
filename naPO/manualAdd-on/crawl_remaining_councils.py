#!/usr/bin/env python3
"""
남은 59개 의회 회의록 전문 크롤링
- 확인된 URL 사용
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
from pathlib import Path
import re
import sys

# 남은 의회 URL (확인된 것들)
COUNCIL_URLS = {
    # 경기도
    'guri': {'base': 'https://www.gcc.or.kr', 'popup': '/meeting/confer/popup.do'},
    'guro': {'base': 'https://council.guro.go.kr', 'popup': '/meeting/confer/popup.do'},
    'namyangju': {'base': 'https://www.nyjc.go.kr', 'popup': '/meeting/confer/popup.do'},
    'pyeongtaek': {'base': 'https://council.pyeongtaek.go.kr', 'popup': '/meeting/confer/popup.do'},
    'pocheon': {'base': 'https://council.pocheon.go.kr', 'popup': '/meeting/confer/popup.do'},
    'seongnam': {'base': 'https://council.seongnam.go.kr', 'popup': '/meeting/confer/popup.do'},
    'siheung': {'base': 'https://council.siheung.go.kr', 'popup': '/meeting/confer/popup.do'},
    'yeoju': {'base': 'https://council.yeoju.go.kr', 'popup': '/meeting/confer/popup.do'},

    # 서울
    'gangseo': {'base': 'https://gsc.gangseo.seoul.kr', 'popup': '/meeting/confer/popup.do'},
    'seocho': {'base': 'https://council.seocho.go.kr', 'popup': '/meeting/confer/popup.do'},
    'seongdong': {'base': 'https://council.sd.go.kr', 'popup': '/meeting/confer/popup.do'},

    # 강원도
    'gangneung': {'base': 'https://www.gncl.go.kr', 'popup': '/meeting/confer/popup.do'},
    'hongcheon': {'base': 'https://council.hongcheon.go.kr', 'popup': '/meeting/confer/popup.do'},
    'hwacheon': {'base': 'https://council.ihc.go.kr', 'popup': '/meeting/confer/popup.do'},
    'goseong_gw': {'base': 'https://council.gwgs.go.kr', 'popup': '/meeting/confer/popup.do'},

    # 충청도
    'gongju': {'base': 'https://council.gongju.go.kr', 'popup': '/meeting/confer/popup.do'},
    'nonsan': {'base': 'https://council.nonsan.go.kr', 'popup': '/meeting/confer/popup.do'},

    # 전라도
    'gimje': {'base': 'https://council.gimje.go.kr', 'popup': '/meeting/confer/popup.do'},
    'jeongeup': {'base': 'https://council.jeongeup.go.kr', 'popup': '/meeting/confer/popup.do'},
    'muju': {'base': 'https://council.muju.go.kr', 'popup': '/meeting/confer/popup.do'},
    'namwon': {'base': 'https://council.namwon.go.kr', 'popup': '/meeting/confer/popup.do'},
    'jindo': {'base': 'https://council.jindo.go.kr', 'popup': '/meeting/confer/popup.do'},
    'hampyeong': {'base': 'https://council.hampyeong.go.kr', 'popup': '/meeting/confer/popup.do'},
    'jangheung': {'base': 'https://council.jangheung.go.kr', 'popup': '/meeting/confer/popup.do'},
    'jangseong': {'base': 'https://council.jangseong.go.kr', 'popup': '/meeting/confer/popup.do'},
    'sinan': {'base': 'https://council.sinan.go.kr', 'popup': '/meeting/confer/popup.do'},

    # 경상도
    'bonghwa': {'base': 'https://council.bonghwa.go.kr', 'popup': '/meeting/confer/popup.do'},
    'cheongdo': {'base': 'https://council.cheongdo.go.kr', 'popup': '/meeting/confer/popup.do'},
    'cheongsong': {'base': 'https://council.cs.go.kr', 'popup': '/meeting/confer/popup.do'},
    'gyeongsan': {'base': 'https://council.gs.go.kr', 'popup': '/meeting/confer/popup.do'},
    'miryang': {'base': 'https://council.miryang.go.kr', 'popup': '/meeting/confer/popup.do'},
    'uiryeong': {'base': 'https://council.uiryeong.go.kr', 'popup': '/meeting/confer/popup.do'},
    'ulleung': {'base': 'https://council.ulleung.go.kr', 'popup': '/meeting/confer/popup.do'},
    'taebaek': {'base': 'https://council.taebaek.go.kr', 'popup': '/meeting/confer/popup.do'},
}

OUTPUT_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes")

async def extract_content(page) -> str:
    """페이지에서 회의록 전문 추출"""
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

    selectors = ['div.view_content', 'pre', 'article', 'div#contentArea', 'div.popCon']
    for sel in selectors:
        try:
            elem = await page.query_selector(sel)
            if elem:
                text = await elem.inner_text()
                if text and len(text) > 500:
                    return text.strip()
        except:
            pass

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

async def crawl_council(browser, council_code: str, config: dict) -> int:
    """의회 크롤링"""
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        ignore_https_errors=True
    )
    page = await context.new_page()

    records = []
    base_url = config['base']
    popup_path = config['popup']

    # 회기 번호 추정 (최근 것부터)
    ntimes = list(range(345, 330, -1))  # 345~331

    for ntime in ntimes:
        # 본회의 (contype=1 또는 2)
        for contype in [1, 2]:
            for num in range(1, 5):
                try:
                    popup_url = f"{base_url}{popup_path}?ntime={ntime}&contype={contype}&subtype=1&num={num}"
                    await page.goto(popup_url, timeout=10000, wait_until="domcontentloaded")
                    await asyncio.sleep(1)

                    content = await extract_content(page)

                    if content and len(content) > 500:
                        title = f"제{ntime}회 본회의 제{num}차"
                        record = {
                            "council_code": council_code,
                            "title": title,
                            "detail_url": popup_url,
                            "meeting_id": f"{ntime}_{contype}_{num}",
                            "cells": [title],
                            "crawled_at": datetime.now().isoformat(),
                            "date": "",
                            "full_content": content,
                            "source": "remaining_councils"
                        }
                        records.append(record)

                except:
                    continue

        if len(records) >= 50:
            break

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
    print("남은 의회 회의록 전문 크롤링")
    print("=" * 60 + "\n")

    start_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end_idx = int(sys.argv[2]) if len(sys.argv) > 2 else len(COUNCIL_URLS)

    councils = list(COUNCIL_URLS.items())[start_idx:end_idx]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        results = {}
        for i, (code, config) in enumerate(councils):
            print(f"[{i+1}/{len(councils)}] {code}", end=" ", flush=True)
            try:
                count = await crawl_council(browser, code, config)
                results[code] = count
                print(f"✅ {count}건" if count > 0 else "❌")
            except Exception as e:
                print(f"오류")
                results[code] = 0

            await asyncio.sleep(0.5)

        await browser.close()

    success = sum(1 for v in results.values() if v > 0)
    total = sum(results.values())
    print(f"\n성공: {success}/{len(councils)} | 총 {total}건")

if __name__ == "__main__":
    asyncio.run(main())
