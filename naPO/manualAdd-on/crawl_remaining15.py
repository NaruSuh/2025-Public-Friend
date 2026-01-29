#!/usr/bin/env python3
"""
최종 15개 의회 - 정확한 URL로 크롤링
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

URLS = {
    # 양구군의회 - 회의록 검색
    'yanggu': {
        'name': '양구군의회',
        'url': 'http://www.ygcl.go.kr/portal/F10000/F10300/F10303/html'
    },
    # 완주군의회 - council 서브도메인
    'wanju': {
        'name': '완주군의회',
        'url': 'https://council.wanju.go.kr/board/detail?depth_2=19&b_idx=5625&pageNum=1'
    },
    # 영광군의회 - 회의록 검색 시스템
    'yeonggwang': {
        'name': '영광군의회',
        'url': 'https://ygcouncil.go.kr/assem/'
    },
    # 합천군의회 - gpki 서브도메인
    'hapcheon': {
        'name': '합천군의회',
        'url': 'https://gpki.hc.go.kr/CLRecords/MRetrieval2/index.jsp'
    },
    # 봉화군의회 - 회의록 검색
    'bonghwa': {
        'name': '봉화군의회',
        'url': 'https://www.bonghwa.go.kr/open.content/council/proceedings/congressional.record/'
    },
    # 울릉군의회
    'ulleung': {
        'name': '울릉군의회',
        'url': 'https://www.ulleung.go.kr/council/page.do?mnu_uid=904'
    },
    # 남양주시의회 - SvcMntsList
    'namyangju': {
        'name': '남양주시의회',
        'url': 'https://www.nyjc.go.kr/minutes/svc/web/cms/mnts/SvcMntsLatelyList.php'
    },
    # 강릉시의회 - 전자회의록
    'gangneung': {
        'name': '강릉시의회',
        'url': 'http://sys.gncl.go.kr/kr/assembly/late.do'
    },
    # 부산 강서구의회
    'gangseo_busan': {
        'name': '부산 강서구의회',
        'url': 'https://www.bsgangseo.go.kr/council/main.do'
    },
    # 광산구의회
    'gwangsan': {
        'name': '광주 광산구의회',
        'url': 'https://gjgc.or.kr/ko/html/menu2/0203.html'
    },
    # 정읍시의회
    'jeongeup': {
        'name': '정읍시의회',
        'url': 'https://jcc.or.kr/confer/index.php'
    },
    # 진도군의회
    'jindo': {
        'name': '진도군의회',
        'url': 'https://www.jindo.go.kr/council/sub.cs?m=14'
    },
    # 성주군의회 - 회의록 목록
    'seongju': {
        'name': '성주군의회',
        'url': 'https://www.sjcouncil.go.kr/mnts/cnts/mnt/mntsLatelyList.php'
    },
    # 칠곡군의회
    'chilgok': {
        'name': '칠곡군의회',
        'url': 'https://www.chilgok.go.kr/council/main.do'
    },
    # 하동군의회 - 최근 회의록
    'hadong': {
        'name': '하동군의회',
        'url': 'https://www.hdcl.go.kr/source/korean/minutes/late.do'
    },
}

async def crawl_page(page, code, url):
    try:
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(4)

        content = await page.content()
        keywords = ['회의록', '본회의', '위원회', '정례회', '임시회', '의안', '회기', '질문', '답변', '의정']
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
                if len(cells) < 1:
                    continue

                link = await row.query_selector('a[href]')
                if not link:
                    # 셀에서 텍스트만 추출
                    text = (await row.inner_text()).strip()
                    if any(kw in text for kw in ['회의록', '본회의', '정례회', '임시회', '제']):
                        meetings.append({
                            'council_code': code,
                            'title': text[:100],
                            'detail_url': url,
                            'meeting_id': '',
                            'cells': [text],
                            'crawled_at': datetime.now().isoformat(),
                            'date': ''
                        })
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
                    for key in ['uid', 'id', 'mntsId', 'schSn', 'sess_id', 'no', 'seq', 'board_key', 'minuteSid', 'dataSid', 'wr_id', 'i']:
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
            list_items = await page.query_selector_all('ul li a, ol li a, .list a, .board-list a, .minutes-list a, .tit a, .title a, dt a, dd a')
            for item in list_items[:30]:
                title = (await item.inner_text()).strip()
                if not title or len(title) < 3:
                    continue
                if not any(kw in title for kw in ['회의록', '본회의', '정례회', '임시회', '제', '위원회', '질문', '감사']):
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

        # div 또는 span에서 회의록 정보 추출
        if not meetings:
            divs = await page.query_selector_all('div.item, div.list-item, div.board-item, .confer-list div')
            for div in divs[:20]:
                text = (await div.inner_text()).strip()
                if any(kw in text for kw in ['회의록', '본회의', '정례회', '임시회', '제']):
                    link = await div.query_selector('a[href]')
                    detail_url = ""
                    if link:
                        href = await link.get_attribute('href') or ''
                        if not href.startswith('javascript:'):
                            detail_url = urljoin(url, href)

                    meetings.append({
                        'council_code': code,
                        'title': text[:100],
                        'detail_url': detail_url if detail_url else url,
                        'meeting_id': '',
                        'cells': [text],
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
    context = await browser.new_context(
        ignore_https_errors=True,
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    )

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
