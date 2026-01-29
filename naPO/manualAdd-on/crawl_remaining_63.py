#!/usr/bin/env python3
"""
남은 63개 의회 전문 크롤링
- PHP 기반 사이트, 직접 접근 등 다양한 패턴 시도
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

# 의회별 URL 설정
COUNCIL_CONFIG = {
    'bonghwa': {
        'urls': ['https://council.bonghwa.go.kr', 'http://www.bonghwa.go.kr/open.content/council/'],
        'paths': ['/proceeding/minute/', '/source/minute/list.do']
    },
    'buk_busan': {
        'urls': ['https://council.bsbukgu.go.kr'],
        'paths': ['/proceeding/minute/', '/minute/list.do']
    },
    'buk_gwangju': {
        'urls': ['https://council.bukgu.gwangju.kr'],
        'paths': ['/board/list.php?bdId=minutes', '/proceeding/minute/']
    },
    'buk_ulsan': {
        'urls': ['https://council.bukgu.ulsan.kr'],
        'paths': ['/02_activity/activity_01.asp', '/proceeding/']
    },
    'bupyeong': {
        'urls': ['https://council.icbp.go.kr'],
        'paths': ['/open_content/main_page/minutes/minutes.do']
    },
    'cheongdo': {
        'urls': ['https://council.cheongdo.go.kr'],
        'paths': ['/sub.php?menukey=95', '/proceeding/']
    },
    'cheongsong': {
        'urls': ['https://council.cs.go.kr', 'http://www.cscouncil.go.kr'],
        'paths': ['/source/minutes/list.do', '/kr/sub04/sub02.php']
    },
    'dobong': {
        'urls': ['https://council.dobong.go.kr'],
        'paths': ['/intra/minute/list.do', '/minute/list.do']
    },
    'dong_busan': {
        'urls': ['https://council.bsdonggu.go.kr'],
        'paths': ['/proceeding/minute/', '/minute/list.do']
    },
    'dongnae': {
        'urls': ['https://council.dongnae.go.kr'],
        'paths': ['/proceeding/minute/', '/minute/list.do']
    },
    'eunpyeong': {
        'urls': ['https://council.ep.go.kr'],
        'paths': ['/minute/list.do', '/intra/minute/']
    },
    'gangneung': {
        'urls': ['https://council.gn.go.kr', 'https://www.gncl.go.kr'],
        'paths': ['/source/minutes/list.do', '/council/board/proceedings.do']
    },
    'gangseo': {
        'urls': ['https://council.gangseo.seoul.kr'],
        'paths': ['/minute/list.do', '/intra/minute/']
    },
    'gangseo_busan': {
        'urls': ['https://council.bsgangseo.go.kr'],
        'paths': ['/proceeding/minute/', '/minute/list.do']
    },
    'geumjeong': {
        'urls': ['https://council.geumjeong.go.kr'],
        'paths': ['/proceeding/minute/', '/minute/list.do']
    },
    'gijang': {
        'urls': ['https://council.gijang.go.kr'],
        'paths': ['/proceeding/minute/', '/minute/list.do']
    },
    'gimje': {
        'urls': ['https://council.gimje.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'gokseong': {
        'urls': ['https://www.gokseong.go.kr/council/'],
        'paths': ['sub04/sub01.php', '/proceeding/']
    },
    'gongju': {
        'urls': ['https://council.gongju.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'goseong_gw': {
        'urls': ['https://council.gwgs.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'guri': {
        'urls': ['https://council.guri.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'guro': {
        'urls': ['https://council.guro.go.kr'],
        'paths': ['/minute/list.do', '/intra/minute/']
    },
    'gwangsan': {
        'urls': ['https://council.gwangsan.go.kr'],
        'paths': ['/board/list.php?bdId=minutes', '/proceeding/']
    },
    'gyeongsan': {
        'urls': ['https://council.gs.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'hadong': {
        'urls': ['https://www.hdcl.go.kr'],
        'paths': ['/kr/sub04/sub02.php']
    },
    'hampyeong': {
        'urls': ['https://council.hampyeong.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'hapcheon': {
        'urls': ['https://www.hccl.go.kr'],
        'paths': ['/kr/sub04/sub02.php']
    },
    'hongcheon': {
        'urls': ['https://council.hongcheon.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'hwacheon': {
        'urls': ['https://council.ihc.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'imsil': {
        'urls': ['https://council.imsil.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'jangheung': {
        'urls': ['https://council.jangheung.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'jangseong': {
        'urls': ['https://council.jangseong.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'jeongeup': {
        'urls': ['https://council.jeongeup.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'jindo': {
        'urls': ['https://council.jindo.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'jung_busan': {
        'urls': ['https://council.bsjunggu.go.kr'],
        'paths': ['/proceeding/minute/', '/minute/list.do']
    },
    'jung_daegu': {
        'urls': ['https://www.junggucouncil.daegu.kr'],
        'paths': ['/contents.do?key=1114', '/proceeding/']
    },
    'jung_incheon': {
        'urls': ['https://council.icjg.go.kr'],
        'paths': ['/proceeding/minute/', '/minute/list.do']
    },
    'miryang': {
        'urls': ['https://council.miryang.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'muan': {
        'urls': ['http://www.muan.or.kr'],
        'paths': ['/kr/sub04/sub02.php']
    },
    'muju': {
        'urls': ['https://council.muju.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'namdong': {
        'urls': ['https://council.namdong.go.kr'],
        'paths': ['/proceeding/minute/', '/minute/list.do']
    },
    'namwon': {
        'urls': ['https://council.namwon.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'namyangju': {
        'urls': ['https://www.nyjc.go.kr', 'https://council.nyj.go.kr'],
        'paths': ['/board/proceedings.do', '/source/minute/list.do']
    },
    'nonsan': {
        'urls': ['https://council.nonsan.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'pocheon': {
        'urls': ['https://council.pocheon.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'pyeongtaek': {
        'urls': ['https://council.pyeongtaek.go.kr'],
        'paths': ['/source/minute/list.do', '/proceeding/']
    },
    'seo_busan': {
        'urls': ['https://council.bsseogu.go.kr'],
        'paths': ['/proceeding/minute/', '/minute/list.do']
    },
    'seocho': {
        'urls': ['https://council.seocho.go.kr'],
        'paths': ['/minute/list.do', '/intra/minute/']
    },
    'seongdong': {
        'urls': ['https://council.sd.go.kr', 'https://sdcouncil.sd.go.kr'],
        'paths': ['/minute/list.do', '/intra/minute/']
    },
    'seongju': {
        'urls': ['https://www.sjcouncil.go.kr'],
        'paths': ['/kr/sub04/sub02.php', '/source/minutes/list.do']
    },
    'seongnam': {
        'urls': ['https://council.seongnam.go.kr'],
        'paths': ['/source/minute/list.do', '/proceeding/']
    },
    'siheung': {
        'urls': ['https://council.siheung.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'sinan': {
        'urls': ['https://council.sinan.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'sunchang': {
        'urls': ['https://www.sunchangcouncil.go.kr'],
        'paths': ['/kr/sub04/sub02.php', '/source/minutes/list.do']
    },
    'suyeong': {
        'urls': ['https://council.suyeong.go.kr'],
        'paths': ['/proceeding/minute/', '/minute/list.do']
    },
    'taebaek': {
        'urls': ['https://council.taebaek.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'uiryeong': {
        'urls': ['https://council.uiryeong.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'ulleung': {
        'urls': ['https://council.ulleung.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'wando': {
        'urls': ['http://www.wdcc.or.kr'],
        'paths': ['/kr/sub04/sub02.php']
    },
    'yeoju': {
        'urls': ['https://council.yeoju.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
    },
    'yeongdo': {
        'urls': ['https://council.yeongdo.go.kr'],
        'paths': ['/proceeding/minute/', '/minute/list.do']
    },
    'yeonje': {
        'urls': ['https://council.yeonje.go.kr'],
        'paths': ['/proceeding/minute/', '/minute/list.do']
    },
    'yesan': {
        'urls': ['https://council.yesan.go.kr'],
        'paths': ['/source/minutes/list.do', '/proceeding/']
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
        'div.view_content', 'div.content_view', 'div.minutes_view',
        'div.board_view', 'pre', 'article', 'div.detail_content',
        'div#contentArea', 'div.con_wrap', 'table.view_table',
        'div.bbs_view', 'div.bd_view', 'div.minutes_content'
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
                return '\n'.join(lines[:200])
    except:
        pass

    return ""

async def crawl_council(browser, council_code: str) -> int:
    """의회 크롤링"""
    config = COUNCIL_CONFIG.get(council_code, {})
    urls = config.get('urls', [])
    paths = config.get('paths', [])

    if not urls:
        return 0

    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        ignore_https_errors=True
    )
    page = await context.new_page()

    records = []

    for base_url in urls:
        for path in paths:
            try:
                url = base_url + path
                await page.goto(url, timeout=12000, wait_until="domcontentloaded")
                await asyncio.sleep(2)

                # 목록에서 회의록 링크 찾기
                links = await page.query_selector_all('a')
                minute_items = []

                for link in links:
                    try:
                        text = await link.inner_text()
                        text = text.strip()

                        if 5 < len(text) < 150 and re.search(r'(제\d+회|본회의|위원회|정례회|임시회|\d차)', text):
                            href = await link.get_attribute('href')

                            if href and 'javascript' not in href.lower() and '#' != href:
                                if not href.startswith('http'):
                                    href = base_url + (href if href.startswith('/') else '/' + href)
                                minute_items.append({'title': text, 'url': href})
                    except:
                        continue

                # 상세 페이지에서 전문 추출
                for item in minute_items[:50]:
                    try:
                        await page.goto(item['url'], timeout=10000, wait_until="domcontentloaded")
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
                                "source": "remaining_63"
                            }
                            records.append(record)

                    except:
                        continue

                if records:
                    break

            except Exception:
                continue

        if records:
            break

    await context.close()

    # 저장
    if records:
        output_file = OUTPUT_DIR / f"{council_code}.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        return len(records)

    return 0

async def main():
    print("=" * 60)
    print("남은 63개 의회 전문 크롤링")
    print("=" * 60 + "\n")

    start_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end_idx = int(sys.argv[2]) if len(sys.argv) > 2 else len(REMAINING)

    councils = REMAINING[start_idx:end_idx]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        results = {}
        for i, code in enumerate(councils):
            print(f"[{i+1}/{len(councils)}] {code}", end=" ", flush=True)
            try:
                count = await crawl_council(browser, code)
                results[code] = count
                print(f"✅ {count}건" if count > 0 else "❌")
            except Exception as e:
                print(f"오류: {str(e)[:20]}")
                results[code] = 0

            await asyncio.sleep(0.5)

        await browser.close()

    success = sum(1 for v in results.values() if v > 0)
    total = sum(results.values())
    print(f"\n성공: {success}/{len(councils)} | 총 {total}건")

if __name__ == "__main__":
    asyncio.run(main())
