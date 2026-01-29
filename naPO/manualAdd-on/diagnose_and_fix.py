#!/usr/bin/env python3
"""
미완료 의회 진단 및 해결 스크립트
1. DNS/HTTP 상태 진단
2. 다양한 URL 패턴 탐색
3. 크롤링 시도
"""

import asyncio
import json
import os
import re
import socket
import yaml
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs
import requests
from requests.exceptions import RequestException
from concurrent.futures import ThreadPoolExecutor

OUTPUT_DIR = "/home/naru/dev/Labgod/apps/naPO/manualAdd-on/output/basic_minutes"

# 다양한 도메인 패턴
DOMAIN_PATTERNS = [
    # 기본 패턴
    "council.{code}.go.kr",
    "www.{code}council.go.kr",
    "{code}council.go.kr",
    # 시/군청 통합 패턴
    "www.{code}.go.kr/council",
    "www.{code}.go.kr",
    # 특수 패턴
    "assembly.{code}.go.kr",
    "{code}cl.go.kr",
    "www.{code}cl.go.kr",
    # 광역시 자치구 패턴
    "council.{code}.busan.kr",
    "council.{code}.daegu.kr",
    "council.{code}.gwangju.kr",
    "{code}council.busan.kr",
    "{code}council.daegu.kr",
    "{code}council.gwangju.kr",
]

# URL 경로 패턴
PATH_PATTERNS = [
    "/kr/minutes/late.do",
    "/kr/assembly/late.do",
    "/source/korean/assembly/late.html",
    "/source/kr/assembly/late.html",
    "/council/kr/minutes/late.do",
    "/assem/index.{ext}",
    "/assem/user/assem/minute/latelyList.{ext}",
    "/viewer/minutes/list.do",
    "/minutes/",
    "/minutes/list.do",
]

def check_dns(domain):
    """DNS 확인"""
    try:
        socket.setdefaulttimeout(5)
        socket.gethostbyname(domain)
        return True
    except:
        return False

def check_url(url, timeout=10):
    """URL 접근성 및 회의록 테이블 확인"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(url, timeout=timeout, headers=headers, verify=False, allow_redirects=True)

        if resp.status_code != 200:
            return False, resp.status_code, "HTTP_ERROR"

        content = resp.text

        # 회의록 관련 키워드 확인
        keywords = ['회의록', '본회의', '위원회', '정례회', '임시회']
        has_keyword = any(kw in content for kw in keywords)

        # 테이블 확인
        has_table = '<table' in content.lower()

        # 링크 확인
        has_links = 'href=' in content and ('회의' in content or 'minute' in content.lower())

        if has_keyword and has_table and has_links:
            return True, 200, "OK"
        elif has_keyword:
            return False, 200, "NO_TABLE"
        else:
            return False, 200, "NO_CONTENT"

    except requests.exceptions.SSLError:
        return False, 0, "SSL_ERROR"
    except requests.exceptions.ConnectionError:
        return False, 0, "CONNECTION_ERROR"
    except requests.exceptions.Timeout:
        return False, 0, "TIMEOUT"
    except Exception as e:
        return False, 0, str(e)[:30]

def generate_urls(code, name, base_url):
    """가능한 URL 조합 생성"""
    urls = []

    # 기존 base_url 기반
    if base_url:
        parsed = urlparse(base_url)
        domain = parsed.netloc

        for path in PATH_PATTERNS:
            ext = code.split('_')[-1] if '_' in code else code
            path = path.replace('{ext}', ext)
            urls.append(f"https://{domain}{path}")
            urls.append(f"http://{domain}{path}")

    # 코드 기반 도메인 생성
    city_code = code.split('_')[-1] if '_' in code else code

    for domain_pattern in DOMAIN_PATTERNS:
        domain = domain_pattern.replace('{code}', city_code)
        for path in PATH_PATTERNS:
            ext = city_code
            path = path.replace('{ext}', ext)
            urls.append(f"https://{domain}{path}")
            urls.append(f"http://{domain}{path}")

    return list(set(urls))

def diagnose_council(code, config):
    """단일 의회 진단"""
    name = config.get('name', code)
    base_url = config.get('base_url', '')

    result = {
        'code': code,
        'name': name,
        'base_url': base_url,
        'status': 'unknown',
        'working_url': None,
        'issues': []
    }

    # 1. 기존 base_url DNS 확인
    if base_url:
        parsed = urlparse(base_url)
        domain = parsed.netloc

        if not check_dns(domain):
            result['issues'].append(f"DNS_FAIL: {domain}")
            result['status'] = 'dns_error'
        else:
            # HTTP 접근 확인
            accessible, status, reason = check_url(base_url)
            if not accessible:
                result['issues'].append(f"HTTP_{status}: {reason}")

    # 2. 다양한 URL 패턴 시도
    urls_to_try = generate_urls(code, name, base_url)

    for url in urls_to_try[:30]:  # 최대 30개까지 시도
        try:
            parsed = urlparse(url)
            if not check_dns(parsed.netloc):
                continue

            accessible, status, reason = check_url(url, timeout=8)
            if accessible:
                result['status'] = 'found'
                result['working_url'] = url
                return result
        except:
            continue

    if result['status'] == 'unknown':
        result['status'] = 'not_found'

    return result

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

    return {k: v for k, v in all_councils.items() if k not in completed}

def main():
    import warnings
    warnings.filterwarnings('ignore')

    pending = load_pending_councils()
    print(f"미완료 의회: {len(pending)}개\n")
    print("="*70)

    results = {
        'found': [],
        'dns_error': [],
        'not_found': []
    }

    for code, config in pending.items():
        name = config.get('name', code)
        print(f"[{code}] {name} 진단 중...", end=" ", flush=True)

        result = diagnose_council(code, config)

        if result['status'] == 'found':
            print(f"✅ 발견: {result['working_url']}")
            results['found'].append(result)
        elif result['status'] == 'dns_error':
            print(f"❌ DNS 오류")
            results['dns_error'].append(result)
        else:
            print(f"❌ URL 미발견")
            results['not_found'].append(result)

    print("\n" + "="*70)
    print(f"진단 결과:")
    print(f"  - 작동 URL 발견: {len(results['found'])}개")
    print(f"  - DNS 오류: {len(results['dns_error'])}개")
    print(f"  - URL 미발견: {len(results['not_found'])}개")

    # 결과 저장
    with open(os.path.join(OUTPUT_DIR, '_diagnosis.json'), 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results
        }, f, ensure_ascii=False, indent=2)

    # 발견된 URL 출력
    if results['found']:
        print("\n발견된 URL:")
        for r in results['found']:
            print(f"  {r['code']}: {r['working_url']}")

    return results

if __name__ == "__main__":
    main()
