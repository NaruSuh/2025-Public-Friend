#!/usr/bin/env python3
"""
최종 5개 의회 - 마지막 시도
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

# 남은 5개 - 다양한 URL 시도
COUNCILS = {
    'yeonggwang': {
        'name': '영광군의회',
        'urls': [
            'https://kpk.ygcouncil.go.kr/assem/',
            'https://www.ygcouncil.go.kr/assem/view.php?wr_id=2172',
            'https://ygcouncil.go.kr/',
        ]
    },
    'ulleung': {
        'name': '울릉군의회',
        'urls': [
            'https://www.ulleung.go.kr/council/page.do?mnu_uid=872',
            'https://www.ulleung.go.kr/council/',
        ]
    },
    'gangneung': {
        'name': '강릉시의회',
        'urls': [
            'http://152.99.143.161:8080/assembly/late.do',
            'http://sys.gncl.go.kr/kr/minutes/late.do',
            'https://www.gncl.go.kr/kr/minutes/late',
        ]
    },
    'gangseo_busan': {
        'name': '부산 강서구의회',
        'urls': [
            'https://www.bsgangseo.go.kr/council/contents.do?mId=0203030000',
            'https://www.bsgangseo.go.kr/council/',
        ]
    },
    'jindo': {
        'name': '진도군의회',
        'urls': [
            'https://www.jindo.go.kr/council/sub.cs?m=14',
            'https://www.jindo.go.kr/council/main.cs',
        ]
    },
}

async def try_crawl(page, url):
    """URL에서 회의록 데이터 추출 시도"""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        content = await page.content()

        # 페이지에 회의록 관련 콘텐츠가 있는지 확인
        keywords = ['회의록', '본회의', '위원회', '정례회', '임시회', '의안']
        if not any(kw in content for kw in keywords):
            return []

        meetings = []

        # 모든 링크 수집
        links = await page.query_selector_all('a')
        for link in links:
            try:
                text = (await link.inner_text()).strip()
                if not text or len(text) < 3:
                    continue

                # 회의록 관련 키워드가 포함된 링크만 선택
                if any(kw in text for kw in ['회의록', '본회의', '정례회', '임시회', '제', '위원회', '행정사무감사']):
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

                    if len(meetings) >= 10:
                        break
            except:
                continue

        # 테이블에서도 추출 시도
        if not meetings:
            tables = await page.query_selector_all('table')
            for table in tables:
                rows = await table.query_selector_all('tr')
                for row in rows:
                    try:
                        text = (await row.inner_text()).strip()
                        if any(kw in text for kw in ['회의록', '본회의', '정례회', '임시회', '제']):
                            meetings.append({
                                'title': text[:100].replace('\n', ' ').replace('\t', ' '),
                                'detail_url': url,
                                'crawled_at': datetime.now().isoformat(),
                            })
                            if len(meetings) >= 10:
                                break
                    except:
                        continue
                if meetings:
                    break

        return meetings
    except Exception as e:
        return []

def save_results(code, meetings, name):
    if not meetings:
        return False

    # 중복 제거
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
                    meetings = await try_crawl(page, url)
                    if meetings:
                        break
                    await asyncio.sleep(1)

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
