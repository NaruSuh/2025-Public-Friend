#!/usr/bin/env python3
"""
CLIK 포털을 통한 남은 의회 회의록 수집
"""

import asyncio
import json
import os
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs, quote

from playwright.async_api import async_playwright

OUTPUT_DIR = "/home/naru/skyimpact/Labgod/apps/naPO/manualAdd-on/output/basic_minutes"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 남은 11개 의회 - CLIK 검색 키워드
COUNCILS = {
    'yeonggwang': {'name': '영광군의회', 'keyword': '영광군'},
    'hapcheon': {'name': '합천군의회', 'keyword': '합천군'},
    'ulleung': {'name': '울릉군의회', 'keyword': '울릉군'},
    'namyangju': {'name': '남양주시의회', 'keyword': '남양주시'},
    'gangneung': {'name': '강릉시의회', 'keyword': '강릉시'},
    'gangseo_busan': {'name': '부산 강서구의회', 'keyword': '강서구 부산'},
    'jeongeup': {'name': '정읍시의회', 'keyword': '정읍시'},
    'jindo': {'name': '진도군의회', 'keyword': '진도군'},
    'seongju': {'name': '성주군의회', 'keyword': '성주군'},
    'chilgok': {'name': '칠곡군의회', 'keyword': '칠곡군'},
    'hadong': {'name': '하동군의회', 'keyword': '하동군'},
}

async def search_clik(page, code, keyword):
    """CLIK 포털에서 의회 회의록 검색"""
    try:
        # CLIK 검색 URL
        search_url = f"https://clik.nanet.go.kr/potal/search/searchList.do?collection=minutes&query={quote(keyword)}"

        await page.goto(search_url, wait_until="networkidle", timeout=45000)
        await asyncio.sleep(3)

        content = await page.content()

        meetings = []

        # 검색 결과에서 회의록 추출
        results = await page.query_selector_all('.search-result-item, .result-item, .list-item, tr')

        for result in results[:15]:
            text = (await result.inner_text()).strip()

            # 회의록 관련 키워드 확인
            if not any(kw in text for kw in ['본회의', '위원회', '정례회', '임시회', '회의록']):
                continue

            link = await result.query_selector('a[href]')
            detail_url = ""
            if link:
                href = await link.get_attribute('href') or ''
                if href and not href.startswith('javascript:'):
                    detail_url = urljoin("https://clik.nanet.go.kr", href)
                title = (await link.inner_text()).strip()
            else:
                title = text[:100]

            if not title or len(title) < 5:
                continue

            # 날짜 추출
            date_match = re.search(r'(\d{4}[-./]\d{1,2}[-./]\d{1,2})', text)
            date = date_match.group(1) if date_match else ""

            meetings.append({
                'council_code': code,
                'title': title,
                'detail_url': detail_url if detail_url else search_url,
                'meeting_id': '',
                'cells': [text[:200]],
                'crawled_at': datetime.now().isoformat(),
                'date': date,
                'source': 'CLIK Portal'
            })

        return meetings
    except Exception as e:
        print(f"    CLIK 오류: {str(e)[:40]}")
        return []

async def direct_crawl(page, code, name):
    """직접 의회 사이트 크롤링 (대안 URL)"""
    alt_urls = {
        'yeonggwang': 'https://www.ygcouncil.go.kr/',
        'hapcheon': 'https://www.hccl.go.kr/',
        'ulleung': 'https://www.ulleung.go.kr/council/',
        'namyangju': 'https://www.nyjc.go.kr/content/minutes/meetingRetrieval.html',
        'gangneung': 'https://www.gncl.go.kr/kr/minutes/late',
        'gangseo_busan': 'https://www.bsgangseo.go.kr/council/',
        'jeongeup': 'https://council.jcc.or.kr/',
        'jindo': 'https://www.jindo.go.kr/council/',
        'seongju': 'https://www.sjcouncil.go.kr/',
        'chilgok': 'https://council.chilgok.go.kr/',
        'hadong': 'https://www.hdcl.go.kr/',
    }

    if code not in alt_urls:
        return []

    url = alt_urls[code]

    try:
        await page.goto(url, wait_until="networkidle", timeout=45000)
        await asyncio.sleep(3)

        content = await page.content()
        keywords = ['회의록', '본회의', '위원회', '정례회', '임시회', '의안', '의정활동']

        if not any(kw in content for kw in keywords):
            return []

        meetings = []

        # 모든 링크에서 회의록 관련 항목 찾기
        links = await page.query_selector_all('a[href]')

        for link in links[:50]:
            text = (await link.inner_text()).strip()

            if not text or len(text) < 3:
                continue

            if any(kw in text for kw in ['회의록', '본회의', '정례회', '임시회', '제', '위원회']):
                href = await link.get_attribute('href') or ''

                if href.startswith('javascript:'):
                    detail_url = url
                else:
                    detail_url = urljoin(url, href)

                meetings.append({
                    'council_code': code,
                    'title': text[:100],
                    'detail_url': detail_url,
                    'meeting_id': '',
                    'cells': [text],
                    'crawled_at': datetime.now().isoformat(),
                    'date': ''
                })

                if len(meetings) >= 10:
                    break

        return meetings
    except Exception as e:
        print(f"    직접 크롤링 오류: {str(e)[:30]}")
        return []

def save_results(code, meetings):
    if not meetings:
        return False

    jsonl_path = os.path.join(OUTPUT_DIR, f"{code}.jsonl")
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for m in meetings:
            f.write(json.dumps(m, ensure_ascii=False) + '\n')

    md_path = os.path.join(OUTPUT_DIR, f"{code}.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {code} 회의록\n\n")
        f.write(f"수집일시: {datetime.now().isoformat()}\n\n")
        f.write(f"총 {len(meetings)}건\n\n")
        for i, m in enumerate(meetings, 1):
            f.write(f"## {i}. {m.get('title', 'N/A')}\n\n")
            if m.get('date'):
                f.write(f"- 날짜: {m['date']}\n")
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
            keyword = config['keyword']
            print(f"[{code}] {name}...", end=" ", flush=True)

            page = await context.new_page()
            try:
                # 먼저 직접 크롤링 시도
                meetings = await direct_crawl(page, code, name)

                # 실패시 CLIK 포털 시도
                if not meetings:
                    meetings = await search_clik(page, code, keyword)

                if meetings:
                    save_results(code, meetings)
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
