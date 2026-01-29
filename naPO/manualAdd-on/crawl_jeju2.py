#!/usr/bin/env python3
"""
제주특별자치도의회 회의록 - 더 깊은 탐색
"""

import asyncio
import json
import os
import re
from datetime import datetime
from urllib.parse import urljoin

from playwright.async_api import async_playwright

OUTPUT_DIR = "/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes"

async def main():
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
        # 회의록 직접 URL들 시도
        minute_urls = [
            'https://www.council.jeju.kr/conts/openmeet/index.do',  # 공개회의
            'https://www.council.jeju.kr/conts/minutes/index.do',   # 회의록
            'https://www.council.jeju.kr/conts/minutes/list.do',
            'https://www.council.jeju.kr/assembly/minutes/late.do',
            'https://www.council.jeju.kr/act/list.do',              # 의정활동
            'https://www.council.jeju.kr/board/minutes/list.do',
        ]
        
        for url in minute_urls:
            print(f"시도: {url}...", end=" ", flush=True)
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=25000)
                await asyncio.sleep(3)
                
                content = await page.content()
                if '제주' in content and ('회의' in content or '본회의' in content):
                    print("접속!", end=" ")
                    
                    # 테이블에서 회의록 추출
                    rows = await page.query_selector_all('table tbody tr, table tr')
                    for row in rows:
                        try:
                            link = await row.query_selector('a')
                            if link:
                                text = (await link.inner_text()).strip()
                                if text and len(text) > 3:
                                    href = await link.get_attribute('href') or ''
                                    detail_url = urljoin(url, href) if not href.startswith('javascript:') else url
                                    
                                    row_text = await row.inner_text()
                                    date_match = re.search(r'(\d{4}[-./]\d{1,2}[-./]\d{1,2})', row_text)
                                    date = date_match.group(1) if date_match else ''
                                    
                                    meetings.append({
                                        'title': text[:150],
                                        'detail_url': detail_url,
                                        'date': date
                                    })
                        except:
                            continue
                    
                    if meetings:
                        print(f"✅ {len(meetings)}건!")
                        break
                    else:
                        print("데이터 없음")
                else:
                    print("실패")
            except Exception as e:
                print(f"오류")
            
            await asyncio.sleep(1)
        
        # 메인 페이지에서 회의록 메뉴 탐색
        if not meetings:
            print("\n메인 페이지에서 회의록 메뉴 탐색...")
            await page.goto('https://www.council.jeju.kr/', wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            
            # 모든 메뉴 링크 확인
            links = await page.query_selector_all('a')
            for link in links:
                try:
                    text = (await link.inner_text()).strip()
                    if '회의록' in text or '본회의' in text:
                        href = await link.get_attribute('href')
                        if href and not href.startswith('javascript:'):
                            full_url = urljoin('https://www.council.jeju.kr/', href)
                            print(f"  발견: {text} -> {full_url[:50]}")
                            
                            await page.goto(full_url, wait_until="domcontentloaded", timeout=25000)
                            await asyncio.sleep(3)
                            
                            # 다시 데이터 추출 시도
                            rows = await page.query_selector_all('table tbody tr, table tr, .list-item, .board-item')
                            for row in rows:
                                try:
                                    sub_link = await row.query_selector('a')
                                    if sub_link:
                                        sub_text = (await sub_link.inner_text()).strip()
                                        if sub_text and len(sub_text) > 5:
                                            sub_href = await sub_link.get_attribute('href') or ''
                                            detail_url = urljoin(full_url, sub_href) if not sub_href.startswith('javascript:') else full_url
                                            meetings.append({
                                                'title': sub_text[:150],
                                                'detail_url': detail_url,
                                                'date': ''
                                            })
                                except:
                                    continue
                            
                            if meetings:
                                print(f"  ✅ {len(meetings)}건 발견!")
                                break
                except:
                    continue
        
        # 최종 저장
        if meetings:
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
                        'crawled_at': datetime.now().isoformat(),
                        'date': m.get('date', '')
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')
            
            print(f"\n✅ 제주도의회 완료: {len(unique)}건")
        else:
            print("\n기존 데이터 유지")
            
    finally:
        await page.close()
        await context.close()
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())
