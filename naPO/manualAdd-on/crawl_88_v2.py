#!/usr/bin/env python3
"""
88개 의회 회의록 전문 크롤링 v2
- 다양한 전자회의록 시스템 패턴 사용
- 병렬 처리
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
from pathlib import Path
import re

# 88개 의회와 URL 패턴
COUNCILS = {
    # 표준 전자회의록 시스템 (cms.council.xxx.go.kr 또는 council.xxx.go.kr)
    'asan': ['https://cms.council.asan.go.kr/record/selectRecordList.do', 'https://council.asan.go.kr'],
    'bonghwa': ['https://www.bonghwa.go.kr/open.content/council/proceedings/', 'https://council.bonghwa.go.kr'],
    'boryeong': ['https://cms.council.boryeong.go.kr/record/selectRecordList.do'],
    'boseong': ['https://www.bscouncil.go.kr/', 'http://bscouncil.go.kr/'],
    'buan': ['https://livecouncil.buan.go.kr/', 'https://council.buan.go.kr/'],
    'buk_busan': ['https://council.bsbukgu.go.kr/', 'http://www.bsbukgu.go.kr/council/'],
    'buk_gwangju': ['https://council.bukgu.gwangju.kr/', 'http://www.bukgu.gwangju.kr/council/'],
    'buk_ulsan': ['https://council.bukgu.ulsan.kr/'],
    'busanjin': ['https://council.busanjin.go.kr/'],
    'cheongdo': ['https://council.cheongdo.go.kr/'],
    'cheongsong': ['https://council.cs.go.kr/', 'http://www.cscouncil.go.kr/'],
    'cheorwon': ['https://council.cwg.go.kr/'],
    'chilgok': ['https://council.chilgok.go.kr/'],
    'damyang': ['http://dycouncil.go.kr/'],
    'dobong': ['https://council.dobong.go.kr/'],
    'dong_busan': ['https://council.bsdonggu.go.kr/'],
    'dong_gwangju': ['https://council.donggu.gwangju.kr/'],
    'dongnae': ['https://council.dongnae.go.kr/'],
    'gangjin': ['https://www.gjcouncil.go.kr/'],
    'gangneung': ['https://www.gncl.go.kr/', 'https://council.gn.go.kr/'],
    'gangseo': ['https://council.gangseo.seoul.kr/'],
    'gangseo_busan': ['https://council.bsgangseo.go.kr/'],
    'geumjeong': ['https://council.geumjeong.go.kr/'],
    'gimje': ['https://council.gimje.go.kr/', 'http://www.gimje.go.kr/council/'],
    'gochang': ['https://council.gochang.go.kr/'],
    'goheung': ['https://council.goheung.go.kr/'],
    'gokseong': ['https://www.gokseong.go.kr/council/'],
    'gongju': ['https://council.gongju.go.kr/'],
    'goseong_gw': ['https://council.gwgs.go.kr/'],
    'gunsan': ['https://council.gunsan.go.kr/'],
    'guri': ['https://council.guri.go.kr/'],
    'guro': ['https://council.guro.go.kr/'],
    'gurye': ['https://council.gurye.go.kr/', 'https://www.gurye.go.kr/assembly/'],
    'gwangsan': ['https://council.gwangsan.go.kr/', 'http://www.gwangsan.go.kr/council/'],
    'gyeongsan': ['https://council.gs.go.kr/'],
    'hadong': ['https://www.hdcl.go.kr/'],
    'hampyeong': ['https://council.hampyeong.go.kr/'],
    'hanam': ['https://council.hanam.go.kr/'],
    'hapcheon': ['https://www.hccl.go.kr/'],
    'hoengseong': ['https://hsg.go.kr/council/'],
    'hongcheon': ['https://council.hongcheon.go.kr/'],
    'hwacheon': ['https://council.ihc.go.kr/'],
    'imsil': ['https://council.imsil.go.kr/'],
    'jangheung': ['https://council.jangheung.go.kr/'],
    'jangseong': ['https://council.jangseong.go.kr/'],
    'jeju': ['https://record.council.jeju.kr/'],
    'jeongeup': ['https://council.jeongeup.go.kr/', 'https://council.jcc.or.kr/'],
    'jeonju': ['https://council.jeonju.go.kr/'],
    'jindo': ['https://council.jindo.go.kr/', 'https://www.jindo.go.kr/council/'],
    'jung_busan': ['https://council.bsjunggu.go.kr/'],
    'jung_daegu': ['https://www.junggucouncil.daegu.kr/'],
    'jung_incheon': ['https://council.icjg.go.kr/'],
    'miryang': ['https://council.miryang.go.kr/'],
    'muan': ['http://www.muan.or.kr/'],
    'muju': ['https://council.muju.go.kr/'],
    'nam_gwangju': ['http://www.gjnc.or.kr/'],
    'namdong': ['https://council.namdong.go.kr/'],
    'namwon': ['https://council.namwon.go.kr/', 'https://live.council.namwon.go.kr/'],
    'namyangju': ['https://www.nyjc.go.kr/', 'https://council.nyj.go.kr/'],
    'nonsan': ['https://council.nonsan.go.kr/'],
    'pocheon': ['https://council.pocheon.go.kr/'],
    'pyeongtaek': ['https://council.pyeongtaek.go.kr/'],
    'seo_busan': ['https://council.bsseogu.go.kr/'],
    'seocho': ['https://council.seocho.go.kr/'],
    'seongdong': ['https://council.sd.go.kr/', 'https://sdcouncil.sd.go.kr/'],
    'seongju': ['https://www.sjcouncil.go.kr/'],
    'seongnam': ['https://council.seongnam.go.kr/'],
    'seosan': ['https://council.seosan.go.kr/'],
    'siheung': ['https://council.siheung.go.kr/'],
    'sinan': ['https://council.sinan.go.kr/'],
    'sunchang': ['https://www.sunchangcouncil.go.kr/'],
    'taean': ['https://council.taean.go.kr/'],
    'taebaek': ['https://council.taebaek.go.kr/'],
    'uijeongbu': ['https://council.ui4u.go.kr/'],
    'uiryeong': ['https://council.uiryeong.go.kr/'],
    'ulleung': ['https://council.ulleung.go.kr/', 'https://www.ulleung.go.kr/council/'],
    'wando': ['http://www.wdcc.or.kr/', 'http://www.wdcc.or.kr:8088/'],
    'wanju': ['https://council.wanju.go.kr/'],
    'yanggu': ['http://www.ygcl.go.kr/'],
    'yangju': ['https://council.yangju.go.kr/'],
    'yeoju': ['https://council.yeoju.go.kr/'],
    'yeongcheon': ['https://council.yc.go.kr/'],
    'yeongdo': ['https://council.yeongdo.go.kr/'],
    'yeonggwang': ['https://council.yeonggwang.go.kr/', 'https://kpk.ygcouncil.go.kr/'],
    'yeongwol': ['https://council.yw.go.kr/'],
    'yeongyang': ['https://councilbroadcast.yyg.go.kr/', 'https://www.yycouncil.go.kr/'],
    'yeonje': ['https://council.yeonje.go.kr/'],
    'yesan': ['https://council.yesan.go.kr/'],
}

OUTPUT_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes")

async def extract_content(page) -> str:
    """페이지에서 회의록 본문 추출"""
    try:
        selectors = [
            'div.minutes_content', 'div.view_content', 'div.content_view',
            'div.board_view', 'div#contentArea', 'pre', 'article',
            'div.con_wrap', 'div.content', 'div.detail_content',
        ]

        for sel in selectors:
            elem = await page.query_selector(sel)
            if elem:
                text = await elem.inner_text()
                if text and len(text) > 200:
                    return text.strip()

        # iframe 확인
        for frame in page.frames:
            if frame != page.main_frame:
                try:
                    body = await frame.query_selector('body')
                    if body:
                        text = await body.inner_text()
                        if text and len(text) > 200:
                            return text.strip()
                except:
                    pass

    except Exception:
        pass
    return ""

async def crawl_council(browser, council_code: str, urls: list) -> int:
    """단일 의회 크롤링"""
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        ignore_https_errors=True
    )
    page = await context.new_page()

    records = []

    for base_url in urls:
        try:
            await page.goto(base_url, timeout=25000, wait_until="domcontentloaded")
            await asyncio.sleep(2)

            # 회의록 링크 수집
            links = await page.query_selector_all('a')
            minute_links = []

            for link in links:
                try:
                    text = await link.inner_text()
                    text = text.strip()

                    # 회의록 패턴 확인
                    if re.search(r'(제\d+회|본회의|위원회|정례회|임시회|\d차|\d{4}년)', text):
                        if len(text) > 5 and len(text) < 200:
                            href = await link.get_attribute('href')
                            if href and not 'javascript:void' in href.lower():
                                if not href.startswith('http'):
                                    base = '/'.join(base_url.split('/')[:3])
                                    href = base + href if href.startswith('/') else base_url

                                minute_links.append((text, href))
                except:
                    continue

            # 상세 페이지에서 전문 추출
            for title, href in minute_links[:50]:
                try:
                    await page.goto(href, timeout=20000, wait_until="domcontentloaded")
                    await asyncio.sleep(1)

                    full_content = await extract_content(page)

                    record = {
                        "council_code": council_code,
                        "title": title,
                        "detail_url": href,
                        "meeting_id": "",
                        "cells": [title],
                        "crawled_at": datetime.now().isoformat(),
                        "date": "",
                        "full_content": full_content,
                        "source": "direct_v2"
                    }
                    records.append(record)

                except Exception:
                    continue

            if len(records) >= 10:
                break

        except Exception as e:
            continue

    await context.close()

    # 저장
    if records:
        valid = [r for r in records if r.get('full_content') and len(r['full_content']) > 100]

        if valid:
            output_file = OUTPUT_DIR / f"{council_code}.jsonl"
            with open(output_file, 'w', encoding='utf-8') as f:
                for r in valid:
                    f.write(json.dumps(r, ensure_ascii=False) + '\n')
            return len(valid)

    return 0

async def main():
    print("=" * 60)
    print("88개 의회 회의록 전문 크롤링 v2")
    print("=" * 60 + "\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        results = {}
        for council_code, urls in COUNCILS.items():
            print(f"크롤링: {council_code}", end=" ")
            try:
                count = await crawl_council(browser, council_code, urls)
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

    # 결과 요약
    print("\n" + "=" * 60)
    success = sum(1 for v in results.values() if v >= 10)
    partial = sum(1 for v in results.values() if 0 < v < 10)
    failed = sum(1 for v in results.values() if v == 0)
    total = sum(results.values())

    print(f"성공(10건+): {success}개 | 부분: {partial}개 | 실패: {failed}개")
    print(f"총 레코드: {total}건")

if __name__ == "__main__":
    asyncio.run(main())
