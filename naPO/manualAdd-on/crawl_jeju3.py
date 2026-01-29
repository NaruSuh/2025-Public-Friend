#!/usr/bin/env python3
"""
제주특별자치도의회 회의록 - record.council.jeju.kr
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
        # record.council.jeju.kr 직접 접속
        urls = [
            'https://record.council.jeju.kr/',
            'https://record.council.jeju.kr/source/minutes/pages/meeting.html',
            'https://record.council.jeju.kr/source/minutes/pages/meeting.html?daesu=12',
            'https://record.council.jeju.kr/CLRecords/Retrieval2/',
        ]
        
        for url in urls:
            print(f"시도: {url[:60]}...", end=" ", flush=True)
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(4)
                
                content = await page.content()
                
                if '제주' in content or '회의록' in content or '본회의' in content:
                    print("접속 성공!", end=" ")
                    
                    # 링크에서 회의록 추출
                    links = await page.query_selector_all('a')
                    for link in links:
                        try:
                            text = (await link.inner_text()).strip()
                            if not text or len(text) < 3:
                                continue
                            
                            # 회의록 관련 텍스트 확인
                            keywords = ['본회의', '위원회', '정례회', '임시회', '제', '차', '회의록']
                            if any(kw in text for kw in keywords) or re.search(r'제\d+회|제\d+차|\d+차', text):
                                href = await link.get_attribute('href') or ''
                                if href.startswith('javascript:'):
                                    detail_url = url
                                else:
                                    detail_url = urljoin(url, href)
                                
                                meetings.append({
                                    'title': text[:150],
                                    'detail_url': detail_url,
                                    'date': ''
                                })
                                
                                if len(meetings) >= 30:
                                    break
                        except:
                            continue
                    
                    # 테이블 행에서도 추출
                    if len(meetings) < 10:
                        rows = await page.query_selector_all('table tr, li, .item')
                        for row in rows:
                            try:
                                text = (await row.inner_text()).strip()
                                if '본회의' in text or '위원회' in text or re.search(r'제\d+회|제\d+차', text):
                                    link = await row.query_selector('a')
                                    if link:
                                        href = await link.get_attribute('href') or ''
                                        detail_url = urljoin(url, href) if not href.startswith('javascript:') else url
                                    else:
                                        detail_url = url
                                    
                                    title = text[:100].replace('\n', ' ').replace('\t', ' ')
                                    meetings.append({
                                        'title': title,
                                        'detail_url': detail_url,
                                        'date': ''
                                    })
                                    
                                    if len(meetings) >= 30:
                                        break
                            except:
                                continue
                    
                    if meetings:
                        print(f"✅ {len(meetings)}건!")
                        break
                    else:
                        print("데이터 없음")
                else:
                    print("페이지 없음")
                    
            except Exception as e:
                print(f"오류: {str(e)[:30]}")
            
            await asyncio.sleep(2)
        
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
            
            print(f"\n✅ 제주특별자치도의회 완료: {len(unique)}건 저장")
        else:
            print("\n❌ 데이터 수집 실패")
    
    finally:
        await page.close()
        await context.close()
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())
