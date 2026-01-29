#!/usr/bin/env python3
"""
수정된 URL로 크롤링
웹 검색으로 찾은 실제 작동하는 URL들
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

# 수정된 URL 매핑
CORRECTED_URLS = {
    # 아산 - 실제 URL은 asansicouncil
    'asan': {
        'name': '아산시의회',
        'urls': [
            'https://www.asansicouncil.go.kr/kr/minutes/late.do',
            'https://www.asansicouncil.go.kr/source/korean/assembly/late.html',
            'https://www.asansicouncil.go.kr/kr/assembly/late.do',
        ]
    },
    # 남양주
    'namyangju': {
        'name': '남양주시의회',
        'urls': [
            'https://www.nyjc.go.kr/minutes/svc/web/mnts/list.php',
            'https://www.nyjc.go.kr/minutes/svc/web/cms/mnts/SvcMntsList.php',
        ]
    },
    # 금정구 - council.geumjeong.go.kr
    'geumjeong': {
        'name': '금정구의회',
        'urls': [
            'https://council.geumjeong.go.kr/kr/minutes/late.do',
            'https://council.geumjeong.go.kr/assem/user/assem/minute/latelyList.geumj',
        ]
    },
    # 강릉
    'gangneung': {
        'name': '강릉시의회',
        'urls': [
            'https://www.gncl.go.kr/kr/minutes/late.do',
            'https://www.gncl.go.kr/source/korean/assembly/late.html',
        ]
    },
    # 하남
    'hanam': {
        'name': '하남시의회',
        'urls': [
            'https://council.hanam.go.kr/kr/minutes/late.do',
            'https://council.hanam.go.kr/assem/user/assem/minute/latelyList.hanam',
        ]
    },
    # 횡성
    'hoengseong': {
        'name': '횡성군의회',
        'urls': [
            'https://www.hsg.go.kr/council/kr/minutes/late.do',
            'https://www.hsg.go.kr/kr/minutes/late.do',
        ]
    },
    # 영월
    'yeongwol': {
        'name': '영월군의회',
        'urls': [
            'https://www.yw.go.kr/council/kr/minutes/late.do',
            'https://council.yw.go.kr/kr/minutes/late.do',
        ]
    },
    # 서산
    'seosan': {
        'name': '서산시의회',
        'urls': [
            'https://www.seosansi.go.kr/council/kr/minutes/late.do',
            'https://council.seosan.go.kr/kr/minutes/late.do',
        ]
    },
    # 태안
    'taean': {
        'name': '태안군의회',
        'urls': [
            'https://www.taean.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 정읍
    'jeongeup': {
        'name': '정읍시의회',
        'urls': [
            'https://www.jeongeup.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 완주
    'wanju': {
        'name': '완주군의회',
        'urls': [
            'https://www.wanju.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 고창
    'gochang': {
        'name': '고창군의회',
        'urls': [
            'https://www.gochang.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 부안
    'buan': {
        'name': '부안군의회',
        'urls': [
            'https://www.buan.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 담양
    'damyang': {
        'name': '담양군의회',
        'urls': [
            'https://www.damyang.go.kr/council/kr/minutes/late.do',
            'http://dycouncil.go.kr/source/korean/assembly/late.html',
        ]
    },
    # 곡성
    'gokseong': {
        'name': '곡성군의회',
        'urls': [
            'https://www.gokseong.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 구례
    'gurye': {
        'name': '구례군의회',
        'urls': [
            'https://www.gurye.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 보성
    'boseong': {
        'name': '보성군의회',
        'urls': [
            'https://www.boseong.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 장흥
    'jangheung': {
        'name': '장흥군의회',
        'urls': [
            'https://www.jangheung.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 강진
    'gangjin': {
        'name': '강진군의회',
        'urls': [
            'https://www.gangjin.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 무안
    'muan': {
        'name': '무안군의회',
        'urls': [
            'https://www.muan.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 영광
    'yeonggwang': {
        'name': '영광군의회',
        'urls': [
            'https://www.yeonggwang.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 완도
    'wando': {
        'name': '완도군의회',
        'urls': [
            'https://www.wando.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 진도
    'jindo': {
        'name': '진도군의회',
        'urls': [
            'https://www.jindo.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 신안
    'sinan': {
        'name': '신안군의회',
        'urls': [
            'https://www.shinan.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 청송
    'cheongsong': {
        'name': '청송군의회',
        'urls': [
            'https://www.cs.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 영양
    'yeongyang': {
        'name': '영양군의회',
        'urls': [
            'https://www.yyg.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 성주
    'seongju': {
        'name': '성주군의회',
        'urls': [
            'https://www.seongju.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 칠곡
    'chilgok': {
        'name': '칠곡군의회',
        'urls': [
            'https://www.chilgok.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 봉화
    'bonghwa': {
        'name': '봉화군의회',
        'urls': [
            'https://www.bonghwa.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 울릉
    'ulleung': {
        'name': '울릉군의회',
        'urls': [
            'https://www.ulleung.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 하동
    'hadong': {
        'name': '하동군의회',
        'urls': [
            'https://www.hadong.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 합천
    'hapcheon': {
        'name': '합천군의회',
        'urls': [
            'https://www.hapcheon.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 부산 중구
    'jung_busan': {
        'name': '부산 중구의회',
        'urls': [
            'https://www.bsjunggu.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 부산 강서구
    'gangseo_busan': {
        'name': '부산 강서구의회',
        'urls': [
            'https://www.bsgangseo.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 대구 중구
    'jung_daegu': {
        'name': '대구 중구의회',
        'urls': [
            'https://www.junggu.daegu.kr/council/kr/minutes/late.do',
        ]
    },
    # 광주 남구
    'nam_gwangju': {
        'name': '광주 남구의회',
        'urls': [
            'https://www.namgu.gwangju.kr/council/kr/minutes/late.do',
        ]
    },
    # 광주 북구
    'buk_gwangju': {
        'name': '광주 북구의회',
        'urls': [
            'https://www.bukgu.gwangju.kr/council/kr/minutes/late.do',
        ]
    },
    # 광산구
    'gwangsan': {
        'name': '광산구의회',
        'urls': [
            'https://www.gwangsan.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 양주
    'yangju': {
        'name': '양주시의회',
        'urls': [
            'https://www.yangju.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 철원
    'cheorwon': {
        'name': '철원군의회',
        'urls': [
            'https://www.cwg.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 양구
    'yanggu': {
        'name': '양구군의회',
        'urls': [
            'https://www.yanggu.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 고성(강원)
    'goseong_gw': {
        'name': '고성군의회',
        'urls': [
            'https://www.gwgs.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 무주
    'muju': {
        'name': '무주군의회',
        'urls': [
            'https://www.muju.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 임실
    'imsil': {
        'name': '임실군의회',
        'urls': [
            'https://www.imsil.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 순창
    'sunchang': {
        'name': '순창군의회',
        'urls': [
            'https://www.sunchang.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 고흥
    'goheung': {
        'name': '고흥군의회',
        'urls': [
            'https://www.goheung.go.kr/council/kr/minutes/late.do',
        ]
    },
}

async def crawl_meetings(page, code, url):
    """회의록 크롤링"""
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        content = await page.content()

        keywords = ['회의록', '의사일정', '본회의', '위원회', '정례회', '임시회']
        has_keyword = any(kw in content for kw in keywords)

        if not has_keyword:
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

                title = await link.inner_text()
                title = title.strip()

                if not title or len(title) < 3:
                    continue

                title_keywords = ['회', '본회의', '위원회', '정례', '임시', '제']
                if not any(kw in title for kw in title_keywords):
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
                    for key in ['uid', 'id', 'mntsId', 'MINTS_SN', 'schSn', 'no', 'seq', 'hfile', 'idx']:
                        if key in params:
                            meeting_id = params[key][0]
                            break

                cell_texts = []
                for cell in cells:
                    text = await cell.inner_text()
                    cell_texts.append(text.strip())

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

            if meetings:
                break

        return meetings
    except Exception as e:
        print(f"  [{code}] 크롤링 오류: {e}")
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

async def process_council(browser, code, config):
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
                print(f"  오류: {str(e)[:50]}")

            await asyncio.sleep(0.5)

        return {'code': code, 'status': 'no_pattern', 'count': 0}

    finally:
        await page.close()

async def main():
    completed = set()
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith('.jsonl') and not f.startswith('_'):
            completed.add(f.replace('.jsonl', ''))

    pending = {k: v for k, v in CORRECTED_URLS.items() if k not in completed}

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
                    print(f"  ✅ {result['count']}건 수집")
                    success += 1
                else:
                    print(f"  ❌ {result['status']}")
                    failed.append({'code': code, 'reason': result['status']})
            except Exception as e:
                print(f"  ❌ 오류: {str(e)[:50]}")
                failed.append({'code': code, 'reason': str(e)[:50]})

            await asyncio.sleep(1)

    finally:
        await browser.close()
        await playwright.stop()

    print(f"\n{'='*60}")
    print(f"완료: 성공 {success}개 / 실패 {len(failed)}개")

if __name__ == "__main__":
    asyncio.run(main())
