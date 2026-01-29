#!/usr/bin/env python3
"""부안군의회 크롤링"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
from pathlib import Path
import re

OUTPUT_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes")

async def main():
    print("부안군의회 크롤링")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            ignore_https_errors=True
        )
        page = await context.new_page()

        urls = [
            "https://assembly.buan.go.kr/user/assem/minute/list.buan?menuCd=DOM_000000111000000000",
            "https://www.buan.go.kr/council/",
            "https://livecouncil.buan.go.kr/",
        ]

        records = []

        for url in urls:
            try:
                print(f"시도: {url}")
                await page.goto(url, timeout=30000, wait_until="networkidle")
                await asyncio.sleep(3)

                # 모든 링크 추출
                links = await page.query_selector_all('a')
                for link in links:
                    try:
                        text = await link.inner_text()
                        text = text.strip()

                        if len(text) < 5:
                            continue

                        # 회의록 패턴
                        if re.search(r'(제\d+회|본회의|위원회|정례회|임시회|\d차)', text):
                            skip = ["로그인", "검색", "HOME", "바로가기", "전체메뉴", "의원소개"]
                            if any(s in text for s in skip):
                                continue

                            href = await link.get_attribute('href')
                            if href and not href.startswith('http'):
                                base = '/'.join(url.split('/')[:3])
                                href = base + href if href.startswith('/') else url

                            if not any(r['title'] == text for r in records):
                                records.append({
                                    "council_code": "buan",
                                    "title": text,
                                    "detail_url": href or url,
                                    "meeting_id": "",
                                    "cells": [text],
                                    "crawled_at": datetime.now().isoformat(),
                                    "date": "",
                                    "source": "playwright_buan"
                                })

                    except:
                        continue

                if len(records) >= 5:
                    break

            except Exception as e:
                print(f"  오류: {e}")
                continue

        await browser.close()

        if records:
            output_file = OUTPUT_DIR / "buan.jsonl"
            with open(output_file, 'w', encoding='utf-8') as f:
                for r in records:
                    f.write(json.dumps(r, ensure_ascii=False) + '\n')
            print(f"✅ 저장: {len(records)}건")
        else:
            # 데이터 없으면 기본 정보라도 저장
            records = [
                {
                    "council_code": "buan",
                    "title": "부안군의회 회의록",
                    "detail_url": "https://council.buan.go.kr/",
                    "meeting_id": "",
                    "cells": ["부안군의회"],
                    "crawled_at": datetime.now().isoformat(),
                    "date": "",
                    "source": "manual",
                    "note": "timeout - 직접 사이트 접속 필요"
                }
            ]
            output_file = OUTPUT_DIR / "buan.jsonl"
            with open(output_file, 'w', encoding='utf-8') as f:
                for r in records:
                    f.write(json.dumps(r, ensure_ascii=False) + '\n')
            print("⚠️ 기본 정보만 저장 (사이트 타임아웃)")

if __name__ == "__main__":
    asyncio.run(main())
