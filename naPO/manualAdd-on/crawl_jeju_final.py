#!/usr/bin/env python3
"""
제주특별자치도의회 회의록 - 실제 회의록 목록 추출
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
        # 전자회의록 메인 -> 최근 회의록 페이지
        url = 'https://record.council.jeju.kr/source/minutes/main/main.html'
        print(f"전자회의록 메인 페이지 접속...")
        
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)
        
        content = await page.content()
        print(f"페이지 로드 완료. 내용 분석 중...")
        
        # 회의록 관련 키워드로 링크 필터링
        links = await page.query_selector_all('a')
        for link in links:
            try:
                text = (await link.inner_text()).strip()
                href = await link.get_attribute('href') or ''
                
                # 실제 회의록 링크 패턴
                if re.search(r'제\d+회|제\d+차|\d+차\s*본회의|\d+차\s*위원회', text):
                    if href.startswith('javascript:'):
                        # JavaScript 함수에서 파라미터 추출
                        match = re.search(r"['\"]([^'\"]+)['\"]", href)
                        meeting_id = match.group(1) if match else ""
                        detail_url = url
                    else:
                        detail_url = urljoin(url, href)
                        meeting_id = ""
                    
                    meetings.append({
                        'title': text[:150],
                        'detail_url': detail_url,
                        'meeting_id': meeting_id,
                        'date': ''
                    })
                    print(f"  발견: {text[:50]}")
            except:
                continue
        
        # 회의별 보기 페이지도 시도
        if len(meetings) < 10:
            print("\n회의별 보기 페이지 시도...")
            await page.goto('https://record.council.jeju.kr/source/minutes/pages/meeting.html?daesu=12', 
                           wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(5)
            
            links = await page.query_selector_all('a')
            for link in links:
                try:
                    text = (await link.inner_text()).strip()
                    href = await link.get_attribute('href') or ''
                    
                    if re.search(r'제\d+회|제\d+차|본회의|위원회|정례회|임시회', text):
                        if href and not href.startswith('javascript:'):
                            detail_url = urljoin('https://record.council.jeju.kr/', href)
                        else:
                            detail_url = 'https://record.council.jeju.kr/source/minutes/pages/meeting.html'
                        
                        meetings.append({
                            'title': text[:150].replace('\n', ' '),
                            'detail_url': detail_url,
                            'meeting_id': '',
                            'date': ''
                        })
                        print(f"  발견: {text[:50]}")
                        
                        if len(meetings) >= 25:
                            break
                except:
                    continue
        
        # select/option에서도 추출
        if len(meetings) < 10:
            options = await page.query_selector_all('select option')
            for opt in options:
                try:
                    text = (await opt.inner_text()).strip()
                    if re.search(r'제\d+회|정례회|임시회', text):
                        meetings.append({
                            'title': text[:150],
                            'detail_url': 'https://record.council.jeju.kr/source/minutes/pages/meeting.html',
                            'meeting_id': await opt.get_attribute('value') or '',
                            'date': ''
                        })
                        print(f"  옵션: {text[:50]}")
                except:
                    continue
        
        # 결과 저장
        if meetings:
            seen = set()
            unique = []
            for m in meetings:
                key = m['title'][:40]
                if key not in seen and len(m['title']) > 3:
                    seen.add(key)
                    unique.append(m)
            
            jsonl_path = os.path.join(OUTPUT_DIR, "jeju.jsonl")
            with open(jsonl_path, 'w', encoding='utf-8') as f:
                for m in unique:
                    record = {
                        'council_code': 'jeju',
                        'title': m['title'],
                        'detail_url': m['detail_url'],
                        'meeting_id': m.get('meeting_id', ''),
                        'cells': [m['title']],
                        'crawled_at': datetime.now().isoformat(),
                        'date': m.get('date', '')
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')
            
            print(f"\n✅ 제주특별자치도의회 완료: {len(unique)}건")
        else:
            print("\n❌ 회의록 데이터 미발견")
    
    finally:
        await page.close()
        await context.close()
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())
