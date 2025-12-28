#!/usr/bin/env python3
"""
Playwright 기반 배치 크롤링 - 남은 의회들의 다양한 URL 패턴 탐색
"""

import asyncio
import json
import os
import re
import yaml
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs

from playwright.async_api import async_playwright

OUTPUT_DIR = "/home/naru/skyimpact/Labgod/apps/naPO/manualAdd-on/output/basic_minutes"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 더 많은 URL 패턴 추가
URL_PATTERNS = [
    # 표준 패턴
    "/kr/minutes/late.do",
    "/kr/assembly/late.do",
    "/kr/assembly/late.html",
    "/kr/source/pages/late.do",

    # source 패턴 (전주 등)
    "/source/korean/assembly/late.html",
    "/source/korean/assembly/late.do",
    "/source/korean/minutes/late.html",
    "/source/korean/minutes/late.do",
    "/source/kr/assembly/late.html",
    "/source/kr/minutes/late.html",

    # 남양주 스타일
    "/content/minutes/meetingRetrieval.html",
    "/content/minutes/recentMinutes.html",
    "/content/minutes/list.html",

    # viewer 패턴
    "/viewer/minutes/list.do",
    "/viewer/minutes.do",
    "/viewer/late.do",

    # meeting 패턴
    "/meeting/confer/recent.do",
    "/meeting/minutes/late.do",
    "/meeting/minutes/list.do",

    # 단순 패턴
    "/minutes/",
    "/minutes/list.do",
    "/minutes/late.do",
    "/minutes/recent.do",
    "/assembly/late.do",
    "/assembly/minutes.do",
    "/assembly/late.html",
    "/assembly/record.do",

    # 기타 패턴
    "/promote/minutes/search.do",
    "/bbs/board.php?bo_table=minutes",
    "/bbs/board.php?bo_table=minute",
    "/board.php?bo_table=minute",

    # 인덱스 패턴
    "/index.php?bo_table=minute",
    "/bbs/minute/",

    # CLRecords 패턴 (전주 스타일)
    "/CLRecords/",
]

async def check_page_has_minutes(page, url, timeout=15000):
    """페이지에 회의록 테이블이 있는지 확인"""
    try:
        await page.goto(url, wait_until="networkidle", timeout=timeout)
        await asyncio.sleep(2)  # 동적 콘텐츠 로딩 대기

        content = await page.content()

        # 회의록 관련 키워드 확인
        keywords = ['회의록', '의사일정', '본회의', '위원회', '정례회', '임시회']
        has_keyword = any(kw in content for kw in keywords)

        if not has_keyword:
            return False, 0, []

        # 테이블 row 수 확인
        rows = await page.query_selector_all('table tbody tr, table tr')
        if len(rows) < 2:
            return False, 0, []

        # 링크가 있는 행 확인
        links = await page.query_selector_all('table a[href]')
        if not links:
            return False, 0, []

        return True, len(rows), []

    except Exception as e:
        return False, 0, [str(e)]

