#!/usr/bin/env python3
"""
최종 2개 의회 - 영광, 강릉
"""

import asyncio
import json
import os
import re
from datetime import datetime
from urllib.parse import urljoin

from playwright.async_api import async_playwright

OUTPUT_DIR = "/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes"
os.makedirs(OUTPUT_DIR, exist_ok=True)

COUNCILS = {
    'yeonggwang': {
        'name': '영광군의회',
        'urls': [
            'https://www.ygcouncil.go.kr/',
            'https://www.ygcouncil.go.kr/assem/',
            'https://www.ygcouncil.go.kr/home/sub.php?menukey=92',
        ]
    },
    'gangneung': {
        'name': '강릉시의회',
        'urls': [
            'https://www.gncl.go.kr/',
            'https://www.gncl.go.kr/kr/minutes/late',
            'https://www.gncl.go.kr/kr/minutes/search.do',
        ]
    },
}

async def try_crawl(page, url):
    """URL에서 회의록 데이터 추출"""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=40000)
        await asyncio.sleep(4)
        
        content = await page.content()
        keywords = ['회의록', '본회의', '위원회', '정례회', '임시회', '의안', '회기']
        if not any(kw in content for kw in keywords):
            return []
        
        meetings = []
        
        # 테이블에서 추출
        tables = await page.query_selector_all('table')
        for table in tables:
            rows = await table.query_selector_all('tr')
            for row in rows:
                try:
                    text = (await row.inner_text()).strip()
                    if any(kw in text for kw in ['회의록', '본회의', '정례회', '임시회', '제', '위원회']):
                        link = await row.query_selector('a')
                        if link:
                            title = (await link.inner_text()).strip()
                            href = await link.get_attribute('href') or ''
                            detail_url = urljoin(url, href) if not href.startswith('javascript:') else url
                        else:
                            title = text[:80].replace('\n', ' ').replace('\t', ' ')
                            detail_url = url
                        
                        if title and len(title) > 3:
                            meetings.append({
                                'title': title,
                                'detail_url': detail_url,
                                'crawled_at': datetime.now().isoformat(),
                            })
                            if len(meetings) >= 10:
                                break
                except:
                    continue
            if meetings:
                break
        
        # 링크에서 추출
        if not meetings:
            links = await page.query_selector_all('a')
            for link in links:
                try:
                    text = (await link.inner_text()).strip()
                    if not text or len(text) < 5:
                        continue
                    if any(kw in text for kw in ['회의록', '본회의', '정례회', '임시회', '제', '위원회', '행정사무감사']):
                        href = await link.get_attribute('href') or ''
                        detail_url = urljoin(url, href) if not href.startswith('javascript:') else url
                        meetings.append({
                            'title': text[:100],
                            'detail_url': detail_url,
                            'crawled_at': datetime.now().isoformat(),
                        })
                        if len(meetings) >= 10:
                            break
                except:
                    continue
        
        # 메뉴/네비게이션에서 회의록 관련 링크 찾기
        if not meetings:
            nav_links = await page.query_selector_all('nav a, .gnb a, .lnb a, .menu a, [class*="menu"] a')
            for link in nav_links:
                try:
                    text = (await link.inner_text()).strip()
                    if '회의록' in text:
                        href = await link.get_attribute('href')
                        if href and not href.startswith('javascript:'):
                            new_url = urljoin(url, href)
                            await page.goto(new_url, wait_until="domcontentloaded", timeout=30000)
                            await asyncio.sleep(3)
                            # 재귀적으로 다시 시도
                            sub_meetings = await extract_meetings(page, new_url)
                            if sub_meetings:
                                return sub_meetings
                except:
                    continue
        
        return meetings
    except Exception as e:
        print(f"    오류: {str(e)[:40]}")
        return []

