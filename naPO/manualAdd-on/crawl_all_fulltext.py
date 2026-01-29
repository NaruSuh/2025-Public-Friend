#!/usr/bin/env python3
"""
86개 의회 회의록 전문 크롤링 - 전체 실행
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

# 의회별 직접 접근 URL
DIRECT_URLS = {
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
    'jeju': 'https://record.council.jeju.kr/minutes/minutesList.do',
    'jeonju': 'https://council.jeonju.go.kr/source/minutes/list.do',
    'seongnam': 'https://council.seongnam.go.kr/source/minute/list.do',
    'pyeongtaek': 'https://council.pyeongtaek.go.kr/source/minute/list.do',
    'namyangju': 'https://www.nyjc.go.kr/board/proceedings.do',
    'gangneung': 'https://www.gncl.go.kr/council/board/proceedings.do',
    'dobong': 'https://council.dobong.go.kr/intra/minute/list.do',
    'gangseo': 'https://council.gangseo.seoul.kr/minute/list.do',
    'seocho': 'https://council.seocho.go.kr/minute/list.do',
    'guro': 'https://council.guro.go.kr/minute/list.do',
    'eunpyeong': 'https://council.ep.go.kr/minute/list.do',
    'seongdong': 'https://council.sd.go.kr/minute/list.do',
}

OUTPUT_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes")

async def extract_detail_content(page) -> str:
    """상세 페이지에서 회의록 전문 추출"""
    content = ""

    try:
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
            'div.bbs_view', 'div.bd_view'
        ]

        for sel in selectors:
            elem = await page.query_selector(sel)
            if elem:
                text = await elem.inner_text()
                if text and len(text) > 500:
                    return text.strip()

        # body 전체
        body = await page.query_selector('body')
        if body:
            text = await body.inner_text()
            lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 30]
            if len(lines) > 30:
                return '\n'.join(lines[:200])

    except:
        pass

    return content

async def crawl_with_direct_url(browser, council_code: str, url: str) -> int:
    """직접 URL로 크롤링"""
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        ignore_https_errors=True
    )
    page = await context.new_page()

    records = []

    try:
        await page.goto(url, timeout=20000, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # 목록에서 링크 추출
        links = await page.query_selector_all('a')
        minute_items = []

        for link in links:
            try:
                text = await link.inner_text()
                text = text.strip()

                if 5 < len(text) < 150 and re.search(r'(제\d+회|본회의|위원회|정례회|임시회|\d차)', text):
                    href = await link.get_attribute('href')
                    onclick = await link.get_attribute('onclick')

                    if href or onclick:
                        minute_items.append({
                            'title': text,
                            'href': href,
                            'onclick': onclick
                        })
            except:
                continue

        # 상세 페이지에서 전문 추출
        base_url = '/'.join(url.split('/')[:3])

        for item in minute_items[:50]:
            try:
                href = item['href']
                onclick = item['onclick']

                if href and 'javascript' not in href.lower() and '#' not in href:
                    if not href.startswith('http'):
                        href = base_url + (href if href.startswith('/') else '/' + href)
                    await page.goto(href, timeout=12000, wait_until="domcontentloaded")
                elif onclick:
                    try:
                        await page.evaluate(onclick)
                    except:
                        continue
                else:
                    continue

                await asyncio.sleep(1)
                full_content = await extract_detail_content(page)

                if full_content and len(full_content) > 500:
                    record = {
                        "council_code": council_code,
                        "title": item['title'],
                        "detail_url": href or url,
                        "meeting_id": "",
                        "cells": [item['title']],
                        "crawled_at": datetime.now().isoformat(),
                        "date": "",
                        "full_content": full_content,
                        "source": "fulltext_direct"
                    }
                    records.append(record)

            except Exception:
                continue

    except Exception:
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

async def crawl_with_search(browser, council_code: str) -> int:
    """검색 패턴으로 크롤링"""
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        ignore_https_errors=True
    )
    page = await context.new_page()

    records = []

    # 도메인 패턴
    domains = [
        f"council.{council_code}.go.kr",
        f"council.{council_code.replace('_', '')}.go.kr",
        f"{council_code}council.go.kr",
    ]

    # 특수 매핑
    domain_map = {
        'buk_busan': 'council.bsbukgu.go.kr',
        'buk_gwangju': 'council.bukgu.gwangju.kr',
        'buk_ulsan': 'council.bukgu.ulsan.kr',
        'dong_busan': 'council.bsdonggu.go.kr',
        'dong_gwangju': 'council.donggu.gwangju.kr',
        'gangseo_busan': 'council.bsgangseo.go.kr',
        'jung_busan': 'council.bsjunggu.go.kr',
        'jung_daegu': 'www.junggucouncil.daegu.kr',
        'jung_incheon': 'council.icjg.go.kr',
        'seo_busan': 'council.bsseogu.go.kr',
        'nam_gwangju': 'council.namgu.gwangju.kr',
        'goseong_gw': 'council.gwgs.go.kr',
        'bupyeong': 'council.icbp.go.kr',
        'gijang': 'council.gijang.go.kr',
        'suyeong': 'council.suyeong.go.kr',
        'cheongsong': 'council.cs.go.kr',
        'gyeongsan': 'council.gs.go.kr',
        'yeongcheon': 'council.yc.go.kr',
        'yeongwol': 'council.yw.go.kr',
    }

    if council_code in domain_map:
        domains.insert(0, domain_map[council_code])

    paths = [
        '/source/minutes/list.do',
        '/source/minute/list.do',
        '/minute/list.do',
        '/minutes/list.do',
        '/board/proceedings.do',
        '/intra/minute/list.do',
    ]

    for domain in domains:
        for path in paths:
            try:
                url = f"https://{domain}{path}"
                await page.goto(url, timeout=10000, wait_until="domcontentloaded")

                content = await page.content()
                if re.search(r'(제\d+회|본회의|회의록)', content):
                    # 목록에서 링크 추출
                    links = await page.query_selector_all('a')
                    minute_items = []

                    for link in links:
                        try:
                            text = await link.inner_text()
                            text = text.strip()

                            if 5 < len(text) < 150 and re.search(r'(제\d+회|본회의|위원회)', text):
                                href = await link.get_attribute('href')
                                if href:
                                    minute_items.append({'title': text, 'href': href})
                        except:
                            continue

                    # 상세 페이지 크롤링
                    base_url = f"https://{domain}"
                    for item in minute_items[:50]:
                        try:
                            href = item['href']
                            if not href.startswith('http'):
                                href = base_url + (href if href.startswith('/') else '/' + href)

                            await page.goto(href, timeout=12000, wait_until="domcontentloaded")
                            await asyncio.sleep(1)

                            full_content = await extract_detail_content(page)

                            if full_content and len(full_content) > 500:
                                record = {
                                    "council_code": council_code,
                                    "title": item['title'],
                                    "detail_url": href,
                                    "meeting_id": "",
                                    "cells": [item['title']],
                                    "crawled_at": datetime.now().isoformat(),
                                    "date": "",
                                    "full_content": full_content,
                                    "source": "fulltext_search"
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

    await context.close()

    if records:
        output_file = OUTPUT_DIR / f"{council_code}.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        return len(records)

    return 0

async def crawl_council(browser, council_code: str) -> int:
    """의회 크롤링"""
    # 1. 직접 URL 시도
    if council_code in DIRECT_URLS:
        count = await crawl_with_direct_url(browser, council_code, DIRECT_URLS[council_code])
        if count > 0:
            return count

    # 2. 검색 패턴으로 시도
    count = await crawl_with_search(browser, council_code)
    return count

async def main():
    print("=" * 60)
    print("86개 의회 회의록 전문 크롤링")
    print("=" * 60 + "\n")

    # 인자로 시작 인덱스 받기
    start_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end_idx = int(sys.argv[2]) if len(sys.argv) > 2 else len(NO_FULLCONTENT)

    councils_to_crawl = NO_FULLCONTENT[start_idx:end_idx]
    print(f"크롤링 대상: {start_idx}~{end_idx-1} ({len(councils_to_crawl)}개)\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        results = {}
        for i, council_code in enumerate(councils_to_crawl):
            print(f"[{start_idx + i + 1}/{end_idx}] {council_code}", end=" ", flush=True)
            try:
                count = await crawl_council(browser, council_code)
                results[council_code] = count
                if count > 0:
                    print(f"✅ {count}건")
                else:
                    print("❌")
            except Exception as e:
                print(f"오류: {str(e)[:30]}")
                results[council_code] = 0

            await asyncio.sleep(0.5)

        await browser.close()

    print("\n" + "=" * 60)
    success = sum(1 for v in results.values() if v > 0)
    total_records = sum(results.values())
    print(f"성공: {success}/{len(councils_to_crawl)} | 총 {total_records}건")

if __name__ == "__main__":
    asyncio.run(main())
