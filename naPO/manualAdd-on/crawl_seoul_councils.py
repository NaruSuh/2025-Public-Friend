#!/usr/bin/env python3
"""
서울시 자치구 의회 회의록 전문 크롤링
- 실제 작동 URL 사용
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
from pathlib import Path
import re
import sys

# 서울시 자치구 의회 URL (실제 작동 확인)
SEOUL_COUNCILS = {
    'dobong': {
        'base': 'https://www.council-dobong.seoul.kr',
        'list': '/meeting/confer/recent.do',
        'popup': '/meeting/confer/popup.do'
    },
    'eunpyeong': {
        'base': 'https://council.ep.go.kr',
        'list': '/meeting/confer/main.do',
        'popup': '/meeting/confer/popup.do'
    },
    'gangseo': {
        'base': 'https://gsc.gangseo.seoul.kr',
        'list': '/meeting/confer/recent.do',
        'popup': '/meeting/confer/popup.do'
    },
    'guro': {
        'base': 'https://council.guro.go.kr',
        'list': '/meeting/confer/main.do',
        'popup': '/meeting/confer/popup.do'
    },
    'seocho': {
        'base': 'https://council.seocho.go.kr',
        'list': '/meeting/confer/main.do',
        'popup': '/meeting/confer/popup.do'
    },
    'seongdong': {
        'base': 'https://council.sd.go.kr',
        'list': '/meeting/confer/main.do',
        'popup': '/meeting/confer/popup.do'
    },
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
        'div#contentArea', 'div.popCon', 'div.pop_content',
        'body'
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

    try:
        # 1. 목록 페이지에서 회기 정보 추출
        list_url = base_url + config['list']
        await page.goto(list_url, timeout=20000, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # ntime (회기 번호) 추출
        content = await page.content()
        ntime_matches = re.findall(r'ntime["\s]*[:=]["\s]*["\']?(\d+)', content)
        if not ntime_matches:
            ntime_matches = re.findall(r'ntime=(\d+)', content)

        if ntime_matches:
            ntimes = list(set(ntime_matches))[:5]  # 최대 5개 회기
        else:
            ntimes = ["319", "318", "317"]  # 기본값

        # 2. 각 회기별로 팝업 접근
        for ntime in ntimes:
            # 본회의 (contype=2)
            for num in range(1, 6):
                try:
                    popup_url = f"{base_url}{config['popup']}?ntime={ntime}&contype=2&subtype=1&num={num}"
                    await page.goto(popup_url, timeout=12000, wait_until="domcontentloaded")
                    await asyncio.sleep(1)

                    content = await extract_content(page)

                    if content and len(content) > 500:
                        title = f"제{ntime}회 본회의 제{num}차"
                        record = {
                            "council_code": council_code,
                            "title": title,
                            "detail_url": popup_url,
                            "meeting_id": f"{ntime}_2_{num}",
                            "cells": [title],
                            "crawled_at": datetime.now().isoformat(),
                            "date": "",
                            "full_content": content,
                            "source": "seoul_council"
                        }
                        records.append(record)

                except:
                    continue

            # 위원회 (contype=3, 4, 5, ...)
            for contype in range(3, 8):
                for num in range(1, 4):
                    try:
                        popup_url = f"{base_url}{config['popup']}?ntime={ntime}&contype={contype}&subtype=1&num={num}"
                        await page.goto(popup_url, timeout=10000, wait_until="domcontentloaded")
                        await asyncio.sleep(0.5)

                        content = await extract_content(page)

                        if content and len(content) > 500:
                            title = f"제{ntime}회 위원회{contype} 제{num}차"
                            record = {
                                "council_code": council_code,
                                "title": title,
                                "detail_url": popup_url,
                                "meeting_id": f"{ntime}_{contype}_{num}",
                                "cells": [title],
                                "crawled_at": datetime.now().isoformat(),
                                "date": "",
                                "full_content": content,
                                "source": "seoul_council"
                            }
                            records.append(record)

                    except:
                        continue

            if len(records) >= 50:
                break

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
    print("서울시 자치구 의회 회의록 전문 크롤링")
    print("=" * 60 + "\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        results = {}
        for code, config in SEOUL_COUNCILS.items():
            print(f"크롤링: {code}", end=" ", flush=True)
            try:
                count = await crawl_council(browser, code, config)
                results[code] = count
                print(f"✅ {count}건" if count > 0 else "❌")
            except Exception as e:
                print(f"오류: {str(e)[:20]}")
                results[code] = 0

            await asyncio.sleep(1)

        await browser.close()

    success = sum(1 for v in results.values() if v > 0)
    total = sum(results.values())
    print(f"\n성공: {success}/{len(SEOUL_COUNCILS)} | 총 {total}건")

if __name__ == "__main__":
    asyncio.run(main())
