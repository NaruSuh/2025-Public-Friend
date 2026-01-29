#!/usr/bin/env python3
"""
기존 레코드의 detail_url에서 전문 추출
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
from pathlib import Path
import sys

OUTPUT_DIR = Path("/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes")

# 전문 없는 의회
NO_FULLCONTENT = [
    'asan', 'bonghwa', 'boryeong', 'buk_busan', 'buk_gwangju',
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

async def extract_content(page) -> str:
    """페이지에서 회의록 전문 추출"""
    # iframe 확인
    for frame in page.frames:
        if frame != page.main_frame:
            try:
                body = await frame.query_selector('body')
                if body:
                    text = await body.inner_text()
                    if text and len(text) > 500:
                        return text.strip()
            except:
                pass

    # 본문 선택자
    selectors = [
        'div.view_content', 'div.content_view', 'div.minutes_view',
        'div.board_view', 'pre', 'article', 'div.detail_content',
        'div#contentArea', 'div.con_wrap', 'table.view_table',
        'div.bbs_view', 'div.bd_view', 'div.minutes_content',
        'div.viewContent', 'div#viewContent', 'div.minView'
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
            if len(lines) > 20:
                return '\n'.join(lines[:300])
    except:
        pass

    return ""

async def process_council(browser, council_code: str) -> int:
    """의회 레코드 처리"""
    file_path = OUTPUT_DIR / f"{council_code}.jsonl"

    if not file_path.exists():
        return 0

    # 기존 레코드 로드
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except:
                    pass

    if not records:
        return 0

    # 전문이 없고 detail_url이 있는 레코드 필터링
    to_fetch = []
    for r in records:
        has_content = r.get('full_content') and len(r['full_content']) > 500
        has_url = r.get('detail_url') and r['detail_url'].startswith('http')
        if not has_content and has_url:
            to_fetch.append(r)

    if not to_fetch:
        return 0

    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        ignore_https_errors=True
    )
    page = await context.new_page()

    updated_count = 0

    for r in to_fetch[:50]:
        try:
            url = r['detail_url']
            await page.goto(url, timeout=15000, wait_until="domcontentloaded")
            await asyncio.sleep(2)

            content = await extract_content(page)

            if content and len(content) > 500:
                r['full_content'] = content
                r['source'] = r.get('source', '') + '_fulltext_extracted'
                r['extracted_at'] = datetime.now().isoformat()
                updated_count += 1

        except Exception as e:
            continue

    await context.close()

    # 저장
    if updated_count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')

    return updated_count

async def main():
    print("=" * 60)
    print("기존 레코드 detail_url에서 전문 추출")
    print("=" * 60 + "\n")

    start_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end_idx = int(sys.argv[2]) if len(sys.argv) > 2 else len(NO_FULLCONTENT)

    councils = NO_FULLCONTENT[start_idx:end_idx]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        results = {}
        for i, code in enumerate(councils):
            print(f"[{i+1}/{len(councils)}] {code}", end=" ", flush=True)
            try:
                count = await process_council(browser, code)
                results[code] = count
                print(f"✅ {count}건 추출" if count > 0 else "❌")
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
