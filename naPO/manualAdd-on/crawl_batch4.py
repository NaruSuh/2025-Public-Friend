#!/usr/bin/env python3
"""
배치 크롤링 4차 - 웹 검색으로 발견된 URL들
"""

import asyncio
import json
import os
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs

from playwright.async_api import async_playwright

OUTPUT_DIR = "/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 웹 검색으로 발견된 URL들
URLS = {
    # 비표준 구조 - 발견된 URL
    'namyangju': {
        'name': '남양주시의회',
        'url': 'https://nyjc.go.kr/content/minutes/meetingRetrieval.html'
    },
    'jung_busan': {
        'name': '부산 중구의회',
        'url': 'https://www.bsjunggu.go.kr/board/list.junggu?boardId=BBS_0000048&menuCd=DOM_000000513004000000&contentsSid=1320'
    },
    'gangseo_busan': {
        'name': '부산 강서구의회',
        'url': 'https://www.bsgangseo.go.kr/council/contents.do?mId=0203020000'
    },
    'jung_daegu': {
        'name': '대구 중구의회',
        'url': 'https://www.junggucouncil.daegu.kr/'
    },
    'nam_gwangju': {
        'name': '광주 남구의회',
        'url': 'http://www.gjnc.or.kr/'
    },
    'buk_gwangju': {
        'name': '광주 북구의회',
        'url': 'https://council.bukgu.gwangju.kr/'
    },
    'gwangsan': {
        'name': '광주 광산구의회',
        'url': 'https://gjgc.or.kr/'
    },
    'hoengseong': {
        'name': '횡성군의회',
        'url': 'https://hsg.go.kr/council/index.do'
    },

    # 소규모 군의회 - 발견된 URL
    'taean': {
        'name': '태안군의회',
        'url': 'https://council.taean.go.kr/main/'
    },
    'imsil': {
        'name': '임실군의회',
        'url': 'https://council.imsil.go.kr/'
    },
    'gochang': {
        'name': '고창군의회',
        'url': 'https://assembly.gochang.go.kr/'
    },
    'buan': {
        'name': '부안군의회',
        'url': 'https://assembly.buan.go.kr/'
    },
    'damyang': {
        'name': '담양군의회',
        'url': 'http://dycouncil.go.kr/'
    },
    'gokseong': {
        'name': '곡성군의회',
        'url': 'https://assembly.gokseong.go.kr/minutes/content/minutes/gunQuestion.html'
    },
    'gurye': {
        'name': '구례군의회',
        'url': 'https://council.gurye.go.kr/assembly/'
    },
    'boseong': {
        'name': '보성군의회',
        'url': 'https://assembly.boseong.go.kr/'
    },
    'jangheung': {
        'name': '장흥군의회',
        'url': 'https://jhc.go.kr/'
    },
    'muan': {
        'name': '무안군의회',
        'url': 'http://www.muan.or.kr/'
    },
    'jindo': {
        'name': '진도군의회',
        'url': 'https://www.jindo.go.kr/council/main.cs'
    },
    'sinan': {
        'name': '신안군의회',
        'url': 'https://council.shinan.go.kr/'
    },
    'cheongsong': {
        'name': '청송군의회',
        'url': 'https://www.cs.go.kr/council/'
    },
    'yeongyang': {
        'name': '영양군의회',
        'url': 'https://councilbroadcast.yyg.go.kr/'
    },
    'seongju': {
        'name': '성주군의회',
        'url': 'https://www.sjcouncil.go.kr/'
    },
    'chilgok': {
        'name': '칠곡군의회',
        'url': 'https://council.chilgok.go.kr/'
    },
    'hadong': {
        'name': '하동군의회',
        'url': 'https://www.hdcl.go.kr/source/korean/main/main.html'
    },

    # DNS/사이트 이슈 - 시도해볼 URL
    'cheorwon': {
        'name': '철원군의회',
        'url': 'https://council.cwg.go.kr/council/index.do'
    },
    'yanggu': {
        'name': '양구군의회',
        'url': 'http://www.ygcl.go.kr/portal/index'
    },
}

async def crawl_page(page, code, url):
    try:
        await page.goto(url, wait_until="networkidle", timeout=45000)
        await asyncio.sleep(3)

        content = await page.content()
        keywords = ['회의록', '본회의', '위원회', '정례회', '임시회', '의안', '회기']
        if not any(kw in content for kw in keywords):
            return []

        meetings = []

        # 테이블에서 회의록 정보 추출
        tables = await page.query_selector_all('table')
        for table in tables:
            rows = await table.query_selector_all('tbody tr')
            if not rows:
                rows = await table.query_selector_all('tr')

            for row in rows:
                cells = await row.query_selector_all('td')
                if len(cells) < 2:
                    continue

                link = await row.query_selector('a[href]')
                if not link:
                    continue

                title = (await link.inner_text()).strip()
                if not title or len(title) < 2:
                    continue

                href = await link.get_attribute('href') or ''

                if href.startswith('javascript:'):
                    match = re.search(r"['\"]([^'\"]+)['\"]", href)
                    meeting_id = match.group(1) if match else ""
                    detail_url = ""
                else:
                    detail_url = urljoin(url, href)
                    parsed = urlparse(detail_url)
                    params = parse_qs(parsed.query)
                    meeting_id = ""
                    for key in ['uid', 'id', 'mntsId', 'schSn', 'sess_id', 'no', 'seq', 'board_key', 'minuteSid', 'dataSid']:
                        if key in params:
                            meeting_id = params[key][0]
                            break

                cell_texts = []
                for cell in cells:
                    text = (await cell.inner_text()).strip()
                    cell_texts.append(text)

                date = ""
                for text in cell_texts:
                    if re.match(r'\d{4}[-./]\d{1,2}[-./]\d{1,2}', text):
                        date = text
                        break

                meetings.append({
                    'council_code': code,
                    'title': title,
                    'detail_url': detail_url,
                    'meeting_id': meeting_id,
                    'cells': cell_texts,
                    'crawled_at': datetime.now().isoformat(),
                    'date': date
                })

            if meetings:
                break

        # 리스트 항목에서도 추출 시도
        if not meetings:
            list_items = await page.query_selector_all('ul li a, ol li a, .list a, .board-list a')
            for item in list_items[:20]:
                title = (await item.inner_text()).strip()
                if not title or len(title) < 3:
                    continue
                if not any(kw in title for kw in ['회의록', '본회의', '정례회', '임시회', '제']):
                    continue

                href = await item.get_attribute('href') or ''
                if href.startswith('javascript:'):
                    detail_url = ""
                else:
                    detail_url = urljoin(url, href)

                meetings.append({
                    'council_code': code,
                    'title': title,
                    'detail_url': detail_url,
                    'meeting_id': '',
                    'cells': [title],
                    'crawled_at': datetime.now().isoformat(),
                    'date': ''
                })

        return meetings[:15]
    except Exception as e:
        print(f"    오류: {str(e)[:50]}")
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

    pending = {k: v for k, v in URLS.items() if k not in completed}
    print(f"크롤링 대상: {len(pending)}개\n")

    if not pending:
        print("모든 의회 완료!")
        return

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )
    context = await browser.new_context(ignore_https_errors=True)

    success = 0
    results = []

    try:
        for code, config in pending.items():
            name = config['name']
            url = config['url']
            print(f"[{code}] {name}...", end=" ", flush=True)

            page = await context.new_page()
            try:
                meetings = await crawl_page(page, code, url)
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

            await asyncio.sleep(1.5)

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
