#!/usr/bin/env python3
"""
88개 의회 회의록 전문 크롤링
- 각 의회 사이트의 회의록 시스템에서 직접 크롤링
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
from pathlib import Path
import re

# 88개 의회 목록
COUNCILS = [
    'asan', 'bonghwa', 'boryeong', 'boseong', 'buan', 'buk_busan', 'buk_gwangju',
    'buk_ulsan', 'busanjin', 'cheongdo', 'cheongsong', 'cheorwon', 'chilgok',
    'damyang', 'dobong', 'dong_busan', 'dong_gwangju', 'dongnae', 'gangjin',
    'gangneung', 'gangseo', 'gangseo_busan', 'geumjeong', 'gimje', 'gochang',
    'goheung', 'gokseong', 'gongju', 'goseong_gw', 'gunsan', 'guri', 'guro',
    'gurye', 'gwangsan', 'gyeongsan', 'hadong', 'hampyeong', 'hanam', 'hapcheon',
    'hoengseong', 'hongcheon', 'hwacheon', 'imsil', 'jangheung', 'jangseong',
    'jeju', 'jeongeup', 'jeonju', 'jindo', 'jung_busan', 'jung_daegu',
    'jung_incheon', 'miryang', 'muan', 'muju', 'nam_gwangju', 'namdong',
    'namwon', 'namyangju', 'nonsan', 'pocheon', 'pyeongtaek', 'seo_busan',
    'seocho', 'seongdong', 'seongju', 'seongnam', 'seosan', 'siheung', 'sinan',
    'sunchang', 'taean', 'taebaek', 'uijeongbu', 'uiryeong', 'ulleung', 'wando',
    'wanju', 'yanggu', 'yangju', 'yeoju', 'yeongcheon', 'yeongdo', 'yeonggwang',
    'yeongwol', 'yeongyang', 'yeonje', 'yesan'
]

# 의회별 회의록 시스템 URL
COUNCIL_URLS = {
    'asan': 'https://council.asan.go.kr/assm/minute/list.do',
    'bonghwa': 'https://www.bonghwa.go.kr/open.content/council/proceedings/congressional.record/',
    'boryeong': 'https://council.boryeong.go.kr/assm/minute/list.do',
    'boseong': 'https://www.bscouncil.go.kr/main/menu/minute',
    'buan': 'https://council.buan.go.kr/assm/minute/list.do',
    'buk_busan': 'https://council.bsbukgu.go.kr/assm/minute/list.do',
    'buk_gwangju': 'https://council.bukgu.gwangju.kr/assm/minute/list.do',
    'buk_ulsan': 'https://council.bukgu.ulsan.kr/assm/minute/list.do',
    'busanjin': 'https://council.busanjin.go.kr/assm/minute/list.do',
    'cheongdo': 'https://council.cheongdo.go.kr/assm/minute/list.do',
    'cheongsong': 'https://www.cscouncil.go.kr/main/menu/minute',
    'cheorwon': 'https://council.cwg.go.kr/assm/minute/list.do',
    'chilgok': 'https://council.chilgok.go.kr/assm/minute/list.do',
    'damyang': 'http://dycouncil.go.kr/korean/meeting/minute.htm',
    'dobong': 'https://council.dobong.go.kr/assm/minute/list.do',
    'dong_busan': 'https://council.bsdonggu.go.kr/assm/minute/list.do',
    'dong_gwangju': 'https://council.donggu.gwangju.kr/assm/minute/list.do',
    'dongnae': 'https://council.dongnae.go.kr/assm/minute/list.do',
    'gangjin': 'https://www.gjcouncil.go.kr/main/menu/minute',
    'gangneung': 'https://council.gn.go.kr/assm/minute/list.do',
    'gangseo': 'https://council.gangseo.seoul.kr/assm/minute/list.do',
    'gangseo_busan': 'https://council.bsgangseo.go.kr/assm/minute/list.do',
    'geumjeong': 'https://council.geumjeong.go.kr/assm/minute/list.do',
    'gimje': 'https://council.gimje.go.kr/assm/minute/list.do',
    'gochang': 'https://council.gochang.go.kr/assm/minute/list.do',
    'goheung': 'https://council.goheung.go.kr/assm/minute/list.do',
    'gokseong': 'https://www.gokseong.go.kr/council/assm/minute/list.do',
    'gongju': 'https://council.gongju.go.kr/assm/minute/list.do',
    'goseong_gw': 'https://council.gwgs.go.kr/assm/minute/list.do',
    'gunsan': 'https://council.gunsan.go.kr/assm/minute/list.do',
    'guri': 'https://council.guri.go.kr/assm/minute/list.do',
    'guro': 'https://council.guro.go.kr/assm/minute/list.do',
    'gurye': 'https://council.gurye.go.kr/assm/minute/list.do',
    'gwangsan': 'https://council.gwangsan.go.kr/assm/minute/list.do',
    'gyeongsan': 'https://council.gs.go.kr/assm/minute/list.do',
    'hadong': 'https://www.hdcl.go.kr/source/korean/meeting/minute.jsp',
    'hampyeong': 'https://council.hampyeong.go.kr/assm/minute/list.do',
    'hanam': 'https://council.hanam.go.kr/assm/minute/list.do',
    'hapcheon': 'https://www.hccl.go.kr/source/korean/meeting/minute.jsp',
    'hoengseong': 'https://hsg.go.kr/council/assm/minute/list.do',
    'hongcheon': 'https://council.hongcheon.go.kr/assm/minute/list.do',
    'hwacheon': 'https://council.ihc.go.kr/assm/minute/list.do',
    'imsil': 'https://council.imsil.go.kr/assm/minute/list.do',
    'jangheung': 'https://council.jangheung.go.kr/assm/minute/list.do',
    'jangseong': 'https://council.jangseong.go.kr/assm/minute/list.do',
    'jeju': 'https://record.council.jeju.kr/CLRecords/Retrieval2/index.php',
    'jeongeup': 'https://council.jeongeup.go.kr/assm/minute/list.do',
    'jeonju': 'https://council.jeonju.go.kr/assm/minute/list.do',
    'jindo': 'https://council.jindo.go.kr/assm/minute/list.do',
    'jung_busan': 'https://council.bsjunggu.go.kr/assm/minute/list.do',
    'jung_daegu': 'https://www.junggucouncil.daegu.kr/assm/minute/list.do',
    'jung_incheon': 'https://council.icjg.go.kr/assm/minute/list.do',
    'miryang': 'https://council.miryang.go.kr/assm/minute/list.do',
    'muan': 'http://www.muan.or.kr/korean/meeting/minute.htm',
    'muju': 'https://council.muju.go.kr/assm/minute/list.do',
    'nam_gwangju': 'http://www.gjnc.or.kr/korean/meeting/minute.htm',
    'namdong': 'https://council.namdong.go.kr/assm/minute/list.do',
    'namwon': 'https://council.namwon.go.kr/assm/minute/list.do',
    'namyangju': 'https://council.nyj.go.kr/assm/minute/list.do',
    'nonsan': 'https://council.nonsan.go.kr/assm/minute/list.do',
    'pocheon': 'https://council.pocheon.go.kr/assm/minute/list.do',
    'pyeongtaek': 'https://council.pyeongtaek.go.kr/assm/minute/list.do',
    'seo_busan': 'https://council.bsseogu.go.kr/assm/minute/list.do',
    'seocho': 'https://council.seocho.go.kr/assm/minute/list.do',
    'seongdong': 'https://council.sd.go.kr/assm/minute/list.do',
    'seongju': 'https://www.sjcouncil.go.kr/content/minutes/mntsList.html',
    'seongnam': 'https://council.seongnam.go.kr/assm/minute/list.do',
    'seosan': 'https://council.seosan.go.kr/assm/minute/list.do',
    'siheung': 'https://council.siheung.go.kr/assm/minute/list.do',
    'sinan': 'https://council.sinan.go.kr/assm/minute/list.do',
    'sunchang': 'https://www.sunchangcouncil.go.kr/assm/minute/list.do',
    'taean': 'https://council.taean.go.kr/assm/minute/list.do',
    'taebaek': 'https://council.taebaek.go.kr/assm/minute/list.do',
    'uijeongbu': 'https://council.ui4u.go.kr/assm/minute/list.do',
    'uiryeong': 'https://council.uiryeong.go.kr/assm/minute/list.do',
    'ulleung': 'https://council.ulleung.go.kr/assm/minute/list.do',
    'wando': 'http://www.wdcc.or.kr:8088/minute/list.do',
    'wanju': 'https://council.wanju.go.kr/assm/minute/list.do',
    'yanggu': 'http://www.ygcl.go.kr/portal/F30000/F30100/boardList',
    'yangju': 'https://council.yangju.go.kr/assm/minute/list.do',
    'yeoju': 'https://council.yeoju.go.kr/assm/minute/list.do',
    'yeongcheon': 'https://council.yc.go.kr/assm/minute/list.do',
    'yeongdo': 'https://council.yeongdo.go.kr/assm/minute/list.do',
    'yeonggwang': 'https://council.yeonggwang.go.kr/assm/minute/list.do',
    'yeongwol': 'https://council.yw.go.kr/assm/minute/list.do',
    'yeongyang': 'https://councilbroadcast.yyg.go.kr/',
    'yeonje': 'https://council.yeonje.go.kr/assm/minute/list.do',
    'yesan': 'https://council.yesan.go.kr/assm/minute/list.do',
}

OUTPUT_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes")

async def extract_minute_content(page) -> str:
    """페이지에서 회의록 본문 추출"""
    try:
        # 다양한 선택자 시도
        selectors = [
            'div.minutes_content',
            'div.view_content',
            'div.content_view',
            'div.board_view',
            'div.detail_content',
            'div#contentArea',
            'div.con_wrap',
            'pre',
            'article',
            'div.content',
        ]

        for selector in selectors:
            elem = await page.query_selector(selector)
            if elem:
                text = await elem.inner_text()
                if text and len(text) > 200:
                    return text.strip()

        # iframe 내 콘텐츠 확인
        frames = page.frames
        for frame in frames:
            if frame != page.main_frame:
                try:
                    body = await frame.query_selector('body')
                    if body:
                        text = await body.inner_text()
                        if text and len(text) > 200:
                            return text.strip()
                except:
                    pass

    except Exception as e:
        pass

    return ""

async def crawl_assm_minutes(page, council_code: str, base_url: str) -> list:
    """assm/minute 시스템 크롤링"""
    records = []

    try:
        await page.goto(base_url, timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # 목록 페이지에서 링크 추출
        rows = await page.query_selector_all('table tbody tr')
        if not rows:
            rows = await page.query_selector_all('div.list_wrap li')
        if not rows:
            rows = await page.query_selector_all('ul.board_list li')

        links_data = []
        for row in rows[:60]:
            try:
                link = await row.query_selector('a')
                if not link:
                    continue

                title = await link.inner_text()
                title = title.strip()

                if not title or len(title) < 3:
                    continue

                href = await link.get_attribute('href')
                if href:
                    if not href.startswith('http'):
                        base = '/'.join(base_url.split('/')[:3])
                        href = base + href if href.startswith('/') else base_url.rsplit('/', 1)[0] + '/' + href

                    # onclick에서 URL 추출
                    onclick = await link.get_attribute('onclick')
                    if onclick and 'view' in onclick.lower():
                        match = re.search(r"'([^']+)'", onclick)
                        if match:
                            href = match.group(1)
                            if not href.startswith('http'):
                                base = '/'.join(base_url.split('/')[:3])
                                href = base + href

                    links_data.append((title, href))

            except Exception:
                continue

        # 각 링크에서 전문 추출
        count = 0
        for title, href in links_data[:50]:
            try:
                await page.goto(href, timeout=20000, wait_until="domcontentloaded")
                await asyncio.sleep(1)

                full_content = await extract_minute_content(page)

                record = {
                    "council_code": council_code,
                    "title": title,
                    "detail_url": href,
                    "meeting_id": "",
                    "cells": [title],
                    "crawled_at": datetime.now().isoformat(),
                    "date": "",
                    "full_content": full_content,
                    "source": "assm_fulltext"
                }
                records.append(record)
                count += 1

                if count >= 50:
                    break

            except Exception:
                continue

    except Exception as e:
        print(f"    오류: {str(e)[:50]}")

    return records

async def crawl_council(browser, council_code: str) -> int:
    """단일 의회 크롤링"""
    print(f"크롤링: {council_code}", end=" ")

    url = COUNCIL_URLS.get(council_code)
    if not url:
        print("- URL 없음")
        return 0

    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        ignore_https_errors=True
    )
    page = await context.new_page()

    records = await crawl_assm_minutes(page, council_code, url)
    await context.close()

    # 저장
    if records:
        # full_content 있는 것 필터링
        valid = [r for r in records if r.get('full_content') and len(r['full_content']) > 100]

        if valid:
            output_file = OUTPUT_DIR / f"{council_code}.jsonl"
            with open(output_file, 'w', encoding='utf-8') as f:
                for r in valid:
                    f.write(json.dumps(r, ensure_ascii=False) + '\n')
            print(f"✅ {len(valid)}건")
            return len(valid)
        else:
            print(f"⚠️  전문 없음 ({len(records)}건)")
            return 0
    else:
        print("❌ 실패")
        return 0

async def main():
    print("=" * 60)
    print("88개 의회 회의록 전문 크롤링")
    print("=" * 60 + "\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        results = {}
        for council_code in COUNCILS:
            try:
                count = await crawl_council(browser, council_code)
                results[council_code] = count
            except Exception as e:
                print(f"{council_code} 예외: {e}")
                results[council_code] = 0

            await asyncio.sleep(1)

        await browser.close()

    # 결과 요약
    print("\n" + "=" * 60)
    success = sum(1 for v in results.values() if v >= 10)
    partial = sum(1 for v in results.values() if 0 < v < 10)
    failed = sum(1 for v in results.values() if v == 0)
    total_records = sum(results.values())

    print(f"성공: {success}개 | 부분: {partial}개 | 실패: {failed}개")
    print(f"총 레코드: {total_records}건")

if __name__ == "__main__":
    asyncio.run(main())