async def crawl_meetings(page, code, url):
    """회의록 크롤링"""
    try:
        await page.goto(url, wait_until="networkidle", timeout=20000)
        await asyncio.sleep(2)

        meetings = []

        # 테이블 찾기
        tables = await page.query_selector_all('table')

        for table in tables:
            rows = await table.query_selector_all('tbody tr')
            if not rows:
                rows = await table.query_selector_all('tr')

            for row in rows:
                cells = await row.query_selector_all('td')
                if len(cells) < 2:
                    continue

                # 링크 찾기
                link = await row.query_selector('a[href]')
                if not link:
                    continue

                title = await link.inner_text()
                title = title.strip()

                if not title or len(title) < 3:
                    continue

                href = await link.get_attribute('href') or ''

                # 상세 URL 생성
                if href.startswith('javascript:'):
                    match = re.search(r"['\"]([^'\"]+)['\"]", href)
                    meeting_id = match.group(1) if match else ""
                    detail_url = ""
                else:
                    detail_url = urljoin(url, href)
                    parsed = urlparse(detail_url)
                    params = parse_qs(parsed.query)
                    meeting_id = ""
                    for key in ['uid', 'id', 'mntsId', 'MINTS_SN', 'schSn', 'no', 'seq', 'hfile']:
                        if key in params:
                            meeting_id = params[key][0]
                            break

                # 셀 텍스트 추출
                cell_texts = []
                for cell in cells:
                    text = await cell.inner_text()
                    cell_texts.append(text.strip())

                # 날짜 추출
                date = ""
                for text in cell_texts:
                    if re.match(r'\d{4}[-./]\d{1,2}[-./]\d{1,2}', text):
                        date = text
                        break

                meeting = {
                    'council_code': code,
                    'title': title,
                    'detail_url': detail_url,
                    'meeting_id': meeting_id,
                    'cells': cell_texts,
                    'crawled_at': datetime.now().isoformat(),
                    'date': date
                }
                meetings.append(meeting)

            # 유효한 데이터가 있으면 첫 테이블만 사용
            if meetings:
                break

        return meetings
    except Exception as e:
        print(f"  [{code}] 크롤링 오류: {e}")
        return []

def save_results(code, meetings):
    """결과 저장"""
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

def load_pending_councils():
    """미완료 의회 로드"""
    with open('basic_councils.yaml', 'r') as f:
        data = yaml.safe_load(f)

    all_councils = {}
    for region, items in data.items():
        if isinstance(items, list):
            for c in items:
                if 'code' in c:
                    all_councils[c['code']] = c

    completed = set()
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith('.jsonl') and not f.startswith('_'):
            completed.add(f.replace('.jsonl', ''))

    pending = {k: v for k, v in all_councils.items() if k not in completed}
    return pending

async def process_council(browser, code, base_url):
    """단일 의회 처리"""
    page = await browser.new_page()

    try:
        # 모든 URL 패턴 시도
        for pattern in URL_PATTERNS:
            url = base_url.rstrip('/') + pattern

            try:
                valid, row_count, _ = await check_page_has_minutes(page, url)

                if valid and row_count >= 2:
                    print(f"  [{code}] 발견: {pattern} ({row_count}행)")

                    # 크롤링
                    meetings = await crawl_meetings(page, code, url)

                    if meetings:
                        save_results(code, meetings)
                        return {'code': code, 'status': 'success', 'count': len(meetings), 'url': url}

            except Exception:
                pass

            await asyncio.sleep(0.3)

        return {'code': code, 'status': 'no_pattern', 'count': 0}

    finally:
        await page.close()

async def main():
    pending = load_pending_councils()
    print(f"미완료 의회: {len(pending)}개\n")

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )

    success = 0
    failed = []

    try:
        for code, config in pending.items():
            base_url = config.get('base_url', '')
            name = config.get('name', code)

            if not base_url:
                print(f"[{code}] {name}: base_url 없음")
                failed.append({'code': code, 'reason': 'no_base_url'})
                continue

            print(f"[{code}] {name} 처리 중... ({base_url})")

            try:
                result = await process_council(browser, code, base_url)

                if result['status'] == 'success':
                    print(f"  ✅ {result['count']}건 수집")
                    success += 1
                else:
                    print(f"  ❌ {result['status']}")
                    failed.append({'code': code, 'reason': result['status']})
            except Exception as e:
                print(f"  ❌ 오류: {e}")
                failed.append({'code': code, 'reason': str(e)})

            await asyncio.sleep(0.5)

    finally:
        await browser.close()
        await playwright.stop()

    print(f"\n{'='*60}")
    print(f"완료: 성공 {success}개 / 실패 {len(failed)}개")

    if failed:
        print(f"\n실패 목록:")
        for f in failed:
            print(f"  - {f['code']}: {f['reason']}")

    # 결과 저장
    with open(os.path.join(OUTPUT_DIR, '_playwright_batch.json'), 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'failed': failed
        }, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
