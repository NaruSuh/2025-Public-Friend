#!/usr/bin/env python3
"""
특정 의회들의 알려진 URL 패턴을 사용하여 크롤링
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

# 의회별 특수 URL 설정
COUNCIL_URLS = {
    # 강릉 - 영상 회의록 시스템 (cast)
    'gangneung': {
        'name': '강릉시의회',
        'urls': [
            'https://www.gncl.go.kr/kr/cast/main',
            'https://www.gncl.go.kr/kr/cast/plenary',
            'http://www.gncl.go.kr:8080/kr/minutes/late.do',
        ]
    },
    # 하남 - 회의록 시스템
    'hanam': {
        'name': '하남시의회',
        'urls': [
            'https://council.hanam.go.kr/assem/index.hanam',
            'https://council.hanam.go.kr/assem/index.hanam?menuCd=DOM_000000101000000000',
            'https://council.hanam.go.kr/kr/minutes/late.do',
        ]
    },
    # 금정구 - 부산 자치구
    'geumjeong': {
        'name': '금정구의회',
        'urls': [
            'https://council.geumjeong.go.kr/assem/index.geumj',
            'https://council.geumjeong.go.kr/kr/minutes/late.do',
        ]
    },
    # 전주 - CLRecords 시스템
    'jeonju': {
        'name': '전주시의회',
        'urls': [
            'https://council.jeonju.go.kr/source/korean/assembly/late.html',
            'https://council.jeonju.go.kr/source/kr/assembly/late.html',
            'https://council.jeonju.go.kr/CLRecords/',
        ]
    },
    # 남양주 - content/minutes 시스템
    'namyangju': {
        'name': '남양주시의회',
        'urls': [
            'https://www.nyjc.go.kr/content/minutes/recentMinutes.html',
            'https://www.nyjc.go.kr/content/minutes/meetingRetrieval.html',
            'https://www.nyjc.go.kr/minutes/',
        ]
    },
    # 아산
    'asan': {
        'name': '아산시의회',
        'urls': [
            'https://council.asan.go.kr/kr/minutes/late.do',
            'https://council.asan.go.kr/assem/index.asan',
            'https://council.asan.go.kr/source/korean/assembly/late.html',
        ]
    },
    # 서산
    'seosan': {
        'name': '서산시의회',
        'urls': [
            'https://council.seosan.go.kr/kr/minutes/late.do',
            'https://council.seosan.go.kr/assem/index.seosan',
        ]
    },
    # 정읍
    'jeongeup': {
        'name': '정읍시의회',
        'urls': [
            'https://council.jeongeup.go.kr/kr/minutes/late.do',
            'https://council.jeongeup.go.kr/source/korean/assembly/late.html',
        ]
    },
    # 부산 중구
    'jung_busan': {
        'name': '부산 중구의회',
        'urls': [
            'https://www.bsjunggu.go.kr/assembly/index.junggu',
            'https://www.bsjunggu.go.kr/kr/minutes/late.do',
            'https://council.junggu.busan.kr/',
        ]
    },
    # 부산 강서구
    'gangseo_busan': {
        'name': '부산 강서구의회',
        'urls': [
            'https://bsgangseo.go.kr/assembly/',
            'https://council.bsgangseo.go.kr/',
            'https://bsgangseo.go.kr/kr/minutes/late.do',
        ]
    },
    # 대구 중구
    'jung_daegu': {
        'name': '대구 중구의회',
        'urls': [
            'https://www.junggucouncil.daegu.kr/kr/minutes/late.do',
            'https://www.junggucouncil.daegu.kr/assem/',
        ]
    },
    # 광주 남구
    'nam_gwangju': {
        'name': '광주 남구의회',
        'urls': [
            'http://www.gjnc.or.kr/kr/minutes/late.do',
            'http://www.gjnc.or.kr/assem/',
        ]
    },
    # 광주 북구
    'buk_gwangju': {
        'name': '광주 북구의회',
        'urls': [
            'https://council.bukgu.gwangju.kr/kr/minutes/late.do',
            'https://council.bukgu.gwangju.kr/assem/',
        ]
    },
    # 광산구
    'gwangsan': {
        'name': '광산구의회',
        'urls': [
            'https://gjgc.or.kr/kr/minutes/late.do',
            'https://gjgc.or.kr/assem/',
        ]
    },
    # 양주
    'yangju': {
        'name': '양주시의회',
        'urls': [
            'http://mss.yjcc.gyeonggi.kr/kr/minutes/late.do',
            'https://council.yangju.go.kr/',
        ]
    },
    # 횡성
    'hoengseong': {
        'name': '횡성군의회',
        'urls': [
            'https://hsg.go.kr/council/kr/minutes/late.do',
            'https://council.hsg.go.kr/',
        ]
    },
    # 영월
    'yeongwol': {
        'name': '영월군의회',
        'urls': [
            'https://council.yw.go.kr/kr/minutes/late.do',
            'https://council.yw.go.kr/assem/',
        ]
    },
    # 철원
    'cheorwon': {
        'name': '철원군의회',
        'urls': [
            'https://council.cwg.go.kr/kr/minutes/late.do',
        ]
    },
    # 양구
    'yanggu': {
        'name': '양구군의회',
        'urls': [
            'https://council.yanggu.go.kr/kr/minutes/late.do',
        ]
    },
    # 고성(강원)
    'goseong_gw': {
        'name': '고성군의회',
        'urls': [
            'https://gwcouncil.gwgs.go.kr/kr/minutes/late.do',
        ]
    },
    # 태안
    'taean': {
        'name': '태안군의회',
        'urls': [
            'https://council.taean.go.kr/kr/minutes/late.do',
        ]
    },
    # 완주
    'wanju': {
        'name': '완주군의회',
        'urls': [
            'https://council.wanju.go.kr/kr/minutes/late.do',
            'https://council.wanju.go.kr/source/korean/assembly/late.html',
        ]
    },
    # 무주
    'muju': {
        'name': '무주군의회',
        'urls': [
            'https://council.muju.go.kr/kr/minutes/late.do',
        ]
    },
    # 임실
    'imsil': {
        'name': '임실군의회',
        'urls': [
            'https://council.imsil.go.kr/kr/minutes/late.do',
        ]
    },
    # 순창
    'sunchang': {
        'name': '순창군의회',
        'urls': [
            'https://www.sunchangcouncil.go.kr:8080/kr/minutes/late.do',
        ]
    },
    # 고창
    'gochang': {
        'name': '고창군의회',
        'urls': [
            'https://assembly.gochang.go.kr/kr/minutes/late.do',
        ]
    },
    # 부안
    'buan': {
        'name': '부안군의회',
        'urls': [
            'https://assembly.buan.go.kr/kr/minutes/late.do',
        ]
    },
    # 담양
    'damyang': {
        'name': '담양군의회',
        'urls': [
            'http://dycouncil.go.kr/kr/minutes/late.do',
        ]
    },
    # 곡성
    'gokseong': {
        'name': '곡성군의회',
        'urls': [
            'https://assembly.gokseong.go.kr/kr/minutes/late.do',
        ]
    },
    # 구례
    'gurye': {
        'name': '구례군의회',
        'urls': [
            'https://www.gurye.go.kr/council/kr/minutes/late.do',
            'https://council.gurye.go.kr/',
        ]
    },
    # 고흥
    'goheung': {
        'name': '고흥군의회',
        'urls': [
            'https://council.goheung.go.kr:8088/kr/minutes/late.do',
        ]
    },
    # 보성
    'boseong': {
        'name': '보성군의회',
        'urls': [
            'https://assembly.boseong.go.kr/kr/minutes/late.do',
        ]
    },
    # 장흥
    'jangheung': {
        'name': '장흥군의회',
        'urls': [
            'https://www.jhc.go.kr/kr/minutes/late.do',
        ]
    },
    # 강진
    'gangjin': {
        'name': '강진군의회',
        'urls': [
            'https://gangjincl.go.kr:8070/kr/minutes/late.do',
        ]
    },
    # 무안
    'muan': {
        'name': '무안군의회',
        'urls': [
            'http://www.muan.or.kr/kr/minutes/late.do',
        ]
    },
    # 영광
    'yeonggwang': {
        'name': '영광군의회',
        'urls': [
            'https://www.ygcouncil.go.kr/kr/minutes/late.do',
        ]
    },
    # 완도
    'wando': {
        'name': '완도군의회',
        'urls': [
            'http://www.wdcc.or.kr:8088/kr/minutes/late.do',
        ]
    },
    # 진도
    'jindo': {
        'name': '진도군의회',
        'urls': [
            'https://www.jindo.go.kr/council/kr/minutes/late.do',
            'https://council.jindo.go.kr/',
        ]
    },
    # 신안
    'sinan': {
        'name': '신안군의회',
        'urls': [
            'https://council.shinan.go.kr/kr/minutes/late.do',
        ]
    },
    # 청송
    'cheongsong': {
        'name': '청송군의회',
        'urls': [
            'https://council.cs.go.kr/kr/minutes/late.do',
        ]
    },
    # 영양
    'yeongyang': {
        'name': '영양군의회',
        'urls': [
            'https://council.yyg.go.kr/kr/minutes/late.do',
        ]
    },
    # 성주
    'seongju': {
        'name': '성주군의회',
        'urls': [
            'https://tv.sjcouncil.go.kr/kr/minutes/late.do',
            'https://sjcouncil.go.kr/',
        ]
    },
    # 칠곡
    'chilgok': {
        'name': '칠곡군의회',
        'urls': [
            'https://council.chilgok.go.kr/kr/minutes/late.do',
        ]
    },
    # 봉화
    'bonghwa': {
        'name': '봉화군의회',
        'urls': [
            'https://www.bonghwa.go.kr/council/kr/minutes/late.do',
            'https://council.bonghwa.go.kr/',
        ]
    },
    # 울릉
    'ulleung': {
        'name': '울릉군의회',
        'urls': [
            'https://www.ulleung.go.kr/council/kr/minutes/late.do',
            'https://council.ulleung.go.kr/',
        ]
    },
    # 하동
    'hadong': {
        'name': '하동군의회',
        'urls': [
            'https://www.hdcl.go.kr/kr/minutes/late.do',
        ]
    },
    # 합천
    'hapcheon': {
        'name': '합천군의회',
        'urls': [
            'https://www.hccl.go.kr/kr/minutes/late.do',
        ]
    },
}

async def crawl_meetings(page, code, url):
    """회의록 크롤링"""
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)  # 동적 콘텐츠 로딩 대기

        content = await page.content()

        # 회의록 관련 키워드 확인
        keywords = ['회의록', '의사일정', '본회의', '위원회', '정례회', '임시회', '회기']
        has_keyword = any(kw in content for kw in keywords)

        if not has_keyword:
            return []

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

                # 제목에 회의 관련 키워드가 있어야 함
                title_keywords = ['회', '본회의', '위원회', '정례', '임시', '제']
                if not any(kw in title for kw in title_keywords):
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
                    for key in ['uid', 'id', 'mntsId', 'MINTS_SN', 'schSn', 'no', 'seq', 'hfile', 'idx']:
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

async def process_council(browser, code, config):
    """단일 의회 처리"""
    page = await browser.new_page()
    name = config['name']
    urls = config['urls']

    try:
        for url in urls:
            try:
                print(f"  시도: {url}")
                meetings = await crawl_meetings(page, code, url)

                if meetings:
                    save_results(code, meetings)
                    return {'code': code, 'status': 'success', 'count': len(meetings), 'url': url}

            except Exception as e:
                print(f"  오류: {e}")

            await asyncio.sleep(0.5)

        return {'code': code, 'status': 'no_pattern', 'count': 0}

    finally:
        await page.close()

async def main():
    # 이미 완료된 의회 확인
    completed = set()
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith('.jsonl') and not f.startswith('_'):
            completed.add(f.replace('.jsonl', ''))

    # 미완료 의회만 필터링
    pending = {k: v for k, v in COUNCIL_URLS.items() if k not in completed}

    print(f"대상 의회: {len(pending)}개\n")

    if not pending:
        print("모든 의회가 완료되었습니다.")
        return

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )

    success = 0
    failed = []

    try:
        for code, config in pending.items():
            print(f"[{code}] {config['name']} 처리 중...")

            try:
                result = await process_council(browser, code, config)

                if result['status'] == 'success':
                    print(f"  ✅ {result['count']}건 수집 ({result.get('url', '')})")
                    success += 1
                else:
                    print(f"  ❌ {result['status']}")
                    failed.append({'code': code, 'reason': result['status']})
            except Exception as e:
                print(f"  ❌ 오류: {e}")
                failed.append({'code': code, 'reason': str(e)})

            await asyncio.sleep(1)

    finally:
        await browser.close()
        await playwright.stop()

    print(f"\n{'='*60}")
    print(f"완료: 성공 {success}개 / 실패 {len(failed)}개")

    if failed:
        print(f"\n실패 목록:")
        for f in failed:
            print(f"  - {f['code']}: {f['reason']}")

if __name__ == "__main__":
    asyncio.run(main())
