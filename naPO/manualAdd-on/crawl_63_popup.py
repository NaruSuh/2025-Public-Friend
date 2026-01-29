#!/usr/bin/env python3
"""
63개 의회 회의록 전문 크롤링 - 팝업 URL 직접 접근
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
from pathlib import Path
import re
import sys

# 서울시 자치구 의회 URL 패턴 (popup.do 직접 접근)
SEOUL_COUNCILS = {
    'dobong': 'https://www.council-dobong.seoul.kr',
    'eunpyeong': 'https://www.epcouncil.seoul.kr',
    'gangseo': 'https://gsc.gangseo.seoul.kr',
    'guro': 'https://www.council-guro.seoul.kr',
    'seocho': 'https://www.council-seocho.seoul.kr',
    'seongdong': 'https://www.sdcouncil.seoul.kr',
}

# 부산시 자치구 의회
BUSAN_COUNCILS = {
    'buk_busan': 'https://council.bsbukgu.go.kr',
    'dong_busan': 'https://council.bsdonggu.go.kr',
    'dongnae': 'https://council.dongnae.go.kr',
    'gangseo_busan': 'https://council.bsgangseo.go.kr',
    'geumjeong': 'https://council.geumjeong.go.kr',
    'gijang': 'https://council.gijang.go.kr',
    'jung_busan': 'https://council.bsjunggu.go.kr',
    'seo_busan': 'https://council.bsseogu.go.kr',
    'suyeong': 'https://council.suyeong.go.kr',
    'yeongdo': 'https://council.yeongdo.go.kr',
}

# 기타 의회 (표준 전자회의록 시스템)
OTHER_COUNCILS = {
    'bupyeong': 'https://council.icbp.go.kr',
    'namdong': 'https://council.namdong.go.kr',
    'jung_incheon': 'https://council.icjg.go.kr',
    'buk_gwangju': 'https://council.bukgu.gwangju.kr',
    'gwangsan': 'https://council.gwangsan.go.kr',
    'jung_daegu': 'https://www.junggucouncil.daegu.kr',
    'buk_ulsan': 'https://council.bukgu.ulsan.kr',
    'guri': 'https://council.guri.go.kr',
    'namyangju': 'https://www.nyjc.go.kr',
    'pyeongtaek': 'https://council.pyeongtaek.go.kr',
    'pocheon': 'https://council.pocheon.go.kr',
    'seongnam': 'https://council.seongnam.go.kr',
    'siheung': 'https://council.siheung.go.kr',
    'yeoju': 'https://council.yeoju.go.kr',
    'gangneung': 'https://www.gncl.go.kr',
    'goseong_gw': 'https://council.gwgs.go.kr',
    'hongcheon': 'https://council.hongcheon.go.kr',
    'hwacheon': 'https://council.ihc.go.kr',
    'gongju': 'https://council.gongju.go.kr',
    'nonsan': 'https://council.nonsan.go.kr',
    'gimje': 'https://council.gimje.go.kr',
    'imsil': 'https://council.imsil.go.kr',
    'jeongeup': 'https://council.jeongeup.go.kr',
    'muju': 'https://council.muju.go.kr',
    'namwon': 'https://council.namwon.go.kr',
    'gokseong': 'https://www.gokseong.go.kr',
    'hadong': 'https://www.hdcl.go.kr',
    'hampyeong': 'https://council.hampyeong.go.kr',
    'hapcheon': 'https://www.hccl.go.kr',
    'jangheung': 'https://council.jangheung.go.kr',
    'jangseong': 'https://council.jangseong.go.kr',
    'jindo': 'https://council.jindo.go.kr',
    'muan': 'http://www.muan.or.kr',
    'sinan': 'https://council.sinan.go.kr',
    'sunchang': 'https://www.sunchangcouncil.go.kr',
    'wando': 'http://www.wdcc.or.kr',
    'bonghwa': 'https://council.bonghwa.go.kr',
    'cheongdo': 'https://council.cheongdo.go.kr',
    'cheongsong': 'https://council.cs.go.kr',
    'gyeongsan': 'https://council.gs.go.kr',
    'miryang': 'https://council.miryang.go.kr',
    'seongju': 'https://www.sjcouncil.go.kr',
    'uiryeong': 'https://council.uiryeong.go.kr',
    'ulleung': 'https://council.ulleung.go.kr',
    'taebaek': 'https://council.taebaek.go.kr',
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
        'div.minView', 'div#minView', 'div.viewContent',
        'div.popCon', 'div.pop_content', 'div#pop_content'
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

async def crawl_seoul_council(browser, council_code: str, base_url: str) -> int:
    """서울시 자치구 의회 크롤링 (popup.do 패턴)"""
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        ignore_https_errors=True
    )
    page = await context.new_page()

    records = []

    try:
        # 최근 회의록 목록 페이지
        list_url = f"{base_url}/meeting/confer/recent.do"
        await page.goto(list_url, timeout=20000, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # 회기 번호 추출 (ntime 파라미터)
        content = await page.content()
        ntime_match = re.search(r'ntime["\s]*[:=]["\s]*(\d+)', content)
        if not ntime_match:
            # URL에서 추출 시도
            ntime_match = re.search(r'ntime=(\d+)', content)

        if ntime_match:
            ntime = ntime_match.group(1)
        else:
            # 기본값 사용 (최근 회기)
            ntime = "348"

        # 여러 회의 유형과 차수에 대해 팝업 접근
        meeting_types = [
            (2, 1, "본회의"),  # contype=2, subtype=1: 본회의
            (3, 1, "운영위원회"),  # contype=3: 위원회
        ]

        for contype, subtype, type_name in meeting_types:
            for num in range(1, 6):  # 1~5차
                try:
                    popup_url = f"{base_url}/meeting/confer/popup.do?ntime={ntime}&contype={contype}&subtype={subtype}&num={num}"
                    await page.goto(popup_url, timeout=15000, wait_until="domcontentloaded")
                    await asyncio.sleep(1)

                    content = await extract_content(page)

                    if content and len(content) > 500:
                        title = f"제{ntime}회 {type_name} 제{num}차"
                        record = {
                            "council_code": council_code,
                            "title": title,
                            "detail_url": popup_url,
                            "meeting_id": f"{ntime}_{contype}_{num}",
                            "cells": [title],
                            "crawled_at": datetime.now().isoformat(),
                            "date": "",
                            "full_content": content,
                            "source": "seoul_popup"
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

async def crawl_standard_council(browser, council_code: str, base_url: str) -> int:
    """표준 전자회의록 시스템 크롤링"""
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        ignore_https_errors=True
    )
    page = await context.new_page()

    records = []

    # 시도할 경로들
    paths = [
        '/source/minute/list.do',
        '/source/minutes/list.do',
        '/record/selectRecordList.do',
        '/board/proceedings.do',
        '/meeting/confer/recent.do',
        '/kr/sub04/sub02.php',
    ]

    for path in paths:
        try:
            url = base_url + path
            await page.goto(url, timeout=15000, wait_until="domcontentloaded")
            await asyncio.sleep(2)

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
                            "source": "standard_minutes"
                        }
                        records.append(record)

                except:
                    continue

            if records:
                break

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
    print("63개 의회 회의록 전문 크롤링 - 팝업/표준 패턴")
    print("=" * 60 + "\n")

    all_councils = {}
    all_councils.update({k: ('seoul', v) for k, v in SEOUL_COUNCILS.items()})
    all_councils.update({k: ('busan', v) for k, v in BUSAN_COUNCILS.items()})
    all_councils.update({k: ('other', v) for k, v in OTHER_COUNCILS.items()})

    start_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end_idx = int(sys.argv[2]) if len(sys.argv) > 2 else len(all_councils)

    councils = list(all_councils.items())[start_idx:end_idx]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        results = {}
        for i, (code, (ctype, url)) in enumerate(councils):
            print(f"[{i+1}/{len(councils)}] {code} ({ctype})", end=" ", flush=True)
            try:
                if ctype == 'seoul':
                    count = await crawl_seoul_council(browser, code, url)
                else:
                    count = await crawl_standard_council(browser, code, url)

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
