#!/usr/bin/env python3
"""
Playwright Fallback 통합 크롤러
1단계: requests 기반 크롤링 시도
2단계: 실패 시 Playwright로 재시도
+ 실패 사유 상세 분류
"""

import asyncio
import json
import os
import re
import socket
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs
import hashlib

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup

# SSL 경고 무시
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Playwright import (선택적)
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️ Playwright 미설치 - requests만 사용")


class FailureReason:
    """실패 사유 분류"""
    DNS_ERROR = "dns_error"
    HTTP_404 = "http_404"
    HTTP_403 = "http_403"
    HTTP_5XX = "http_5xx"
    TIMEOUT = "timeout"
    SSL_ERROR = "ssl_error"
    CONNECTION_REFUSED = "connection_refused"
    NO_TABLE = "no_table"
    EMPTY_TABLE = "empty_table"
    NO_VALID_ROWS = "no_valid_rows"
    JS_REQUIRED = "js_required"
    PARSE_ERROR = "parse_error"
    UNKNOWN = "unknown"


class IntegratedCrawler:
    """통합 크롤러 (requests + Playwright fallback)"""

    def __init__(self, output_dir: str = "output/basic_minutes"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # requests 세션 설정
        self.session = requests.Session()
        retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        })

        # Playwright 브라우저 (지연 초기화)
        self.browser = None
        self.playwright = None

        # URL 패턴 후보
        self.url_patterns = [
            "/kr/minutes/late.do",
            "/kr/assembly/late.do",
            "/kr/assembly/late",
            "/kr/minutes/late",
            "/viewer/minutes/list.do",
            "/source/korean/assembly/late.html",
            "/meeting/confer/recent.do",
            "/svc/cms/mnts/MntsLatelyList.do",
            "/content/minutes/latelyMinutes.html",
            "/content/minutes/meetingRetrieval.html",
            "/minutes/ems/late.do",
        ]

    async def init_playwright(self):
        """Playwright 초기화"""
        if not PLAYWRIGHT_AVAILABLE:
            return False
        if self.browser:
            return True
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            return True
        except Exception as e:
            print(f"Playwright 초기화 실패: {e}")
            return False

    async def close_playwright(self):
        """Playwright 종료"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def check_dns(self, url: str) -> bool:
        """DNS 확인"""
        try:
            parsed = urlparse(url)
            socket.gethostbyname(parsed.hostname)
            return True
        except:
            return False

    def try_requests(self, url: str, timeout: int = 15) -> Tuple[Optional[str], str]:
        """requests로 페이지 가져오기"""
        try:
            if not self.check_dns(url):
                return None, FailureReason.DNS_ERROR

            response = self.session.get(url, timeout=timeout, verify=False, allow_redirects=True)

            if response.status_code == 404:
                return None, FailureReason.HTTP_404
            elif response.status_code == 403:
                return None, FailureReason.HTTP_403
            elif response.status_code >= 500:
                return None, FailureReason.HTTP_5XX
            elif response.status_code != 200:
                return None, f"http_{response.status_code}"

            return response.text, ""

        except requests.exceptions.Timeout:
            return None, FailureReason.TIMEOUT
        except requests.exceptions.SSLError:
            return None, FailureReason.SSL_ERROR
        except requests.exceptions.ConnectionError as e:
            if "Name or service not known" in str(e) or "getaddrinfo" in str(e):
                return None, FailureReason.DNS_ERROR
            return None, FailureReason.CONNECTION_REFUSED
        except Exception as e:
            return None, FailureReason.UNKNOWN

    async def try_playwright(self, url: str, timeout: int = 20000) -> Tuple[Optional[str], str]:
        """Playwright로 페이지 가져오기"""
        if not await self.init_playwright():
            return None, "playwright_unavailable"

        page = None
        try:
            page = await self.browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=timeout)

            # 테이블 렌더링 대기
            try:
                await page.wait_for_selector("table", timeout=10000)
            except:
                pass

            await asyncio.sleep(2)
            content = await page.content()
            return content, ""

        except Exception as e:
            error_str = str(e).lower()
            if "timeout" in error_str:
                return None, FailureReason.TIMEOUT
            elif "net::err_name_not_resolved" in error_str:
                return None, FailureReason.DNS_ERROR
            else:
                return None, FailureReason.UNKNOWN
        finally:
            if page:
                await page.close()

    def parse_meetings(self, html: str, code: str, base_url: str) -> Tuple[List[Dict], str]:
        """HTML에서 회의록 파싱"""
        soup = BeautifulSoup(html, 'html.parser')

        tables = soup.select('table')
        if not tables:
            # JS 렌더링이 필요할 수 있음
            if 'document.write' in html or 'createElement' in html:
                return [], FailureReason.JS_REQUIRED
            return [], FailureReason.NO_TABLE

        meetings = []

        for table in tables:
            rows = table.select('tbody tr')
            if not rows:
                rows = table.select('tr')

            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue

                cell_texts = [c.get_text(strip=True) for c in cells]

                # 링크 찾기
                link = row.find('a', href=True)
                detail_url = ""
                meeting_id = ""

                if link:
                    href = link.get('href', '')
                    onclick = link.get('onclick', '')

                    if href and not href.startswith(('#', 'javascript:void')):
                        if href.startswith('javascript:'):
                            match = re.search(r"['\"](\d+)['\"]", href)
                            if match:
                                meeting_id = match.group(1)
                        else:
                            detail_url = href if href.startswith('http') else urljoin(base_url, href)
                            # URL에서 ID 추출
                            for key in ['uid', 'schSn', 'MINTS_SN', 'id']:
                                match = re.search(rf'{key}=(\d+)', detail_url)
                                if match:
                                    meeting_id = match.group(1)
                                    break

                    if onclick and not meeting_id:
                        match = re.search(r"['\"](\d+)['\"]", onclick)
                        if match:
                            meeting_id = match.group(1)

                # 날짜 추출
                date = ""
                for text in cell_texts:
                    date_match = re.search(r'(\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2})', text)
                    if date_match:
                        date = date_match.group(1)
                        break

                if meeting_id or date:
                    # 중복 ID 방지
                    if not meeting_id:
                        meeting_id = hashlib.md5(''.join(cell_texts).encode()).hexdigest()[:12]

                    meetings.append({
                        'council_code': code,
                        'title': cell_texts[1] if len(cell_texts) > 1 else cell_texts[0],
                        'detail_url': detail_url,
                        'meeting_id': meeting_id,
                        'cells': cell_texts,
                        'crawled_at': datetime.now().isoformat(),
                        'date': date
                    })

            # 첫 번째 유효한 테이블에서 결과 있으면 종료
            if meetings:
                break

        if not meetings:
            return [], FailureReason.NO_VALID_ROWS

        return meetings, ""

    async def crawl_council(self, code: str, base_url: str, list_url: str = "") -> Dict[str, Any]:
        """단일 의회 크롤링 (fallback 포함)"""
        result = {
            'code': code,
            'status': 'unknown',
            'reason': '',
            'meetings': 0,
            'method': '',
            'url_used': ''
        }

        # URL 후보 생성
        urls_to_try = []
        if list_url:
            urls_to_try.append(base_url + list_url)
        for pattern in self.url_patterns:
            url = base_url + pattern
            if url not in urls_to_try:
                urls_to_try.append(url)

        # 1단계: requests로 시도
        for url in urls_to_try[:5]:  # 최대 5개 URL 시도
            html, error = self.try_requests(url)

            if html:
                meetings, parse_error = self.parse_meetings(html, code, base_url)
                if meetings:
                    self.save_results(code, meetings)
                    result['status'] = 'success'
                    result['meetings'] = len(meetings)
                    result['method'] = 'requests'
                    result['url_used'] = url
                    return result

                if parse_error == FailureReason.JS_REQUIRED:
                    # JS 필요 - Playwright로 시도
                    break

            if error == FailureReason.DNS_ERROR:
                # DNS 에러면 다른 URL 시도해도 의미 없음
                result['reason'] = FailureReason.DNS_ERROR
                break

        # 2단계: Playwright로 재시도
        if PLAYWRIGHT_AVAILABLE:
            for url in urls_to_try[:3]:
                html, error = await self.try_playwright(url)

                if html:
                    meetings, parse_error = self.parse_meetings(html, code, base_url)
                    if meetings:
                        self.save_results(code, meetings)
                        result['status'] = 'success'
                        result['meetings'] = len(meetings)
                        result['method'] = 'playwright'
                        result['url_used'] = url
                        return result

                if error == FailureReason.DNS_ERROR:
                    result['reason'] = FailureReason.DNS_ERROR
                    break

        # 실패
        if not result['reason']:
            result['reason'] = error or FailureReason.UNKNOWN
        result['status'] = 'fail'
        return result

    def save_results(self, code: str, meetings: List[Dict]):
        """결과 저장"""
        if not meetings:
            return

        # JSONL 저장
        jsonl_path = self.output_dir / f"{code}.jsonl"
        with open(jsonl_path, 'w', encoding='utf-8') as f:
            for m in meetings:
                f.write(json.dumps(m, ensure_ascii=False) + '\n')

        # Markdown 저장
        md_path = self.output_dir / f"{code}.md"
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


def load_councils_from_yaml(yaml_path: str = "basic_councils.yaml") -> Dict[str, Dict]:
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


def get_pending_councils(councils: Dict, output_dir: str) -> List[str]:
    """미완료 의회 목록"""
    completed = set()
    output_path = Path(output_dir)

    if output_path.exists():
        for f in output_path.iterdir():
            if f.suffix == '.jsonl' and f.stat().st_size > 10:
                completed.add(f.stem)

    return [code for code in councils.keys() if code not in completed]


async def main():
    import argparse

    parser = argparse.ArgumentParser(description='통합 크롤러 (requests + Playwright fallback)')
    parser.add_argument('--yaml', default='basic_councils.yaml', help='YAML 설정')
    parser.add_argument('--output', '-o', default='output/basic_minutes', help='출력 디렉토리')
    parser.add_argument('--council', '-c', help='특정 의회만 크롤링')
    parser.add_argument('--pending', action='store_true', help='미완료 의회만 크롤링')
    parser.add_argument('--limit', type=int, default=0, help='최대 크롤링 수')

    args = parser.parse_args()

    councils = load_councils_from_yaml(args.yaml)
    print(f"전체 의회: {len(councils)}개")

    # 크롤링 대상 선택
    if args.council:
        if args.council not in councils:
            print(f"의회 코드 '{args.council}' 없음")
            return
        to_crawl = [args.council]
    elif args.pending:
        to_crawl = get_pending_councils(councils, args.output)
    else:
        to_crawl = list(councils.keys())

    if args.limit > 0:
        to_crawl = to_crawl[:args.limit]

    print(f"크롤링 대상: {len(to_crawl)}개")

    # 크롤링 실행
    crawler = IntegratedCrawler(args.output)

    results = []
    success_count = 0

    for i, code in enumerate(to_crawl, 1):
        config = councils[code]
        base_url = config.get('base_url', '')
        list_url = config.get('list_url', '')
        name = config.get('name', code)

        result = await crawler.crawl_council(code, base_url, list_url)
        results.append(result)

        if result['status'] == 'success':
            success_count += 1
            print(f"[{i:3d}/{len(to_crawl)}] ✓ {name}: {result['meetings']}건 ({result['method']})")
        else:
            print(f"[{i:3d}/{len(to_crawl)}] ✗ {name}: {result['reason']}")

    await crawler.close_playwright()

    # 결과 저장
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total': len(to_crawl),
        'success': success_count,
        'fail': len(to_crawl) - success_count,
        'results': results
    }

    summary_path = Path(args.output) / "_crawl_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # 실패 사유 통계
    failure_stats = {}
    for r in results:
        if r['status'] == 'fail':
            reason = r['reason']
            failure_stats[reason] = failure_stats.get(reason, 0) + 1

    print(f"\n{'='*60}")
    print(f"완료: {success_count}/{len(to_crawl)} ({success_count/len(to_crawl)*100:.1f}%)")

    if failure_stats:
        print(f"\n실패 사유 분석:")
        for reason, count in sorted(failure_stats.items(), key=lambda x: -x[1]):
            print(f"  {reason}: {count}개")

    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
