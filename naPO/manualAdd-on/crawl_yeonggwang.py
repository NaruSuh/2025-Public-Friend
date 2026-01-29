#!/usr/bin/env python3
"""
영광군의회 - 최종 시도
"""

import asyncio
import json
import os
from datetime import datetime
from urllib.parse import urljoin

from playwright.async_api import async_playwright

OUTPUT_DIR = "/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes"

# 시도할 모든 URL
URLS = [
    'https://www.ygcouncil.go.kr/',
    'https://www.ygcouncil.go.kr/assem/bbs/board.php?bo_table=minutes',
    'https://www.ygcouncil.go.kr/assem/bbs/board.php?bo_table=record',
    'https://www.ygcouncil.go.kr/home/sub.php?menukey=92',
    'https://www.ygcouncil.go.kr/home/sub.php?menukey=93',
    'https://www.ygcouncil.go.kr/home/sub.php?menukey=94',
    'http://kpk.ygcouncil.go.kr/',
    'https://clik.nanet.go.kr/SearchRecord',
]

async def extract_from_page(page, url):
    """페이지에서 회의록 추출"""
    meetings = []
    
    # 모든 링크 확인
    links = await page.query_selector_all('a')
    for link in links:
        try:
            text = (await link.inner_text()).strip()
            if not text or len(text) < 3:
                continue
            
            keywords = ['회의록', '본회의', '정례회', '임시회', '제', '위원회', '행정', '감사', '조례']
            if any(kw in text for kw in keywords):
                href = await link.get_attribute('href') or ''
                if href.startswith('javascript:'):
                    detail_url = url
                else:
                    detail_url = urljoin(url, href)
                
                meetings.append({
                    'title': text[:100],
                    'detail_url': detail_url,
                    'crawled_at': datetime.now().isoformat(),
                })
                
                if len(meetings) >= 15:
                    break
        except:
            continue
    
    # 테이블 행에서도 추출
    if not meetings:
        rows = await page.query_selector_all('table tr')
        for row in rows:
            try:
                text = (await row.inner_text()).strip()
                if any(kw in text for kw in ['회의록', '본회의', '정례회', '임시회', '위원회']):
                    meetings.append({
                        'title': text[:80].replace('\n', ' ').replace('\t', ' '),
                        'detail_url': url,
                        'crawled_at': datetime.now().isoformat(),
                    })
                    if len(meetings) >= 10:
                        break
            except:
                continue
    
    return meetings

async def main():
    # 이미 완료되었는지 확인
    jsonl_path = os.path.join(OUTPUT_DIR, "yeonggwang.jsonl")
    if os.path.exists(jsonl_path):
        print("영광군의회 이미 완료!")
        return
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )
    context = await browser.new_context(
        ignore_https_errors=True,
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    )
    page = await context.new_page()
    
    meetings = []
    
    try:
        for url in URLS:
            print(f"시도: {url[:60]}...", end=" ", flush=True)
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)
                
                content = await page.content()
                # 회의록 관련 콘텐츠 확인
                if '영광' in content or '회의록' in content:
                    meetings = await extract_from_page(page, url)
                    if meetings:
                        print(f"✅ {len(meetings)}건 발견!")
                        break
                    else:
                        print("콘텐츠 없음")
                else:
                    print("페이지 없음")
            except Exception as e:
                print(f"오류: {str(e)[:30]}")
            
            await asyncio.sleep(2)
        
        # CLIK 포털에서 검색
        if not meetings:
            print("\nCLIK 포털 검색 시도...")
            try:
                await page.goto('https://clik.nanet.go.kr/', wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)
                
                # 검색창에 영광군의회 입력
                search_input = await page.query_selector('input[type="text"], input[name*="search"], input[id*="search"]')
                if search_input:
                    await search_input.fill('영광군의회')
                    await page.keyboard.press('Enter')
                    await asyncio.sleep(4)
                    
                    meetings = await extract_from_page(page, 'https://clik.nanet.go.kr/')
                    if meetings:
                        print(f"CLIK에서 {len(meetings)}건 발견!")
            except Exception as e:
                print(f"CLIK 오류: {str(e)[:30]}")
        
        # 결과 저장
        if meetings:
            # 중복 제거
            seen = set()
            unique = []
            for m in meetings:
                key = m['title'][:40]
                if key not in seen:
                    seen.add(key)
                    unique.append(m)
            
            with open(jsonl_path, 'w', encoding='utf-8') as f:
                for m in unique:
                    record = {
                        'council_code': 'yeonggwang',
                        'title': m['title'],
                        'detail_url': m['detail_url'],
                        'meeting_id': '',
                        'cells': [m['title']],
                        'crawled_at': m['crawled_at'],
                        'date': ''
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')
            
            md_path = os.path.join(OUTPUT_DIR, "yeonggwang.md")
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write("# 영광군의회 회의록\n\n")
                f.write(f"수집일시: {datetime.now().isoformat()}\n\n")
                f.write(f"총 {len(unique)}건\n\n")
                for i, m in enumerate(unique, 1):
                    f.write(f"## {i}. {m['title']}\n\n")
                    if m.get('detail_url'):
                        f.write(f"- URL: {m['detail_url']}\n")
                    f.write('\n')
            
            print(f"\n✅ 영광군의회 완료: {len(unique)}건 저장")
        else:
            print("\n❌ 영광군의회 실패 - 데이터 발견 못함")
    
    finally:
        await page.close()
        await context.close()
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())
