#!/usr/bin/env python3
"""
2단계: 웹 검색 기반 URL 복구
DNS 에러나 404 에러가 발생한 의회들의 실제 URL을 찾아 YAML 업데이트
"""

import json
import os
import re
import socket
import time
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class URLRecovery:
    """URL 복구 도구"""

    def __init__(self, yaml_path: str = "basic_councils.yaml", output_dir: str = "output/basic_minutes"):
        self.yaml_path = yaml_path
        self.output_dir = Path(output_dir)
        self.councils = self._load_councils()

        # HTTP 세션
        self.session = requests.Session()
        retry = Retry(total=2, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # 도메인 패턴 템플릿
        self.domain_templates = [
            "council.{city}.go.kr",
            "www.{city}council.go.kr",
            "{city}council.go.kr",
            "www.{city}c.go.kr",
            "{city}c.go.kr",
            "council.{city}.{region}.kr",
            "{city}.go.kr",
            "www.{city}.go.kr",
            "assembly.{city}.go.kr",
        ]

        # 회의록 URL 패턴
        self.list_url_patterns = [
            "/kr/minutes/late.do",
            "/kr/assembly/late.do",
            "/kr/assembly/late",
            "/viewer/minutes/list.do",
            "/source/korean/assembly/late.html",
            "/meeting/confer/recent.do",
        ]

    def _load_councils(self) -> Dict:
        """YAML에서 의회 정보 로드"""
        with open(self.yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        councils = {}
        for region, items in data.items():
            if isinstance(items, list):
                for c in items:
                    code = c.get('code')
                    if code:
                        councils[code] = c

        return councils

    def get_pending_councils(self) -> List[str]:
        """미완료 의회 목록"""
        completed = set()
        if self.output_dir.exists():
            for f in self.output_dir.iterdir():
                if f.suffix == '.jsonl' and f.stat().st_size > 10:
                    completed.add(f.stem)

        return [code for code in self.councils.keys() if code not in completed]

    def check_dns(self, domain: str) -> bool:
        """DNS 확인"""
        try:
            socket.gethostbyname(domain)
            return True
        except:
            return False

    def check_url(self, url: str) -> Tuple[bool, int, bool]:
        """URL 확인: (접근가능, 상태코드, 테이블존재)"""
        try:
            response = self.session.get(url, timeout=10, verify=False, allow_redirects=True)
            has_table = '<table' in response.text.lower()
            has_minutes = '회의록' in response.text or '의사일정' in response.text
            return True, response.status_code, has_table and has_minutes
        except:
            return False, 0, False

    def generate_domain_candidates(self, code: str, name: str) -> List[str]:
        """도메인 후보 생성"""
        candidates = []

        # 코드에서 도시명 추출 (예: jung_busan -> busan, geumjeong -> geumjeong)
        city = code.split('_')[-1] if '_' in code else code

        # 이름에서 지역 추출 (예: 중구의회 -> 중구)
        region = name.replace('의회', '').replace('시', '').replace('군', '').replace('구', '')

        for template in self.domain_templates:
            domain = template.format(city=city, region=region)
            candidates.append(f"https://{domain}")
            candidates.append(f"http://{domain}")

        # 특수 케이스 추가
        if 'busan' in code or '부산' in name:
            candidates.append(f"https://council.{city}.busan.kr")
            candidates.append(f"https://www.bs{city}.go.kr")
        if 'daegu' in code or '대구' in name:
            candidates.append(f"https://www.{city}council.daegu.kr")
        if 'gwangju' in code or '광주' in name:
            candidates.append(f"https://council.{city}.gwangju.kr")

        return list(set(candidates))

    def find_working_url(self, code: str) -> Optional[Tuple[str, str]]:
        """작동하는 URL 찾기"""
        config = self.councils.get(code, {})
        name = config.get('name', code)
        current_base = config.get('base_url', '')

        print(f"\n[{code}] {name} URL 탐색 중...")

        # 1. 현재 URL 확인
        if current_base:
            parsed = urlparse(current_base)
            if self.check_dns(parsed.hostname):
                for pattern in self.list_url_patterns:
                    url = current_base + pattern
                    accessible, status, valid = self.check_url(url)
                    if accessible and status == 200 and valid:
                        print(f"  ✓ 현재 URL 작동: {url}")
                        return current_base, pattern

        # 2. 도메인 후보 탐색
        candidates = self.generate_domain_candidates(code, name)

        for base_url in candidates:
            parsed = urlparse(base_url)
            if not self.check_dns(parsed.hostname):
                continue

            for pattern in self.list_url_patterns:
                url = base_url + pattern
                accessible, status, valid = self.check_url(url)

                if accessible and status == 200 and valid:
                    print(f"  ✓ 발견: {url}")
                    return base_url, pattern

            time.sleep(0.3)

        print(f"  ✗ 작동하는 URL 없음")
        return None

    def update_yaml(self, updates: Dict[str, Tuple[str, str]]):
        """YAML 파일 업데이트"""
        if not updates:
            print("업데이트할 내용 없음")
            return

        with open(self.yaml_path, 'r', encoding='utf-8') as f:
            content = f.read()

        for code, (base_url, list_url) in updates.items():
            config = self.councils.get(code, {})
            old_base = config.get('base_url', '')

            if old_base:
                # 기존 base_url 교체
                content = content.replace(
                    f"base_url: {old_base}",
                    f"base_url: {base_url}"
                )
            # list_url 업데이트는 수동으로 해야 함

        # 백업
        backup_path = self.yaml_path + ".backup"
        with open(backup_path, 'w', encoding='utf-8') as f:
            with open(self.yaml_path, 'r', encoding='utf-8') as orig:
                f.write(orig.read())

        # 저장
        with open(self.yaml_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"\n✓ YAML 업데이트 완료 (백업: {backup_path})")

    def diagnose_failures(self) -> Dict[str, List[str]]:
        """실패 의회 진단"""
        pending = self.get_pending_councils()

        diagnosis = {
            'dns_error': [],
            'http_error': [],
            'no_table': [],
            'accessible': []
        }

        print(f"미완료 의회 {len(pending)}개 진단 중...\n")

        for code in pending:
            config = self.councils.get(code, {})
            base_url = config.get('base_url', '')
            name = config.get('name', code)

            if not base_url:
                diagnosis['http_error'].append(code)
                continue

            parsed = urlparse(base_url)

            # DNS 체크
            if not self.check_dns(parsed.hostname):
                diagnosis['dns_error'].append(code)
                print(f"  {code}: DNS 에러")
                continue

            # HTTP 체크
            accessible, status, valid = self.check_url(base_url)
            if not accessible or status >= 400:
                diagnosis['http_error'].append(code)
                print(f"  {code}: HTTP {status}")
            elif not valid:
                diagnosis['no_table'].append(code)
                print(f"  {code}: 테이블 없음")
            else:
                diagnosis['accessible'].append(code)
                print(f"  {code}: 접근 가능 (크롤러 문제)")

            time.sleep(0.2)

        return diagnosis

    def run_recovery(self, limit: int = 0) -> Dict[str, Tuple[str, str]]:
        """URL 복구 실행"""
        pending = self.get_pending_councils()

        if limit > 0:
            pending = pending[:limit]

        print(f"URL 복구 대상: {len(pending)}개\n")

        updates = {}
        for code in pending:
            result = self.find_working_url(code)
            if result:
                base_url, list_url = result
                updates[code] = (base_url, list_url)
            time.sleep(0.5)

        return updates


def main():
    import argparse

    parser = argparse.ArgumentParser(description='URL 복구 도구')
    parser.add_argument('--yaml', default='basic_councils.yaml', help='YAML 설정')
    parser.add_argument('--output', default='output/basic_minutes', help='출력 디렉토리')
    parser.add_argument('--diagnose', action='store_true', help='실패 원인 진단')
    parser.add_argument('--recover', action='store_true', help='URL 복구 실행')
    parser.add_argument('--update', action='store_true', help='YAML 업데이트')
    parser.add_argument('--limit', type=int, default=0, help='최대 처리 수')

    args = parser.parse_args()

    recovery = URLRecovery(args.yaml, args.output)

    if args.diagnose:
        diagnosis = recovery.diagnose_failures()
        print(f"\n{'='*60}")
        print("진단 결과:")
        for category, codes in diagnosis.items():
            print(f"  {category}: {len(codes)}개")
        print(f"{'='*60}")

    if args.recover:
        updates = recovery.run_recovery(args.limit)
        print(f"\n발견된 URL: {len(updates)}개")

        if updates and args.update:
            recovery.update_yaml(updates)

        # 결과 저장
        result_path = Path(args.output) / "_url_recovery.json"
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'updates': {k: {'base_url': v[0], 'list_url': v[1]} for k, v in updates.items()}
            }, f, ensure_ascii=False, indent=2)
        print(f"결과 저장: {result_path}")


if __name__ == "__main__":
    main()