async def extract_meetings(page, url):
    """페이지에서 회의록 목록 추출"""
    meetings = []
    content = await page.content()
    
    if '회의록' not in content:
        return []
    
    # 테이블
    tables = await page.query_selector_all('table')
    for table in tables:
        rows = await table.query_selector_all('tr')
        for row in rows:
            try:
                link = await row.query_selector('a')
                if link:
                    text = (await link.inner_text()).strip()
                    if text and len(text) > 3:
                        href = await link.get_attribute('href') or ''
                        detail_url = urljoin(url, href) if not href.startswith('javascript:') else url
                        meetings.append({
                            'title': text[:100],
                            'detail_url': detail_url,
                            'crawled_at': datetime.now().isoformat(),
                        })
                        if len(meetings) >= 10:
                            return meetings
            except:
                continue
    
    # 리스트
    if not meetings:
        list_items = await page.query_selector_all('ul li a, .list a, .board a')
        for item in list_items:
            try:
                text = (await item.inner_text()).strip()
                if text and len(text) > 5 and any(kw in text for kw in ['회의록', '본회의', '정례회', '임시회', '제']):
                    href = await item.get_attribute('href') or ''
                    detail_url = urljoin(url, href) if not href.startswith('javascript:') else url
                    meetings.append({
                        'title': text[:100],
                        'detail_url': detail_url,
                        'crawled_at': datetime.now().isoformat(),
                    })
                    if len(meetings) >= 10:
                        return meetings
            except:
                continue
    
    return meetings

def save_results(code, meetings, name):
    if not meetings:
        return False
    
    seen = set()
    unique = []
    for m in meetings:
        key = m['title'][:50]
        if key not in seen:
            seen.add(key)
            unique.append(m)
    
    if not unique:
        return False
    
    jsonl_path = os.path.join(OUTPUT_DIR, f"{code}.jsonl")
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for m in unique:
            record = {
                'council_code': code,
                'title': m['title'],
                'detail_url': m['detail_url'],
                'meeting_id': '',
                'cells': [m['title']],
                'crawled_at': m['crawled_at'],
                'date': ''
            }
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    md_path = os.path.join(OUTPUT_DIR, f"{code}.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {name} 회의록\n\n")
        f.write(f"수집일시: {datetime.now().isoformat()}\n\n")
        f.write(f"총 {len(unique)}건\n\n")
        for i, m in enumerate(unique, 1):
            f.write(f"## {i}. {m['title']}\n\n")
            if m.get('detail_url'):
                f.write(f"- URL: {m['detail_url']}\n")
            f.write('\n')
    
    return True

async def main():
    completed = set()
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith('.jsonl') and not f.startswith('_'):
            completed.add(f.replace('.jsonl', ''))
    
    pending = {k: v for k, v in COUNCILS.items() if k not in completed}
    print(f"크롤링 대상: {len(pending)}개\n")
    
    if not pending:
        print("모든 의회 완료!")
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
    
    success = 0
    results = []
    
    try:
        for code, config in pending.items():
            name = config['name']
            urls = config['urls']
            print(f"[{code}] {name}...", end=" ", flush=True)
            
            page = await context.new_page()
            meetings = []
            
            try:
                for url in urls:
                    print(f"\n    시도: {url[:50]}...", end=" ", flush=True)
                    meetings = await try_crawl(page, url)
                    if meetings:
                        print(f"발견!", end=" ")
                        break
                    await asyncio.sleep(2)
                
                if meetings and save_results(code, meetings, name):
                    print(f"✅ {len(meetings)}건")
                    success += 1
                    results.append({'code': code, 'name': name, 'count': len(meetings)})
                else:
                    print("❌")
            except Exception as e:
                print(f"❌ {str(e)[:30]}")
            finally:
                await page.close()
            
            await asyncio.sleep(2)
    
    finally:
        await context.close()
        await browser.close()
        await playwright.stop()
    
    print(f"\n{'='*50}")
    print(f"성공: {success}개")
    if results:
        print("\n새로 완료된 의회:")
        for r in results:
            print(f"  - {r['name']} ({r['code']}): {r['count']}건")

if __name__ == "__main__":
    asyncio.run(main())
