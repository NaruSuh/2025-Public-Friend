#!/usr/bin/env python3
"""
실제 발견된 URL로 크롤링
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

# 실제 발견된 URL들
REAL_URLS = {
    'yangju': {
        'name': '양주시의회',
        'base': 'http://yjccmss.yangju.go.kr',
        'path': '/content/minutesLately.html'
    },
    'seosan': {
        'name': '서산시의회',
        'base': 'https://lib.scc.go.kr',
        'path': '/minutes/cnts/minutesLately.html'
    },
    'asan': {
        'name': '아산시의회',
        'base': 'https://minutes.asansicouncil.go.kr',
        'path': '/mnts/asvr/cnts/mnt/mntsLately.html'
    },
    'namyangju': {
        'name': '남양주시의회',
        'base': 'https://www.nyjc.go.kr',
        'path': '/content/minutes/meetingRetrieval.html'
    },
    'hanam': {
        'name': '하남시의회',
        'base': 'https://council.hanam.go.kr',
        'path': '/content/minutes/latelyMinutes.html'
    },
}

async def crawl_page(page, code, url):
    """페이지 크롤링"""
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        content = await page.content()
        keywords = ['회의록', '본회의', '위원회', '정례회', '임시회']
        if not any(kw in content for kw in keywords):
            return []

        meetings = []
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
                    for key in ['uid', 'id', 'mntsId', 'schSn', 'sess_id', 'no', 'seq']:
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

        return meetings
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
    # 완료된 의회 확인
    completed = set()
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith('.jsonl') and not f.startswith('_'):
            completed.add(f.replace('.jsonl', ''))

    pending = {k: v for k, v in REAL_URLS.items() if k not in completed}
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
    failed = []

    try:
        for code, config in pending.items():
            name = config['name']
            url = config['base'] + config['path']
            print(f"[{code}] {name} ({url[:50]}...)...", end=" ", flush=True)

            page = await context.new_page()
            try:
                meetings = await crawl_page(page, code, url)
                if meetings:
                    save_results(code, meetings)
                    print(f"✅ {len(meetings)}건")
                    success += 1
                else:
                    print("❌ 데이터 없음")
                    failed.append(code)
            except Exception as e:
                print(f"❌ {str(e)[:30]}")
                failed.append(code)
            finally:
                await page.close()

            await asyncio.sleep(1)

    finally:
        await context.close()
        await browser.close()
        await playwright.stop()

    print(f"\n{'='*50}")
    print(f"성공: {success}개 / 실패: {len(failed)}개")

if __name__ == "__main__":
    asyncio.run(main())
