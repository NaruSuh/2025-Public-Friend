#!/usr/bin/env python3
"""
86개 의회 회의록 전문 크롤링 - 공격적 접근
각 의회 메인 페이지에서 회의록 링크 탐색
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
from pathlib import Path
import re
import sys

# 전문 없는 86개 의회
NO_FULLCONTENT = [
    'asan', 'bonghwa', 'boryeong', 'boseong', 'buk_busan', 'buk_gwangju',
    'buk_ulsan', 'bupyeong', 'cheongdo', 'cheongsong', 'dobong', 'dong_busan',
    'dong_gwangju', 'dongnae', 'eunpyeong', 'gangjin', 'gangneung', 'gangseo',
    'gangseo_busan', 'geumjeong', 'gijang', 'gimje', 'gochang', 'gokseong',
    'gongju', 'goseong_gw', 'gunsan', 'guri', 'guro', 'gurye', 'gwangsan',
    'gyeongsan', 'hadong', 'hampyeong', 'hanam', 'hapcheon', 'hoengseong',
    'hongcheon', 'hwacheon', 'imsil', 'jangheung', 'jangseong', 'jeju',
    'jeongeup', 'jeonju', 'jindo', 'jung_busan', 'jung_daegu', 'jung_incheon',
    'miryang', 'muan', 'muju', 'nam_gwangju', 'namdong', 'namwon', 'namyangju',
    'nonsan', 'pocheon', 'pyeongtaek', 'seo_busan', 'seocho', 'seongdong',
    'seongju', 'seongnam', 'seosan', 'siheung', 'sinan', 'sunchang', 'suyeong',
    'taean', 'taebaek', 'uijeongbu', 'uiryeong', 'ulleung', 'wando', 'wanju',
    'yanggu', 'yangju', 'yeoju', 'yeongcheon', 'yeongdo', 'yeonggwang',
    'yeongwol', 'yeongyang', 'yeonje', 'yesan'
]

# 확인된 작동 URL
WORKING_URLS = {
    'boseong': 'http://www.bscouncil.go.kr/kr/sub04/sub02.php',
    'gangjin': 'https://www.gjcouncil.go.kr/kr/sub04/sub02.php',
    'hadong': 'https://www.hdcl.go.kr/kr/sub04/sub02.php',
    'hapcheon': 'https://www.hccl.go.kr/kr/sub04/sub02.php',
    'muan': 'http://www.muan.or.kr/kr/sub04/sub02.php',
    'wando': 'http://www.wdcc.or.kr/kr/sub04/sub02.php',
    'yanggu': 'http://www.ygcl.go.kr/kr/sub04/sub02.php',
    'gokseong': 'https://www.gokseong.go.kr/council/sub04/sub01.php',
    'seongju': 'https://www.sjcouncil.go.kr/kr/sub04/sub02.php',
    'sunchang': 'https://www.sunchangcouncil.go.kr/kr/sub04/sub02.php',
    'yeongyang': 'https://www.yycouncil.go.kr/kr/sub04/sub02.php',
}

# 의회 메인 페이지 URL
MAIN_URLS = {
    'asan': ['https://council.asan.go.kr'],
    'bonghwa': ['https://council.bonghwa.go.kr', 'http://www.bonghwa.go.kr/open.content/council/'],
    'boryeong': ['https://council.boryeong.go.kr'],
    'boseong': ['http://www.bscouncil.go.kr'],
    'buk_busan': ['https://council.bsbukgu.go.kr'],
    'buk_gwangju': ['https://council.bukgu.gwangju.kr'],
    'buk_ulsan': ['https://council.bukgu.ulsan.kr'],
    'bupyeong': ['https://council.icbp.go.kr'],
    'cheongdo': ['https://council.cheongdo.go.kr'],
    'cheongsong': ['https://council.cs.go.kr', 'http://www.cscouncil.go.kr'],
    'dobong': ['https://council.dobong.go.kr'],
    'dong_busan': ['https://council.bsdonggu.go.kr'],
    'dong_gwangju': ['https://council.donggu.gwangju.kr'],
    'dongnae': ['https://council.dongnae.go.kr'],
    'eunpyeong': ['https://council.ep.go.kr'],
    'gangjin': ['https://www.gjcouncil.go.kr'],
    'gangneung': ['https://council.gn.go.kr', 'https://www.gncl.go.kr'],
    'gangseo': ['https://council.gangseo.seoul.kr'],
    'gangseo_busan': ['https://council.bsgangseo.go.kr'],
    'geumjeong': ['https://council.geumjeong.go.kr'],
    'gijang': ['https://council.gijang.go.kr'],
    'gimje': ['https://council.gimje.go.kr'],
    'gochang': ['https://council.gochang.go.kr'],
    'gokseong': ['https://www.gokseong.go.kr/council/'],
    'gongju': ['https://council.gongju.go.kr'],
    'goseong_gw': ['https://council.gwgs.go.kr'],
    'gunsan': ['https://council.gunsan.go.kr'],
    'guri': ['https://council.guri.go.kr'],
    'guro': ['https://council.guro.go.kr'],
    'gurye': ['https://council.gurye.go.kr'],
    'gwangsan': ['https://council.gwangsan.go.kr'],
    'gyeongsan': ['https://council.gs.go.kr'],
    'hadong': ['https://www.hdcl.go.kr'],
    'hampyeong': ['https://council.hampyeong.go.kr'],
    'hanam': ['https://council.hanam.go.kr'],
    'hapcheon': ['https://www.hccl.go.kr'],
    'hoengseong': ['https://council.hsg.go.kr', 'https://hsg.go.kr/council/'],
    'hongcheon': ['https://council.hongcheon.go.kr'],
    'hwacheon': ['https://council.ihc.go.kr'],
    'imsil': ['https://council.imsil.go.kr'],
    'jangheung': ['https://council.jangheung.go.kr'],
    'jangseong': ['https://council.jangseong.go.kr'],
    'jeju': ['https://record.council.jeju.kr', 'https://council.jeju.kr'],
    'jeongeup': ['https://council.jeongeup.go.kr'],
    'jeonju': ['https://council.jeonju.go.kr'],
    'jindo': ['https://council.jindo.go.kr'],
    'jung_busan': ['https://council.bsjunggu.go.kr'],
    'jung_daegu': ['https://www.junggucouncil.daegu.kr'],
    'jung_incheon': ['https://council.icjg.go.kr'],
    'miryang': ['https://council.miryang.go.kr'],
    'muan': ['http://www.muan.or.kr'],
    'muju': ['https://council.muju.go.kr'],
    'nam_gwangju': ['http://www.gjnc.or.kr', 'https://council.namgu.gwangju.kr'],
    'namdong': ['https://council.namdong.go.kr'],
    'namwon': ['https://council.namwon.go.kr'],
    'namyangju': ['https://www.nyjc.go.kr', 'https://council.nyj.go.kr'],
    'nonsan': ['https://council.nonsan.go.kr'],
    'pocheon': ['https://council.pocheon.go.kr'],
    'pyeongtaek': ['https://council.pyeongtaek.go.kr'],
    'seo_busan': ['https://council.bsseogu.go.kr'],
    'seocho': ['https://council.seocho.go.kr'],
    'seongdong': ['https://council.sd.go.kr', 'https://sdcouncil.sd.go.kr'],
    'seongju': ['https://www.sjcouncil.go.kr'],
    'seongnam': ['https://council.seongnam.go.kr'],
    'seosan': ['https://council.seosan.go.kr'],
    'siheung': ['https://council.siheung.go.kr'],
    'sinan': ['https://council.sinan.go.kr'],
    'sunchang': ['https://www.sunchangcouncil.go.kr'],
    'suyeong': ['https://council.suyeong.go.kr'],
    'taean': ['https://council.taean.go.kr'],
    'taebaek': ['https://council.taebaek.go.kr'],
    'uijeongbu': ['https://council.ui4u.go.kr'],
    'uiryeong': ['https://council.uiryeong.go.kr'],
    'ulleung': ['https://council.ulleung.go.kr'],
    'wando': ['http://www.wdcc.or.kr'],
    'wanju': ['https://council.wanju.go.kr'],
    'yanggu': ['http://www.ygcl.go.kr'],
    'yangju': ['https://council.yangju.go.kr'],
    'yeoju': ['https://council.yeoju.go.kr'],
    'yeongcheon': ['https://council.yc.go.kr'],
    'yeongdo': ['https://council.yeongdo.go.kr'],
    'yeonggwang': ['https://council.yeonggwang.go.kr'],
    'yeongwol': ['https://council.yw.go.kr'],
    'yeongyang': ['https://www.yycouncil.go.kr'],
    'yeonje': ['https://council.yeonje.go.kr'],
    'yesan': ['https://council.yesan.go.kr'],
}

OUTPUT_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes")

async def find_minutes_links(page, base_url: str) -> list:
    """페이지에서 회의록 관련 링크 찾기"""
    links = await page.query_selector_all('a')
    results = []

    for link in links:
        try:
            text = await link.inner_text()
            text = text.strip()

            # 회의록 메뉴 찾기
            if any(kw in text for kw in ['회의록', '의정활동', '본회의', '위원회활동']):
                href = await link.get_attribute('href')
                if href and 'javascript' not in href.lower():
                    if not href.startswith('http'):
                        href = base_url + (href if href.startswith('/') else '/' + href)
                    results.append({'text': text, 'url': href, 'type': 'menu'})
        except:
            continue

    return results

async def find_meeting_items(page, base_url: str) -> list:
    """회의록 목록에서 개별 회의 항목 찾기"""
    items = []

    # 테이블 행에서 찾기
    rows = await page.query_selector_all('table tbody tr')
    for row in rows:
        try:
            link = await row.query_selector('a')
            if link:
                text = await link.inner_text()
                text = text.strip()

                if 5 < len(text) < 150 and re.search(r'(제\d+회|본회의|위원회|정례회|임시회|\d차)', text):
                    href = await link.get_attribute('href')
                    onclick = await link.get_attribute('onclick')

                    if href and 'javascript' not in href.lower():
                        if not href.startswith('http'):
                            href = base_url + (href if href.startswith('/') else '/' + href)
                        items.append({'title': text, 'url': href, 'onclick': None})
                    elif onclick:
                        items.append({'title': text, 'url': None, 'onclick': onclick})
        except:
            continue

    # 일반 링크에서 찾기
    if not items:
        links = await page.query_selector_all('a')
        for link in links:
            try:
                text = await link.inner_text()
                text = text.strip()

                if 5 < len(text) < 150 and re.search(r'(제\d+회|본회의|위원회|정례회|임시회|\d차)', text):
                    href = await link.get_attribute('href')

                    if href and 'javascript' not in href.lower():
                        if not href.startswith('http'):
                            href = base_url + (href if href.startswith('/') else '/' + href)
                        items.append({'title': text, 'url': href, 'onclick': None})
            except:
                continue

    return items

async def extract_content(page) -> str:
    """페이지에서 회의록 본문 추출"""
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

    # body 전체에서 긴 텍스트 추출
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
    main_urls = MAIN_URLS.get(council_code, [])
    if not main_urls:
        return 0

    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        ignore_https_errors=True
    )
    page = await context.new_page()

    records = []

    for main_url in main_urls:
        try:
            base_url = '/'.join(main_url.split('/')[:3])

            # 1. 메인 페이지 접근
            await page.goto(main_url, timeout=15000, wait_until="domcontentloaded")
            await asyncio.sleep(2)

            # 2. 회의록 메뉴 찾기
            menu_links = await find_minutes_links(page, base_url)

            if not menu_links:
                # 직접 회의록 목록이 있는지 확인
                items = await find_meeting_items(page, base_url)
                if items:
                    menu_links = [{'url': main_url, 'type': 'direct'}]

            # 3. 회의록 페이지로 이동하여 목록 추출
            for menu in menu_links[:3]:
                try:
                    if menu.get('url'):
                        await page.goto(menu['url'], timeout=12000, wait_until="domcontentloaded")
                        await asyncio.sleep(1)

                    items = await find_meeting_items(page, base_url)

                    # 4. 상세 페이지에서 전문 추출
                    for item in items[:50]:
                        try:
                            if item.get('url'):
                                await page.goto(item['url'], timeout=10000, wait_until="domcontentloaded")
                            elif item.get('onclick'):
                                await page.evaluate(item['onclick'])
                            else:
                                continue

                            await asyncio.sleep(1)
                            content = await extract_content(page)

                            if content and len(content) > 500:
                                record = {
                                    "council_code": council_code,
                                    "title": item['title'],
                                    "detail_url": item.get('url', main_url),
                                    "meeting_id": "",
                                    "cells": [item['title']],
                                    "crawled_at": datetime.now().isoformat(),
                                    "date": "",
                                    "full_content": content,
                                    "source": "aggressive_crawl"
                                }
                                records.append(record)

                        except:
                            continue

                    if records:
                        break

                except:
                    continue

            if records:
                break

        except Exception as e:
            continue

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
    print("86개 의회 회의록 전문 크롤링 (공격적 접근)")
    print("=" * 60 + "\n")

    start_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end_idx = int(sys.argv[2]) if len(sys.argv) > 2 else len(NO_FULLCONTENT)

    councils = NO_FULLCONTENT[start_idx:end_idx]
    print(f"대상: {len(councils)}개 ({start_idx}~{end_idx-1})\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        results = {}
        for i, code in enumerate(councils):
            print(f"[{start_idx + i + 1}/{end_idx}] {code}", end=" ", flush=True)
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
