#!/usr/bin/env python3
"""
미완료 의회들의 올바른 URL을 탐색하고 크롤링하는 스크립트
"""

import json
import os
import re
import time
import yaml
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 출력 디렉토리
OUTPUT_DIR = "/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 스레드 안전 출력
print_lock = threading.Lock()
def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs, flush=True)

# 다양한 회의록 URL 패턴들
URL_PATTERNS = [
    "/kr/minutes/late.do",
    "/kr/assembly/late.do",
    "/kr/source/pages/late.do",
    "/source/korean/assembly/late.html",
    "/source/korean/assembly/late.do",
    "/source/korean/minutes/late.do",
    "/viewer/minutes/list.do",
    "/viewer/minutes.do",
    "/meeting/confer/recent.do",
    "/meeting/minutes/late.do",
    "/minutes/",
    "/minutes/list.do",
    "/promote/minutes/search.do",
    "/assembly/late.do",
    "/assembly/minutes.do",
    "/minutes/late.do",
    "/minutes/recent.do",
    "/council/minutes/",
    "/contents/minutes.do",
    "/contents/meeting.do",
    "/bbs/minutes/",
    "/bbs/board.php?bo_table=minutes",
    "/assembly/record.do",
    "/assembly/record/late.do",
    "/assembly/late.html",
]

def create_session():
    """세션 생성"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
    })
    return session

def check_url_has_table(session, url, timeout=15):
    """URL이 회의록 테이블을 포함하는지 확인"""
    try:
        resp = session.get(url, timeout=timeout, verify=False, allow_redirects=True)
        if resp.status_code != 200:
            return False, 0, ""

        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')

        # 회의록 관련 키워드
        keywords = ['회의록', '의사일정', '본회의', '위원회', '회의', '제\d+회', '제\d+차']
        has_keyword = any(kw in html for kw in keywords[:4]) or bool(re.search(r'제\d+[회차]', html))

        # 테이블 확인
        tables = soup.select('table')
        has_table = len(tables) > 0

        # 행 수 확인
        if tables:
            for table in tables:
                rows = table.select('tbody tr') or table.select('tr')
                if len(rows) >= 2:
                    # 링크 있는지 확인
                    links = table.select('a[href]')
                    if links and has_keyword:
                        return True, len(rows), url

        return has_keyword and has_table, 0, url
    except Exception as e:
        return False, 0, str(e)

def find_minutes_url(base_url, session):
    """회의록 URL 패턴 찾기"""
    results = []

    for pattern in URL_PATTERNS:
        url = base_url.rstrip('/') + pattern
        try:
            valid, row_count, info = check_url_has_table(session, url, timeout=10)
            if valid and row_count >= 2:
                results.append({
                    'url': url,
                    'pattern': pattern,
                    'rows': row_count
                })
        except:
            pass
        time.sleep(0.2)

    return results

def crawl_from_url(code, url, session):
    """특정 URL에서 회의록 데이터 크롤링"""
    try:
        resp = session.get(url, timeout=20, verify=False, allow_redirects=True)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, 'html.parser')
        meetings = []

        tables = soup.select('table')
        for table in tables:
            rows = table.select('tbody tr') or table.select('tr')

            for row in rows:
                cells = row.select('td')
                if len(cells) < 2:
                    continue

                link = row.select_one('a[href]')
                if not link:
                    continue

                href = link.get('href', '')
                title = link.get_text(strip=True)

                if not title or len(title) < 3:
                    continue

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
                    for key in ['uid', 'id', 'mntsId', 'MINTS_SN', 'schSn', 'no', 'seq']:
                        if key in params:
                            meeting_id = params[key][0]
                            break

                # 날짜 추출
                date = ""
                for cell in cells:
                    text = cell.get_text(strip=True)
                    if re.match(r'\d{4}[-./]\d{1,2}[-./]\d{1,2}', text):
                        date = text
                        break

                meeting = {
                    'council_code': code,
                    'title': title,
                    'detail_url': detail_url,
                    'meeting_id': meeting_id,
                    'cells': [c.get_text(strip=True) for c in cells],
                    'crawled_at': datetime.now().isoformat(),
                    'date': date
                }
                meetings.append(meeting)

            # 유효한 데이터가 있으면 첫 테이블만 사용
            if meetings:
                break

        return meetings
    except Exception as e:
        safe_print(f"  [{code}] 크롤링 오류: {e}")
        return []

def save_results(code, meetings):
    """결과 저장"""
    if not meetings:
        return False

    jsonl_path = os.path.join(OUTPUT_DIR, f"{code}.jsonl")
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for m in meetings:
            f.write(json.dumps(m, ensure_ascii=False) + '\n')

    # MD 저장
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

def process_council(code, base_url):
    """단일 의회 처리"""
    session = create_session()

    # 1. URL 패턴 탐색
    results = find_minutes_url(base_url, session)

    if not results:
        return {'code': code, 'status': 'no_pattern', 'count': 0}

    # 2. 가장 많은 행을 가진 URL 선택
    best = max(results, key=lambda x: x['rows'])

    # 3. 크롤링
    meetings = crawl_from_url(code, best['url'], session)

    if meetings:
        save_results(code, meetings)
        return {'code': code, 'status': 'success', 'count': len(meetings), 'url': best['url']}

    return {'code': code, 'status': 'no_data', 'count': 0, 'url': best['url']}

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

    # 완료된 의회
    completed = set()
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith('.jsonl') and not f.startswith('_'):
            completed.add(f.replace('.jsonl', ''))

    pending = {k: v for k, v in all_councils.items() if k not in completed}
    return pending

def main():
    import warnings
    warnings.filterwarnings('ignore')

    pending = load_pending_councils()
    print(f"미완료 의회: {len(pending)}개\n")

    success = 0
    failed = []

    for code, config in pending.items():
        base_url = config.get('base_url', '')
        name = config.get('name', code)

        if not base_url:
            safe_print(f"[{code}] {name}: base_url 없음")
            failed.append({'code': code, 'reason': 'no_base_url'})
            continue

        safe_print(f"[{code}] {name} 처리 중... ({base_url})")

        try:
            result = process_council(code, base_url)

            if result['status'] == 'success':
                safe_print(f"  ✅ {result['count']}건 수집 ({result.get('url', '')})")
                success += 1
            else:
                safe_print(f"  ❌ {result['status']}")
                failed.append({'code': code, 'reason': result['status']})
        except Exception as e:
            safe_print(f"  ❌ 오류: {e}")
            failed.append({'code': code, 'reason': str(e)})

        time.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"완료: 성공 {success}개 / 실패 {len(failed)}개")

    if failed:
        print(f"\n실패 목록:")
        for f in failed:
            print(f"  - {f['code']}: {f['reason']}")

    # 결과 저장
    with open(os.path.join(OUTPUT_DIR, '_batch_discovery.json'), 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'failed': failed
        }, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
