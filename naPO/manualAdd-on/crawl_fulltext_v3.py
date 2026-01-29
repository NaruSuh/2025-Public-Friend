#!/usr/bin/env python3
"""
86개 의회 회의록 전문 크롤링 v3
- 전자회의록 시스템 iframe 직접 추출
- 더 공격적인 콘텐츠 추출
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

# 전자회의록 시스템 URL 패턴
COUNCIL_URLS = {
    'asan': 'https://council.asan.go.kr/source/minutes/list.do',
    'bonghwa': 'https://council.bonghwa.go.kr/contents.do?key=1114',
    'boryeong': 'https://council.boryeong.go.kr/council/minute/list',
    'boseong': 'http://www.bscouncil.go.kr/kr/sub04/sub02.php',
    'buk_busan': 'https://council.bsbukgu.go.kr/minutes/list',
    'buk_gwangju': 'https://council.bukgu.gwangju.kr/board/list.php?bdId=minutes',
    'buk_ulsan': 'https://council.bukgu.ulsan.kr/02_activity/activity_01.asp',
    'bupyeong': 'https://council.icbp.go.kr/open_content/main_page/minutes/minutes.do',
    'cheongdo': 'https://council.cheongdo.go.kr/sub.php?menukey=95',
    'cheongsong': 'https://www.cscouncil.go.kr/source/minutes/list.do',
    'dobong': 'https://council.dobong.go.kr/minutes/list',
    'dong_busan': 'https://council.bsdonggu.go.kr/minutes/list',
    'dong_gwangju': 'https://council.donggu.gwangju.kr/board/list.php?bdId=minutes',
    'dongnae': 'https://council.dongnae.go.kr/minutes/list',
    'eunpyeong': 'https://council.ep.go.kr/minutes/list',
    'gangjin': 'https://www.gjcouncil.go.kr/kr/sub04/sub02.php',
    'gangneung': 'https://council.gn.go.kr/source/minutes/list.do',
    'gangseo': 'https://council.gangseo.seoul.kr/minutes/list',
    'gangseo_busan': 'https://council.bsgangseo.go.kr/minutes/list',
    'geumjeong': 'https://council.geumjeong.go.kr/minutes/list',
    'gijang': 'https://council.gijang.go.kr/minutes/list',
    'gimje': 'https://council.gimje.go.kr/source/minutes/list.do',
    'gochang': 'https://council.gochang.go.kr/source/minutes/list.do',
    'gokseong': 'https://www.gokseong.go.kr/council/sub04/sub01.php',
    'gongju': 'https://council.gongju.go.kr/source/minutes/list.do',
    'goseong_gw': 'https://council.gwgs.go.kr/source/minutes/list.do',
    'gunsan': 'https://council.gunsan.go.kr/source/minutes/list.do',
    'guri': 'https://council.guri.go.kr/source/minutes/list.do',
    'guro': 'https://council.guro.go.kr/minutes/list',
    'gurye': 'https://council.gurye.go.kr/source/minutes/list.do',
    'gwangsan': 'https://council.gwangsan.go.kr/board/list.php?bdId=minutes',
    'gyeongsan': 'https://council.gs.go.kr/source/minutes/list.do',
    'hadong': 'https://www.hdcl.go.kr/kr/sub04/sub02.php',
    'hampyeong': 'https://council.hampyeong.go.kr/source/minutes/list.do',
    'hanam': 'https://council.hanam.go.kr/source/minutes/list.do',
    'hapcheon': 'https://www.hccl.go.kr/kr/sub04/sub02.php',
    'hoengseong': 'https://council.hsg.go.kr/source/minutes/list.do',
    'hongcheon': 'https://council.hongcheon.go.kr/source/minutes/list.do',
    'hwacheon': 'https://council.ihc.go.kr/source/minutes/list.do',
    'imsil': 'https://council.imsil.go.kr/source/minutes/list.do',
    'jangheung': 'https://council.jangheung.go.kr/source/minutes/list.do',
    'jangseong': 'https://council.jangseong.go.kr/source/minutes/list.do',
    'jeju': 'https://record.council.jeju.kr/minutes/list',
    'jeongeup': 'https://council.jeongeup.go.kr/source/minutes/list.do',
    'jeonju': 'https://council.jeonju.go.kr/source/minutes/list.do',
    'jindo': 'https://council.jindo.go.kr/source/minutes/list.do',
    'jung_busan': 'https://council.bsjunggu.go.kr/minutes/list',
    'jung_daegu': 'https://www.junggucouncil.daegu.kr/contents.do?key=1114',
    'jung_incheon': 'https://council.icjg.go.kr/minutes/list',
    'miryang': 'https://council.miryang.go.kr/source/minutes/list.do',
    'muan': 'http://www.muan.or.kr/kr/sub04/sub02.php',
    'muju': 'https://council.muju.go.kr/source/minutes/list.do',
    'nam_gwangju': 'https://council.namgu.gwangju.kr/board/list.php?bdId=minutes',
    'namdong': 'https://council.namdong.go.kr/minutes/list',
    'namwon': 'https://council.namwon.go.kr/source/minutes/list.do',
    'namyangju': 'https://council.nyj.go.kr/source/minutes/list.do',
    'nonsan': 'https://council.nonsan.go.kr/source/minutes/list.do',
    'pocheon': 'https://council.pocheon.go.kr/source/minutes/list.do',
    'pyeongtaek': 'https://council.pyeongtaek.go.kr/source/minutes/list.do',
    'seo_busan': 'https://council.bsseogu.go.kr/minutes/list',
    'seocho': 'https://council.seocho.go.kr/minutes/list',
    'seongdong': 'https://council.sd.go.kr/minutes/list',
    'seongju': 'https://www.sjcouncil.go.kr/source/minutes/list.do',
    'seongnam': 'https://council.seongnam.go.kr/source/minutes/list.do',
    'seosan': 'https://council.seosan.go.kr/source/minutes/list.do',
    'siheung': 'https://council.siheung.go.kr/source/minutes/list.do',
    'sinan': 'https://council.sinan.go.kr/source/minutes/list.do',
    'sunchang': 'https://www.sunchangcouncil.go.kr/source/minutes/list.do',
    'suyeong': 'https://council.suyeong.go.kr/minutes/list',
    'taean': 'https://council.taean.go.kr/source/minutes/list.do',
    'taebaek': 'https://council.taebaek.go.kr/source/minutes/list.do',
    'uijeongbu': 'https://council.ui4u.go.kr/source/minutes/list.do',
    'uiryeong': 'https://council.uiryeong.go.kr/source/minutes/list.do',
    'ulleung': 'https://council.ulleung.go.kr/source/minutes/list.do',
    'wando': 'http://www.wdcc.or.kr/kr/sub04/sub02.php',
    'wanju': 'https://council.wanju.go.kr/source/minutes/list.do',
    'yanggu': 'http://www.ygcl.go.kr/kr/sub04/sub02.php',
    'yangju': 'https://council.yangju.go.kr/source/minutes/list.do',
    'yeoju': 'https://council.yeoju.go.kr/source/minutes/list.do',
    'yeongcheon': 'https://council.yc.go.kr/source/minutes/list.do',
    'yeongdo': 'https://council.yeongdo.go.kr/minutes/list',
    'yeonggwang': 'https://council.yeonggwang.go.kr/source/minutes/list.do',
    'yeongwol': 'https://council.yw.go.kr/source/minutes/list.do',
    'yeongyang': 'https://www.yycouncil.go.kr/source/minutes/list.do',
    'yeonje': 'https://council.yeonje.go.kr/minutes/list',
    'yesan': 'https://council.yesan.go.kr/source/minutes/list.do',
}

OUTPUT_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes")

async def extract_fulltext(page, timeout=10000) -> str:
    """페이지에서 회의록 전문 추출"""
    content = ""

    try:
        # 1. iframe 확인
        frames = page.frames
        for frame in frames:
            if frame != page.main_frame:
                try:
                    body = await frame.query_selector('body')
                    if body:
                        text = await body.inner_text()
                        if text and len(text) > 500:
                            content = text.strip()
                            if len(content) > 1000:
                                return content
                except:
                    pass

        # 2. 본문 영역 선택자
        selectors = [
            'div.minutes_view', 'div.view_content', 'div.content_view',
            'div.board_view', 'div#contentArea', 'pre.minutes_text',
            'div.detail_view', 'article.view', 'div.con_wrap',
            'table.view_table td', 'div.minutes_content'
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

        # 3. body 전체에서 추출
        body = await page.query_selector('body')
        if body:
            text = await body.inner_text()
            lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 30]
            if len(lines) > 20:
                return '\n'.join(lines[:300])

    except Exception as e:
        pass

    return content

async def crawl_council(browser, council_code: str) -> int:
    """단일 의회 크롤링"""
    url = COUNCIL_URLS.get(council_code)
    if not url:
        return 0

    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        ignore_https_errors=True
    )
    page = await context.new_page()

    records = []

    try:
        await page.goto(url, timeout=20000, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # 목록에서 링크 수집
        links = await page.query_selector_all('a')
        minute_links = []

        for link in links:
            try:
                text = await link.inner_text()
                text = text.strip()

                # 회의록 패턴
                if re.search(r'(제\d+회|본회의|위원회|정례회|임시회|\d차|회의록)', text):
                    if 5 < len(text) < 150:
                        href = await link.get_attribute('href')
                        onclick = await link.get_attribute('onclick')

                        if href and 'javascript' not in href.lower():
                            if not href.startswith('http'):
                                base = '/'.join(url.split('/')[:3])
                                href = base + (href if href.startswith('/') else '/' + href)
                            minute_links.append((text, href, None))
                        elif onclick:
                            minute_links.append((text, url, onclick))
            except:
                continue

        # 상세 페이지에서 전문 추출
        for title, href, onclick in minute_links[:50]:
            try:
                if onclick:
                    # onclick 실행
                    await page.evaluate(f'() => {{ {onclick} }}')
                    await asyncio.sleep(2)
                else:
                    await page.goto(href, timeout=15000, wait_until="domcontentloaded")
                    await asyncio.sleep(1)

                full_content = await extract_fulltext(page)

                if full_content and len(full_content) > 500:
                    record = {
                        "council_code": council_code,
                        "title": title,
                        "detail_url": href,
                        "meeting_id": "",
                        "cells": [title],
                        "crawled_at": datetime.now().isoformat(),
                        "date": "",
                        "full_content": full_content,
                        "source": "fulltext_v3"
                    }
                    records.append(record)

                    if len(records) >= 50:
                        break

            except Exception:
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
    print("86개 의회 회의록 전문 크롤링 v3")
    print("=" * 60 + "\n")

    # 처음 10개 테스트
    test_councils = NO_FULLCONTENT[:10]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        results = {}
        for council_code in test_councils:
            print(f"크롤링: {council_code}", end=" ")
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
