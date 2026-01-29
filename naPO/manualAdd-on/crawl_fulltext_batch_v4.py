#!/usr/bin/env python3
"""
86개 의회 회의록 전문 크롤링 v4
- 각 의회 사이트에서 회의록 상세 페이지 직접 접근
- PDF/HWP 다운로드 링크 있으면 메타데이터 포함
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
from pathlib import Path
import re

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

# 의회 도메인 패턴
COUNCIL_DOMAINS = {
    'asan': 'council.asan.go.kr',
    'bonghwa': 'council.bonghwa.go.kr',
    'boryeong': 'council.boryeong.go.kr',
    'boseong': 'bscouncil.go.kr',
    'buk_busan': 'council.bsbukgu.go.kr',
    'buk_gwangju': 'council.bukgu.gwangju.kr',
    'buk_ulsan': 'council.bukgu.ulsan.kr',
    'bupyeong': 'council.icbp.go.kr',
    'cheongdo': 'council.cheongdo.go.kr',
    'cheongsong': 'council.cs.go.kr',
    'dobong': 'council.dobong.go.kr',
    'dong_busan': 'council.bsdonggu.go.kr',
    'dong_gwangju': 'council.donggu.gwangju.kr',
    'dongnae': 'council.dongnae.go.kr',
    'eunpyeong': 'council.ep.go.kr',
    'gangjin': 'gjcouncil.go.kr',
    'gangneung': 'council.gn.go.kr',
    'gangseo': 'council.gangseo.seoul.kr',
    'gangseo_busan': 'council.bsgangseo.go.kr',
    'geumjeong': 'council.geumjeong.go.kr',
    'gijang': 'council.gijang.go.kr',
    'gimje': 'council.gimje.go.kr',
    'gochang': 'council.gochang.go.kr',
    'gokseong': 'gokseong.go.kr',
    'gongju': 'council.gongju.go.kr',
    'goseong_gw': 'council.gwgs.go.kr',
    'gunsan': 'council.gunsan.go.kr',
    'guri': 'council.guri.go.kr',
    'guro': 'council.guro.go.kr',
    'gurye': 'council.gurye.go.kr',
    'gwangsan': 'council.gwangsan.go.kr',
    'gyeongsan': 'council.gs.go.kr',
    'hadong': 'hdcl.go.kr',
    'hampyeong': 'council.hampyeong.go.kr',
    'hanam': 'council.hanam.go.kr',
    'hapcheon': 'hccl.go.kr',
    'hoengseong': 'council.hsg.go.kr',
    'hongcheon': 'council.hongcheon.go.kr',
    'hwacheon': 'council.ihc.go.kr',
    'imsil': 'council.imsil.go.kr',
    'jangheung': 'council.jangheung.go.kr',
    'jangseong': 'council.jangseong.go.kr',
    'jeju': 'council.jeju.kr',
    'jeongeup': 'council.jeongeup.go.kr',
    'jeonju': 'council.jeonju.go.kr',
    'jindo': 'council.jindo.go.kr',
    'jung_busan': 'council.bsjunggu.go.kr',
    'jung_daegu': 'junggucouncil.daegu.kr',
    'jung_incheon': 'council.icjg.go.kr',
    'miryang': 'council.miryang.go.kr',
    'muan': 'muan.or.kr',
    'muju': 'council.muju.go.kr',
    'nam_gwangju': 'council.namgu.gwangju.kr',
    'namdong': 'council.namdong.go.kr',
    'namwon': 'council.namwon.go.kr',
    'namyangju': 'council.nyj.go.kr',
    'nonsan': 'council.nonsan.go.kr',
    'pocheon': 'council.pocheon.go.kr',
    'pyeongtaek': 'council.pyeongtaek.go.kr',
    'seo_busan': 'council.bsseogu.go.kr',
    'seocho': 'council.seocho.go.kr',
    'seongdong': 'council.sd.go.kr',
    'seongju': 'sjcouncil.go.kr',
    'seongnam': 'council.seongnam.go.kr',
    'seosan': 'council.seosan.go.kr',
    'siheung': 'council.siheung.go.kr',
    'sinan': 'council.sinan.go.kr',
    'sunchang': 'sunchangcouncil.go.kr',
    'suyeong': 'council.suyeong.go.kr',
    'taean': 'council.taean.go.kr',
    'taebaek': 'council.taebaek.go.kr',
    'uijeongbu': 'council.ui4u.go.kr',
    'uiryeong': 'council.uiryeong.go.kr',
    'ulleung': 'council.ulleung.go.kr',
    'wando': 'wdcc.or.kr',
    'wanju': 'council.wanju.go.kr',
    'yanggu': 'ygcl.go.kr',
    'yangju': 'council.yangju.go.kr',
    'yeoju': 'council.yeoju.go.kr',
    'yeongcheon': 'council.yc.go.kr',
    'yeongdo': 'council.yeongdo.go.kr',
    'yeonggwang': 'council.yeonggwang.go.kr',
    'yeongwol': 'council.yw.go.kr',
    'yeongyang': 'yycouncil.go.kr',
    'yeonje': 'council.yeonje.go.kr',
    'yesan': 'council.yesan.go.kr',
}

OUTPUT_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes")

async def find_minutes_page(page, domain: str) -> str:
    """회의록 목록 페이지 URL 찾기"""
    base_urls = [
        f"https://{domain}",
        f"https://www.{domain}",
        f"http://{domain}",
    ]

    # 회의록 관련 경로
    paths = [
        '/source/minutes/list.do',
        '/minutes/list',
        '/board/minutes',
        '/contents.do?key=1114',
        '/sub04/sub02.php',
        '/kr/sub04/sub02.php',
        '/open_content/main_page/minutes/minutes.do',
        '/council/minute/list',
        '/activity/minute',
        '/proceedings',
    ]

    for base in base_urls:
        for path in paths:
            try:
                url = base + path
                await page.goto(url, timeout=10000, wait_until="domcontentloaded")

                # 회의록 관련 콘텐츠가 있는지 확인
                content = await page.content()
                if re.search(r'(제\d+회|본회의|회의록|위원회)', content):
                    return url
            except:
                continue

        # 메인 페이지에서 회의록 링크 찾기
        try:
            await page.goto(base, timeout=10000, wait_until="domcontentloaded")
            links = await page.query_selector_all('a')

            for link in links:
                try:
                    text = await link.inner_text()
                    if '회의록' in text or '의정활동' in text:
                        href = await link.get_attribute('href')
                        if href and not href.startswith('javascript'):
                            if not href.startswith('http'):
                                href = base + (href if href.startswith('/') else '/' + href)
                            return href
                except:
                    continue
        except:
            continue

    return ""

async def extract_minutes_list(page) -> list:
    """현재 페이지에서 회의록 목록 추출"""
    items = []

    # 테이블 행 또는 리스트 아이템에서 추출
    selectors = [
        'table tbody tr',
        'ul.list li',
        'div.board_list li',
        'div.list_wrap div.item',
    ]

    for sel in selectors:
        rows = await page.query_selector_all(sel)
        if rows:
            for row in rows[:60]:
                try:
                    link = await row.query_selector('a')
                    if not link:
                        continue

                    title = await link.inner_text()
                    title = title.strip()

                    if len(title) < 5:
                        continue

                    # 회의록 패턴 확인
                    if not re.search(r'(제\d+회|본회의|위원회|정례회|임시회|\d차|회의록)', title):
                        continue

                    href = await link.get_attribute('href')
                    onclick = await link.get_attribute('onclick')

                    items.append({
                        'title': title,
                        'href': href,
                        'onclick': onclick
                    })
                except:
                    continue

            if items:
                break

    # 일반 링크에서도 추출
    if not items:
        links = await page.query_selector_all('a')
        for link in links:
            try:
                title = await link.inner_text()
                title = title.strip()

                if 5 < len(title) < 150 and re.search(r'(제\d+회|본회의|위원회)', title):
                    href = await link.get_attribute('href')
                    onclick = await link.get_attribute('onclick')
                    items.append({'title': title, 'href': href, 'onclick': onclick})
            except:
                continue

    return items

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
            'div#contentArea', 'div.con_wrap', 'table.view_table'
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

async def crawl_council(browser, council_code: str) -> int:
    """단일 의회 크롤링"""
    domain = COUNCIL_DOMAINS.get(council_code)
    if not domain:
        return 0

    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        ignore_https_errors=True
    )
    page = await context.new_page()

    records = []

    try:
        # 1. 회의록 페이지 찾기
        minutes_url = await find_minutes_page(page, domain)
        if not minutes_url:
            await context.close()
            return 0

        # 2. 목록 추출
        await page.goto(minutes_url, timeout=15000, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        items = await extract_minutes_list(page)

        # 3. 상세 페이지에서 전문 추출
        base_url = '/'.join(minutes_url.split('/')[:3])

        for item in items[:50]:
            try:
                href = item['href']
                onclick = item['onclick']

                if href and 'javascript' not in href.lower():
                    if not href.startswith('http'):
                        href = base_url + (href if href.startswith('/') else '/' + href)
                    await page.goto(href, timeout=12000, wait_until="domcontentloaded")
                elif onclick:
                    await page.evaluate(onclick)
                else:
                    continue

                await asyncio.sleep(1)
                full_content = await extract_detail_content(page)

                if full_content and len(full_content) > 500:
                    record = {
                        "council_code": council_code,
                        "title": item['title'],
                        "detail_url": href or minutes_url,
                        "meeting_id": "",
                        "cells": [item['title']],
                        "crawled_at": datetime.now().isoformat(),
                        "date": "",
                        "full_content": full_content,
                        "source": "fulltext_v4"
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

async def main():
    print("=" * 60)
    print("86개 의회 회의록 전문 크롤링 v4")
    print("=" * 60 + "\n")

    # 5개씩 테스트
    test_councils = NO_FULLCONTENT[:5]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        results = {}
        for council_code in test_councils:
            print(f"크롤링: {council_code}", end=" ", flush=True)
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

            await asyncio.sleep(1)

        await browser.close()

    print("\n" + "=" * 60)
    success = sum(1 for v in results.values() if v > 0)
    print(f"성공: {success}/{len(test_councils)}")

if __name__ == "__main__":
    asyncio.run(main())
