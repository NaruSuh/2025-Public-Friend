#!/usr/bin/env python3
"""
63개 의회 회의록 전문 크롤링 - 최종 버전
검증된 URL 패턴 사용
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
from pathlib import Path
import re
import sys

# 63개 의회의 검증된 URL
COUNCIL_URLS = {
    # 서울시 자치구 (council-XXX.seoul.kr 패턴)
    'dobong': 'https://www.council-dobong.seoul.kr/meeting/confer/recent.do',
    'eunpyeong': 'https://www.epcouncil.seoul.kr/meeting/confer/recent.do',
    'gangseo': 'https://gsc.gangseo.seoul.kr/meeting/confer/recent.do',
    'guro': 'https://www.council-guro.seoul.kr/meeting/confer/recent.do',
    'seocho': 'https://www.council-seocho.seoul.kr/meeting/confer/recent.do',
    'seongdong': 'https://www.sdcouncil.seoul.kr/meeting/confer/recent.do',

    # 부산시 자치구
    'buk_busan': 'https://council.bsbukgu.go.kr/record/selectRecordList.do',
    'dong_busan': 'https://council.bsdonggu.go.kr/record/selectRecordList.do',
    'dongnae': 'https://council.dongnae.go.kr/record/selectRecordList.do',
    'gangseo_busan': 'https://council.bsgangseo.go.kr/record/selectRecordList.do',
    'geumjeong': 'https://council.geumjeong.go.kr/record/selectRecordList.do',
    'gijang': 'https://council.gijang.go.kr/record/selectRecordList.do',
    'jung_busan': 'https://council.bsjunggu.go.kr/record/selectRecordList.do',
    'seo_busan': 'https://council.bsseogu.go.kr/record/selectRecordList.do',
    'suyeong': 'https://council.suyeong.go.kr/record/selectRecordList.do',
    'yeongdo': 'https://council.yeongdo.go.kr/record/selectRecordList.do',

    # 인천시 자치구
    'bupyeong': 'https://council.icbp.go.kr/record/selectRecordList.do',
    'namdong': 'https://council.namdong.go.kr/record/selectRecordList.do',
    'jung_incheon': 'https://council.icjg.go.kr/record/selectRecordList.do',

    # 광주시 자치구
    'buk_gwangju': 'https://council.bukgu.gwangju.kr/board/proceedings.do',
    'gwangsan': 'https://council.gwangsan.go.kr/board/proceedings.do',

    # 대구시 자치구
    'jung_daegu': 'https://www.junggucouncil.daegu.kr/board/minutes/list.do',

    # 울산시 자치구
    'buk_ulsan': 'https://council.bukgu.ulsan.kr/minutes/list.do',

    # 경기도
    'guri': 'https://council.guri.go.kr/source/minute/list.do',
    'namyangju': 'https://www.nyjc.go.kr/board/proceedings.do',
    'pyeongtaek': 'https://council.pyeongtaek.go.kr/source/minute/list.do',
    'pocheon': 'https://council.pocheon.go.kr/source/minute/list.do',
    'seongnam': 'https://council.seongnam.go.kr/source/minute/list.do',
    'siheung': 'https://council.siheung.go.kr/source/minute/list.do',
    'yeoju': 'https://council.yeoju.go.kr/source/minute/list.do',

    # 강원도
    'gangneung': 'https://www.gncl.go.kr/council/board/proceedings.do',
    'goseong_gw': 'https://council.gwgs.go.kr/source/minute/list.do',
    'hongcheon': 'https://council.hongcheon.go.kr/source/minute/list.do',
    'hwacheon': 'https://council.ihc.go.kr/source/minute/list.do',

    # 충청남도
    'gongju': 'https://council.gongju.go.kr/source/minute/list.do',
    'nonsan': 'https://council.nonsan.go.kr/source/minute/list.do',

    # 전라북도
    'gimje': 'https://council.gimje.go.kr/source/minute/list.do',
    'imsil': 'https://council.imsil.go.kr/source/minute/list.do',
    'jeongeup': 'https://council.jeongeup.go.kr/source/minute/list.do',
    'muju': 'https://council.muju.go.kr/source/minute/list.do',
    'namwon': 'https://council.namwon.go.kr/source/minute/list.do',

    # 전라남도
    'gokseong': 'https://www.gokseong.go.kr/council/board/proceedings.do',
    'hadong': 'https://www.hdcl.go.kr/board/proceedings.do',
    'hampyeong': 'https://council.hampyeong.go.kr/source/minute/list.do',
    'hapcheon': 'https://www.hccl.go.kr/board/proceedings.do',
    'jangheung': 'https://council.jangheung.go.kr/source/minute/list.do',
    'jangseong': 'https://council.jangseong.go.kr/source/minute/list.do',
    'jindo': 'https://council.jindo.go.kr/source/minute/list.do',
    'muan': 'http://www.muan.or.kr/board/proceedings.do',
    'sinan': 'https://council.sinan.go.kr/source/minute/list.do',
    'sunchang': 'https://www.sunchangcouncil.go.kr/board/proceedings.do',
    'wando': 'http://www.wdcc.or.kr/board/proceedings.do',

    # 경상북도
    'bonghwa': 'https://council.bonghwa.go.kr/source/minute/list.do',
    'cheongdo': 'https://council.cheongdo.go.kr/source/minute/list.do',
    'cheongsong': 'https://council.cs.go.kr/source/minute/list.do',
    'gyeongsan': 'https://council.gs.go.kr/source/minute/list.do',
    'miryang': 'https://council.miryang.go.kr/source/minute/list.do',
    'seongju': 'https://www.sjcouncil.go.kr/board/proceedings.do',
    'uiryeong': 'https://council.uiryeong.go.kr/source/minute/list.do',
    'ulleung': 'https://council.ulleung.go.kr/source/minute/list.do',

    # 경상남도
    'taebaek': 'https://council.taebaek.go.kr/source/minute/list.do',
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
        'div.bbs_view', 'div.bd_view', 'div.minutes_content',
        'div.minView', 'div#minView', 'div.viewContent'
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

    try:
        await page.goto(url, timeout=20000, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # 목록에서 회의록 링크 찾기
        links = await page.query_selector_all('a')
        minute_items = []
        base_url = '/'.join(url.split('/')[:3])

        for link in links:
            try:
                text = await link.inner_text()
                text = text.strip()

                if 5 < len(text) < 150 and re.search(r'(제\d+회|본회의|위원회|정례회|임시회|\d차|회의록)', text):
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

        # 상세 페이지에서 전문 추출
        for item in minute_items[:50]:
            try:
                if item.get('onclick'):
                    try:
                        await page.evaluate(item['onclick'])
                        await asyncio.sleep(2)
                    except:
                        continue
                else:
                    await page.goto(item['url'], timeout=15000, wait_until="domcontentloaded")
                    await asyncio.sleep(2)

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
                        "source": "final_63"
                    }
                    records.append(record)

            except Exception as e:
                continue

    except Exception as e:
        pass

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
    print("63개 의회 회의록 전문 크롤링 - 최종")
    print("=" * 60 + "\n")

    start_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end_idx = int(sys.argv[2]) if len(sys.argv) > 2 else len(COUNCIL_URLS)

    councils = list(COUNCIL_URLS.items())[start_idx:end_idx]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        results = {}
        for i, (code, url) in enumerate(councils):
            print(f"[{i+1}/{len(councils)}] {code}", end=" ", flush=True)
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
    print(f"\n성공: {success}/{len(councils)} | 총 {total}건")

if __name__ == "__main__":
    asyncio.run(main())
