#!/usr/bin/env python3
"""
제주특별자치도의회 회의록 크롤링 - Playwright 사용
"""

import asyncio
import json
import os
import re
from datetime import datetime
from urllib.parse import urljoin

from playwright.async_api import async_playwright

OUTPUT_DIR = "/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes"

# 제주도의회 시도 URL들
URLS = [
    'https://www.council.jeju.kr/',
    'https://www.council.jeju.kr/contents/index.php?mid=0501',  # 회의록 메뉴 추정
    'https://www.council.jeju.kr/contents/index.php?mid=0502',
    'https://www.council.jeju.kr/contents/index.php?mid=0503',
    'https://council.jeju.kr/source/korean/minutes/late.do',
    'https://council.jeju.kr/source/korean/minutes/search.do',
    'http://record.council.jeju.kr/',
    'https://www.council.jeju.kr/board/list.jeju',
]

async def extract_meetings(page, url):
    """페이지에서 회의록 데이터 추출"""
    meetings = []
    content = await page.content()
    
    # 회의록 관련 키워드 확인
    if not any(kw in content for kw in ['회의록', '본회의', '위원회', '정례회', '임시회', '의안', '회기']):
        return []
    
    # 테이블에서 추출
    tables = await page.query_selector_all('table')
    for table in tables:
        rows = await table.query_selector_all('tbody tr, tr')
        for row in rows:
            try:
                link = await row.query_selector('a')
                if link:
                    text = (await link.inner_text()).strip()
                    if text and len(text) > 3:
                        href = await link.get_attribute('href') or ''
                        detail_url = urljoin(url, href) if not href.startswith('javascript:') else url
                        
                        # 날짜 추출 시도
                        row_text = await row.inner_text()
                        date_match = re.search(r'(\d{4}[-./]\d{1,2}[-./]\d{1,2})', row_text)
                        date = date_match.group(1) if date_match else ''
                        
                        meetings.append({
                            'title': text[:150],
                            'detail_url': detail_url,
                            'date': date,
                            'crawled_at': datetime.now().isoformat(),
                        })
                        
                        if len(meetings) >= 20:
                            return meetings
            except:
                continue
    
    # 링크에서 추출
    if not meetings:
        links = await page.query_selector_all('a')
        for link in links:
            try:
                text = (await link.inner_text()).strip()
                if not text or len(text) < 5:
                    continue
                
                keywords = ['회의록', '본회의', '정례회', '임시회', '제', '위원회', '상임위', '특별위', '예결위']
                if any(kw in text for kw in keywords):
                    href = await link.get_attribute('href') or ''
                    detail_url = urljoin(url, href) if not href.startswith('javascript:') else url
                    
                    meetings.append({
                        'title': text[:150],
                        'detail_url': detail_url,
                        'date': '',
                        'crawled_at': datetime.now().isoformat(),
                    })
                    
                    if len(meetings) >= 20:
                        return meetings
            except:
                continue
    
    return meetings

async def navigate_to_minutes(page, base_url):
    """메인 페이지에서 회의록 메뉴로 이동"""
    try:
        # 회의록 메뉴 찾기
        menu_selectors = [
            'a:has-text("회의록")',
            'a:has-text("의정활동")',
            'a:has-text("본회의")',
            '[class*="menu"] a:has-text("회의")',
            'nav a:has-text("회의")',
        ]
        
        for selector in menu_selectors:
            try:
                menu = await page.query_selector(selector)
                if menu:
                    href = await menu.get_attribute('href')
                    if href and not href.startswith('javascript:') and href != '#':
                        new_url = urljoin(base_url, href)
                        print(f"    메뉴 발견: {new_url[:60]}...")
                        await page.goto(new_url, wait_until="domcontentloaded", timeout=30000)
                        await asyncio.sleep(3)
                        return new_url
            except:
                continue
        
        return None
    except:
        return None

async def main():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )
    context = await browser.new_context(
        ignore_https_errors=True,
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    page = await context.new_page()
    
    meetings = []
    
    try:
        print("=" * 50)
        print("제주특별자치도의회 회의록 크롤링")
        print("=" * 50)
        
        for url in URLS:
            print(f"\n시도: {url[:60]}...", end=" ", flush=True)
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=40000)
                await asyncio.sleep(4)
                
                # 페이지 내용 확인
                content = await page.content()
                if '제주' in content:
                    print("접속 성공!", end=" ")
                    
                    # 회의록 데이터 추출
                    meetings = await extract_meetings(page, url)
                    
                    if not meetings:
                        # 회의록 메뉴로 이동 시도
                        new_url = await navigate_to_minutes(page, url)
                        if new_url:
                            meetings = await extract_meetings(page, new_url)
                    
                    if meetings:
                        print(f"✅ {len(meetings)}건 발견!")
                        break
                    else:
                        print("데이터 없음")
                else:
                    print("페이지 로드 실패")
                    
            except Exception as e:
                print(f"오류: {str(e)[:40]}")
            
            await asyncio.sleep(2)
        
        # CLIK 포털 백업 시도
        if not meetings:
            print("\n\nCLIK 포털에서 제주도의회 검색 시도...")
            try:
                await page.goto('https://clik.nanet.go.kr/', wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)
                
                # 검색
                search_input = await page.query_selector('input[type="text"], input[name*="search"], #searchKeyword')
                if search_input:
                    await search_input.fill('제주특별자치도의회 회의록')
                    await page.keyboard.press('Enter')
                    await asyncio.sleep(4)
                    
                    meetings = await extract_meetings(page, 'https://clik.nanet.go.kr/')
                    if meetings:
                        print(f"CLIK에서 {len(meetings)}건 발견!")
            except Exception as e:
                print(f"CLIK 오류: {str(e)[:40]}")
        
        # 결과 저장
        if meetings:
            # 중복 제거
            seen = set()
            unique = []
            for m in meetings:
                key = m['title'][:50]
                if key not in seen:
                    seen.add(key)
                    unique.append(m)
            
            jsonl_path = os.path.join(OUTPUT_DIR, "jeju.jsonl")
            with open(jsonl_path, 'w', encoding='utf-8') as f:
                for m in unique:
                    record = {
                        'council_code': 'jeju',
                        'title': m['title'],
                        'detail_url': m['detail_url'],
                        'meeting_id': '',
                        'cells': [m['title']],
                        'crawled_at': m['crawled_at'],
                        'date': m.get('date', '')
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')
            
            md_path = os.path.join(OUTPUT_DIR, "jeju.md")
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write("# 제주특별자치도의회 회의록\n\n")
                f.write(f"수집일시: {datetime.now().isoformat()}\n\n")
                f.write(f"총 {len(unique)}건\n\n")
                for i, m in enumerate(unique, 1):
                    f.write(f"## {i}. {m['title']}\n\n")
                    if m.get('date'):
                        f.write(f"- 날짜: {m['date']}\n")
                    if m.get('detail_url'):
                        f.write(f"- URL: {m['detail_url']}\n")
                    f.write('\n')
            
            print(f"\n{'='*50}")
            print(f"✅ 제주특별자치도의회 완료: {len(unique)}건 저장")
            print(f"{'='*50}")
        else:
            print(f"\n{'='*50}")
            print("❌ 제주특별자치도의회 - 데이터 수집 실패")
            print("{'='*50}")
    
    finally:
        await page.close()
        await context.close()
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())
