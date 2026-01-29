#!/usr/bin/env python3
"""
웹 검색으로 발견한 실제 URL로 크롤링
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

# 웹 검색으로 발견한 실제 URL들
DISCOVERED_URLS = {
    # 서산시 - lib.scc.go.kr 발견!
    'seosan': {
        'name': '서산시의회',
        'urls': [
            'https://lib.scc.go.kr/minutes/mnts/cnts/mnt/mntsList.php',
            'https://www.scc.go.kr/kr/minutes/late.do',
        ]
    },
    # 아산시 - asansicouncil 확인
    'asan': {
        'name': '아산시의회',
        'urls': [
            'https://www.asansicouncil.go.kr/assem/assem_list.php',
            'http://www.asansicouncil.go.kr/assem/assem_list.php',
        ]
    },
    # 양주시 - yjcc.yangju.go.kr
    'yangju': {
        'name': '양주시의회',
        'urls': [
            'http://yjcc.yangju.go.kr/yjcc/minutes/late.do',
            'https://www.yangju.go.kr/yjcc/minutes/late.do',
        ]
    },
    # 강릉시 - gncl.go.kr
    'gangneung': {
        'name': '강릉시의회',
        'urls': [
            'https://www.gncl.go.kr/kr/minutes/late.do',
            'http://www.gncl.go.kr/kr/minutes/late.do',
        ]
    },
    # 남양주시 - nyjc.go.kr
    'namyangju': {
        'name': '남양주시의회',
        'urls': [
            'https://www.nyjc.go.kr/minutes/svc/web/cms/mnts/SvcMntsList.php',
            'https://www.nyjc.go.kr/content/minutes/recentMinutes.html',
        ]
    },
    # 하남시 - council.hanam.go.kr
    'hanam': {
        'name': '하남시의회',
        'urls': [
            'https://council.hanam.go.kr/assem/user/assem/minute/latelyList.hanam',
            'https://council.hanam.go.kr/kr/minutes/late.do',
        ]
    },
    # 횡성군 - hsg.go.kr/council
    'hoengseong': {
        'name': '횡성군의회',
        'urls': [
            'https://hsg.go.kr/council/kr/minutes/late.do',
            'https://www.hsg.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 금정구 - council.geumjeong.go.kr
    'geumjeong': {
        'name': '금정구의회',
        'urls': [
            'https://council.geumjeong.go.kr/assem/user/assem/minute/latelyList.geumj',
        ]
    },
    # 부산 중구
    'jung_busan': {
        'name': '부산 중구의회',
        'urls': [
            'https://www.bsjunggu.go.kr/council/kr/minutes/late.do',
            'https://www.bsjunggu.go.kr/council/assem/minute/latelyList.junggu',
        ]
    },
    # 부산 강서구
    'gangseo_busan': {
        'name': '부산 강서구의회',
        'urls': [
            'https://bsgangseo.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 대구 중구
    'jung_daegu': {
        'name': '대구 중구의회',
        'urls': [
            'https://www.junggucouncil.daegu.kr/kr/minutes/late.do',
        ]
    },
    # 광주 남구
    'nam_gwangju': {
        'name': '광주 남구의회',
        'urls': [
            'http://www.gjnc.or.kr/kr/minutes/late.do',
        ]
    },
    # 광주 북구
    'buk_gwangju': {
        'name': '광주 북구의회',
        'urls': [
            'https://council.bukgu.gwangju.kr/kr/minutes/late.do',
        ]
    },
    # 광산구
    'gwangsan': {
        'name': '광산구의회',
        'urls': [
            'https://gjgc.or.kr/kr/minutes/late.do',
        ]
    },
    # 영월군
    'yeongwol': {
        'name': '영월군의회',
        'urls': [
            'https://council.yw.go.kr/kr/minutes/late.do',
            'https://www.yw.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 철원군
    'cheorwon': {
        'name': '철원군의회',
        'urls': [
            'https://council.cwg.go.kr/kr/minutes/late.do',
            'https://www.cwg.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 양구군
    'yanggu': {
        'name': '양구군의회',
        'urls': [
            'https://council.yanggu.go.kr/kr/minutes/late.do',
            'https://www.yanggu.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 고성군(강원)
    'goseong_gw': {
        'name': '고성군의회',
        'urls': [
            'https://council.gwgs.go.kr/kr/minutes/late.do',
            'https://gwcouncil.gwgs.go.kr/kr/minutes/late.do',
        ]
    },
    # 태안군
    'taean': {
        'name': '태안군의회',
        'urls': [
            'https://council.taean.go.kr/kr/minutes/late.do',
            'https://www.taean.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 정읍시
    'jeongeup': {
        'name': '정읍시의회',
        'urls': [
            'https://council.jeongeup.go.kr/kr/minutes/late.do',
            'https://www.jeongeup.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 완주군
    'wanju': {
        'name': '완주군의회',
        'urls': [
            'https://council.wanju.go.kr/kr/minutes/late.do',
        ]
    },
    # 무주군
    'muju': {
        'name': '무주군의회',
        'urls': [
            'https://council.muju.go.kr/kr/minutes/late.do',
            'https://www.muju.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 임실군
    'imsil': {
        'name': '임실군의회',
        'urls': [
            'https://council.imsil.go.kr/kr/minutes/late.do',
        ]
    },
    # 순창군
    'sunchang': {
        'name': '순창군의회',
        'urls': [
            'https://www.sunchangcouncil.go.kr:8080/kr/minutes/late.do',
        ]
    },
    # 고창군
    'gochang': {
        'name': '고창군의회',
        'urls': [
            'https://assembly.gochang.go.kr/kr/minutes/late.do',
        ]
    },
    # 부안군
    'buan': {
        'name': '부안군의회',
        'urls': [
            'https://assembly.buan.go.kr/kr/minutes/late.do',
        ]
    },
    # 담양군
    'damyang': {
        'name': '담양군의회',
        'urls': [
            'http://dycouncil.go.kr/kr/minutes/late.do',
            'http://dycouncil.go.kr/source/korean/assembly/late.html',
        ]
    },
    # 곡성군
    'gokseong': {
        'name': '곡성군의회',
        'urls': [
            'https://assembly.gokseong.go.kr/kr/minutes/late.do',
        ]
    },
    # 구례군
    'gurye': {
        'name': '구례군의회',
        'urls': [
            'https://www.gurye.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 고흥군
    'goheung': {
        'name': '고흥군의회',
        'urls': [
            'https://council.goheung.go.kr:8088/kr/minutes/late.do',
        ]
    },
    # 보성군
    'boseong': {
        'name': '보성군의회',
        'urls': [
            'https://assembly.boseong.go.kr/kr/minutes/late.do',
        ]
    },
    # 장흥군
    'jangheung': {
        'name': '장흥군의회',
        'urls': [
            'https://www.jhc.go.kr/kr/minutes/late.do',
        ]
    },
    # 강진군
    'gangjin': {
        'name': '강진군의회',
        'urls': [
            'https://gangjincl.go.kr:8070/kr/minutes/late.do',
        ]
    },
    # 무안군
    'muan': {
        'name': '무안군의회',
        'urls': [
            'http://www.muan.or.kr/kr/minutes/late.do',
        ]
    },
    # 영광군
    'yeonggwang': {
        'name': '영광군의회',
        'urls': [
            'https://www.ygcouncil.go.kr/kr/minutes/late.do',
        ]
    },
    # 완도군
    'wando': {
        'name': '완도군의회',
        'urls': [
            'http://www.wdcc.or.kr:8088/kr/minutes/late.do',
        ]
    },
    # 진도군
    'jindo': {
        'name': '진도군의회',
        'urls': [
            'https://www.jindo.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 신안군
    'sinan': {
        'name': '신안군의회',
        'urls': [
            'https://council.shinan.go.kr/kr/minutes/late.do',
        ]
    },
    # 청송군
    'cheongsong': {
        'name': '청송군의회',
        'urls': [
            'https://council.cs.go.kr/kr/minutes/late.do',
        ]
    },
    # 영양군
    'yeongyang': {
        'name': '영양군의회',
        'urls': [
            'https://council.yyg.go.kr/kr/minutes/late.do',
        ]
    },
    # 성주군
    'seongju': {
        'name': '성주군의회',
        'urls': [
            'https://tv.sjcouncil.go.kr/kr/minutes/late.do',
        ]
    },
    # 칠곡군
    'chilgok': {
        'name': '칠곡군의회',
        'urls': [
            'https://council.chilgok.go.kr/kr/minutes/late.do',
        ]
    },
    # 봉화군
    'bonghwa': {
        'name': '봉화군의회',
        'urls': [
            'https://www.bonghwa.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 울릉군
    'ulleung': {
        'name': '울릉군의회',
        'urls': [
            'https://www.ulleung.go.kr/council/kr/minutes/late.do',
        ]
    },
    # 하동군
    'hadong': {
        'name': '하동군의회',
        'urls': [
            'https://www.hdcl.go.kr/kr/minutes/late.do',
        ]
    },
    # 합천군
    'hapcheon': {
        'name': '합천군의회',
        'urls': [
            'https://www.hccl.go.kr/kr/minutes/late.do',
        ]
    },
}

async def crawl_page(page, code, url):
    """페이지 크롤링"""
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        content = await page.content()

        # 회의록 키워드 확인
        keywords = ['회의록', '본회의', '위원회', '정례회', '임시회', '회기']
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
                if not title or len(title) < 3:
                    continue

                # 회의 관련 키워드 확인
                if not any(kw in title for kw in ['회', '본회의', '위원회', '정례', '임시', '제']):
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
                    for key in ['uid', 'id', 'mntsId', 'MINTS_SN', 'schSn', 'no', 'seq', 'sess_id']:
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

    pending = {k: v for k, v in DISCOVERED_URLS.items() if k not in completed}
    print(f"크롤링 대상: {len(pending)}개\n")

    if not pending:
        print("모든 의회 완료!")
        return

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox', '--ignore-certificate-errors']
    )

    context = await browser.new_context(ignore_https_errors=True)
    success = 0
    failed = []

    try:
        for code, config in pending.items():
            name = config['name']
            urls = config['urls']
            print(f"[{code}] {name}...", end=" ", flush=True)

            page = await context.new_page()
            found = False

            for url in urls:
                try:
                    meetings = await crawl_page(page, code, url)
                    if meetings:
                        save_results(code, meetings)
                        print(f"✅ {len(meetings)}건")
                        success += 1
                        found = True
                        break
                except Exception as e:
                    continue

            if not found:
                print("❌")
                failed.append(code)

            await page.close()
            await asyncio.sleep(1)

    finally:
        await context.close()
        await browser.close()
        await playwright.stop()

    print(f"\n{'='*50}")
    print(f"성공: {success}개 / 실패: {len(failed)}개")
    if failed:
        print(f"실패: {failed}")

if __name__ == "__main__":
    asyncio.run(main())
