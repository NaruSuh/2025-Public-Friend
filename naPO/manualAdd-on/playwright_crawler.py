#!/usr/bin/env python3
"""
Playwright 기반 회의록 크롤러
JavaScript 렌더링이 필요한 의회 사이트 처리
"""

import asyncio
import json
import os
import re
import yaml
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse, parse_qs

from playwright.async_api import async_playwright, Page, Browser


class PlaywrightCouncilCrawler:
    """Playwright 기반 의회 크롤러"""

    def __init__(self, output_dir: str = "output/basic_minutes"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.browser: Optional[Browser] = None

    async def init_browser(self):
        """브라우저 초기화"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

    async def close_browser(self):
        """브라우저 종료"""
        if self.browser:
            await self.browser.close()

    async def get_page_content(self, url: str, wait_selector: str = "table", timeout: int = 30000) -> str:
        """페이지 내용 가져오기"""
        page = await self.browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=timeout)

            # 테이블이 렌더링될 때까지 대기
            try:
                await page.wait_for_selector(wait_selector, timeout=10000)
            except:
                pass

            # 추가 대기 (동적 콘텐츠 로딩)
            await asyncio.sleep(2)

            content = await page.content()
            return content
        finally:
            await page.close()

    async def crawl_council(self, code: str, base_url: str, list_url: str, max_pages: int = 2) -> List[Dict[str, Any]]:
        """의회 크롤링"""
        from bs4 import BeautifulSoup

        all_meetings = []
        full_url = base_url + list_url

        print(f"[{code}] 크롤링 시작: {full_url}")

        try:
            content = await self.get_page_content(full_url)
            soup = BeautifulSoup(content, 'html.parser')

            # 테이블 찾기
            tables = soup.select('table')
            if not tables:
                print(f"[{code}] 테이블 없음")
                return []

            # 데이터 행 추출
            for table in tables:
                rows = table.select('tbody tr') or table.select('tr')

                for row in rows:
                    cells = row.select('td')
                    if len(cells) < 2:
                        continue

                    # 링크 찾기
                    link = row.select_one('a[href]')
                    onclick = row.get('onclick', '') or (link.get('onclick', '') if link else '')

                    # 유효한 링크/onclick 확인
                    detail_url = None
                    meeting_id = None

                    if link:
                        href = link.get('href', '')
                        if href and href != '#' and not href.startswith('javascript:void'):
                            if href.startswith('javascript:'):
                                # JavaScript 함수에서 파라미터 추출
                                match = re.search(r"['\"]([^'\"]+)['\"]", href)
                                if match:
                                    meeting_id = match.group(1)
                            else:
                                detail_url = urljoin(full_url, href)
                                # URL에서 ID 추출
                                parsed = urlparse(detail_url)
                                params = parse_qs(parsed.query)
                                for key in ['uid', 'id', 'mntsId', 'MINTS_SN', 'schSn']:
                                    if key in params:
                                        meeting_id = params[key][0]
                                        break

                    if onclick:
                        # onclick에서 파라미터 추출
                        match = re.search(r"['\"]([a-zA-Z0-9]+)['\"]", onclick)
                        if match:
                            meeting_id = match.group(1)

                    if not detail_url and not meeting_id:
                        continue

                    # 회의 정보 추출
                    title = link.get_text(strip=True) if link else cells[0].get_text(strip=True)

                    meeting = {
                        'council_code': code,
                        'title': title,
                        'detail_url': detail_url or '',
                        'meeting_id': meeting_id or '',
                        'cells': [c.get_text(strip=True) for c in cells],
                        'crawled_at': datetime.now().isoformat(),
                    }

                    # 날짜 추출 시도
                    for cell in cells:
                        text = cell.get_text(strip=True)
                        if re.match(r'\d{4}[-./]\d{1,2}[-./]\d{1,2}', text):
                            meeting['date'] = text
                            break

                    all_meetings.append(meeting)

                # 첫 번째 유효한 테이블만 처리
                if all_meetings:
                    break

            print(f"[{code}] {len(all_meetings)}건 발견")

        except Exception as e:
            print(f"[{code}] 오류: {e}")

        return all_meetings

    def save_results(self, code: str, meetings: List[Dict[str, Any]]):
        """결과 저장"""
        if not meetings:
            return

        # JSONL 저장
        jsonl_path = os.path.join(self.output_dir, f"{code}.jsonl")
        with open(jsonl_path, 'w', encoding='utf-8') as f:
            for m in meetings:
                f.write(json.dumps(m, ensure_ascii=False) + '\n')

        # Markdown 저장
        md_path = os.path.join(self.output_dir, f"{code}.md")
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

        print(f"[{code}] 저장 완료: {jsonl_path}")


async def crawl_councils(councils: List[Dict[str, Any]], output_dir: str = "output/basic_minutes"):
    """여러 의회 크롤링"""
    crawler = PlaywrightCouncilCrawler(output_dir)
    await crawler.init_browser()

    try:
        for council in councils:
            code = council['code']
            base_url = council['base_url']
            list_url = council.get('list_url', '')

            meetings = await crawler.crawl_council(code, base_url, list_url)
            crawler.save_results(code, meetings)

            # 요청 간 딜레이
            await asyncio.sleep(1)

    finally:
        await crawler.close_browser()


def load_councils_from_yaml(yaml_path: str) -> Dict[str, Dict[str, Any]]:
    """YAML에서 의회 정보 로드"""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    councils = {}
    for region, items in data.items():
        if isinstance(items, list):
            for c in items:
                code = c.get('code')
                if code:
                    councils[code] = c

    return councils


async def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='Playwright 회의록 크롤러')
    parser.add_argument('--council', '-c', help='크롤링할 의회 코드')
    parser.add_argument('--yaml', default='basic_councils.yaml', help='YAML 설정 파일')
    parser.add_argument('--output', '-o', default='output/basic_minutes', help='출력 디렉토리')
    parser.add_argument('--all-js', action='store_true', help='JS_REQUIRED 의회 모두 크롤링')
    parser.add_argument('--all-needs-fix', action='store_true', help='NEEDS_FIX 의회 모두 크롤링')

    args = parser.parse_args()

    # 의회 정보 로드
    councils = load_councils_from_yaml(args.yaml)

    # 이미 완료된 의회 확인
    completed = set()
    if os.path.exists(args.output):
        for f in os.listdir(args.output):
            if f.endswith('.jsonl'):
                name = f.replace('.jsonl', '')
                if not name.startswith('_'):
                    path = os.path.join(args.output, f)
                    if os.path.getsize(path) > 10:
                        completed.add(name)

    to_crawl = []

    if args.council:
        # 특정 의회만
        if args.council in councils:
            to_crawl.append(councils[args.council])
        else:
            print(f"의회 코드 '{args.council}'를 찾을 수 없습니다.")
            return

    elif args.all_js:
        # JS_REQUIRED 의회들
        for code, c in councils.items():
            if code not in completed and 'JS' in c.get('note', ''):
                to_crawl.append(c)

    elif args.all_needs_fix:
        # NEEDS_FIX 의회들 (note가 없거나 특수 플래그가 없는 의회)
        skip_notes = ['WAF', 'JS', 'PORT', 'NO_MINUTES', 'EXTERNAL', 'SUBDOMAIN']
        for code, c in councils.items():
            if code not in completed:
                note = c.get('note', '')
                if not any(flag in note for flag in skip_notes):
                    to_crawl.append(c)

    else:
        print("--council, --all-js, 또는 --all-needs-fix 옵션을 지정하세요.")
        return

    if not to_crawl:
        print("크롤링할 의회가 없습니다.")
        return

    print(f"크롤링 대상: {len(to_crawl)}개 의회")

    await crawl_councils(to_crawl, args.output)

    # 결과 요약
    new_completed = 0
    for c in to_crawl:
        jsonl_path = os.path.join(args.output, f"{c['code']}.jsonl")
        if os.path.exists(jsonl_path) and os.path.getsize(jsonl_path) > 10:
            new_completed += 1

    print(f"\n완료: {new_completed}/{len(to_crawl)}개 의회")


if __name__ == "__main__":
    asyncio.run(main())
