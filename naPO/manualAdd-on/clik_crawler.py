#!/usr/bin/env python3
"""
국회지방의회의정포털(CLIK) 통합 크롤러
========================================
- 243개 지방의회 회의록을 CLIK 포털에서 통합 크롤링
- https://clik.nanet.go.kr/ 활용
- 개별 의회 웹사이트 접근 불필요

Usage:
    python clik_crawler.py --max-pages 5
    python clik_crawler.py --region gyeonggi --max-pages 3
    python clik_crawler.py --council-name 수원시의회 --max-pages 2
    python clik_crawler.py --year 2024 --max-pages 10
"""

import argparse
import json
import logging
import re
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional, Dict, Any, List
from urllib.parse import urljoin, urlencode, quote

import requests
from bs4 import BeautifulSoup

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ============================================================================
# 데이터 모델
# ============================================================================
@dataclass
class ClikMeetingMinutes:
    """CLIK 회의록 데이터 모델"""
    control_no: str          # CLIK 제어번호
    council_name: str        # 의회명 (ex: 수원시의회)
    council_type: str        # 광역/기초
    region: str              # 지역 (경기, 서울 등)
    title: str               # 회의록 제목
    pub_date: str            # 발행일 (YYYY-MM-DD)
    assembly_committee: str  # 대수/위원회
    meeting_type: str        # 회의 유형
    content_preview: str     # 본문 미리보기
    pdf_url: Optional[str] = None
    source_url: str = ""
    scraped_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# CLIK 포털 크롤러
# ============================================================================
class ClikCrawler:
    """국회지방의회의정포털 크롤러"""

    BASE_URL = "https://clik.nanet.go.kr"
    SEARCH_URL = "/potal/search/searchList.do"

    # 지역 코드 매핑
    REGION_CODES = {
        'seoul': '서울특별시',
        'busan': '부산광역시',
        'daegu': '대구광역시',
        'incheon': '인천광역시',
        'gwangju': '광주광역시',
        'daejeon': '대전광역시',
        'ulsan': '울산광역시',
        'sejong': '세종특별자치시',
        'gyeonggi': '경기도',
        'gangwon': '강원특별자치도',
        'chungbuk': '충청북도',
        'chungnam': '충청남도',
        'jeonbuk': '전북특별자치도',
        'jeonnam': '전라남도',
        'gyeongbuk': '경상북도',
        'gyeongnam': '경상남도',
        'jeju': '제주특별자치도',
    }

    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://clik.nanet.go.kr/",
    }

    def __init__(self, output_dir: str = "output"):
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.request_delay = 1.5

    def _get(self, url: str, params: Dict = None, max_retries: int = 3) -> Optional[requests.Response]:
        """GET 요청 with 재시도"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"요청 실패 (시도 {attempt + 1}/{max_retries}): {url} - {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        return None

    def _post(self, url: str, data: Dict = None, max_retries: int = 3) -> Optional[requests.Response]:
        """POST 요청 with 재시도"""
        for attempt in range(max_retries):
            try:
                response = self.session.post(url, data=data, timeout=30)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"요청 실패 (시도 {attempt + 1}/{max_retries}): {url} - {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        return None

    def build_search_url(self, page: int = 1, keyword: str = "",
                         region: str = None, council_name: str = None,
                         year_from: int = None, year_to: int = None) -> str:
        """검색 URL 생성"""
        params = {
            'collection': 'proc',  # 회의록 컬렉션
            'searchSelect': 'Y',
            'sPageIndex': str(page),
            'sPageSize': '10',
        }

        # 키워드 검색
        if keyword:
            params['sSearch_keyword'] = keyword

        # 지역 필터
        if region and region in self.REGION_CODES:
            params['detailSearchStatus'] = 'Y'
            params['sSearch_area'] = self.REGION_CODES[region]

        # 의회명 필터
        if council_name:
            params['detailSearchStatus'] = 'Y'
            params['sSearch_assem'] = council_name

        # 연도 범위
        if year_from:
            params['sSearch_pubYear_from'] = str(year_from)
        if year_to:
            params['sSearch_pubYear_to'] = str(year_to)

        url = urljoin(self.BASE_URL, self.SEARCH_URL)
        return f"{url}?{urlencode(params)}"

    def parse_search_results(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """검색 결과 페이지 파싱"""
        results = []

        # CLIK 검색 결과 목록 파싱
        # 실제 HTML 구조에 맞춰 셀렉터 조정 필요
        items = soup.select('ul.search_result li, div.search_list li, .result_list li')

        if not items:
            # 대체 셀렉터 시도
            items = soup.select('dl.book, div.book_item, .list_item')

        for item in items:
            try:
                result = self._parse_result_item(item, page_url)
                if result:
                    results.append(result)
            except Exception as e:
                logger.debug(f"항목 파싱 실패: {e}")
                continue

        # 결과가 없으면 테이블 형식 시도
        if not results:
            results = self._parse_table_results(soup, page_url)

        return results

    def _parse_result_item(self, item: BeautifulSoup, page_url: str) -> Optional[Dict[str, Any]]:
        """개별 검색 결과 항목 파싱"""
        # 제목과 링크
        title_elem = item.select_one('dt a, .title a, a.title, h3 a, .book_title a')
        if not title_elem:
            title_elem = item.select_one('a[onclick*="goDetail"], a[onclick*="viewPdf"]')

        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)

        # 제어번호 추출 (onclick 속성에서)
        onclick = title_elem.get('onclick', '')
        control_no = self._extract_control_no(onclick)

        # 메타 정보 추출
        meta_text = item.get_text(separator=' ', strip=True)

        # 의회명 추출
        council_name = ""
        council_elem = item.select_one('.assem_name, .council, dd:contains("의회")')
        if council_elem:
            council_name = council_elem.get_text(strip=True)
        else:
            # 텍스트에서 추출
            council_match = re.search(r'([가-힣]+(?:시|군|구|도)의회)', meta_text)
            if council_match:
                council_name = council_match.group(1)

        # 발행일 추출
        pub_date = ""
        date_match = re.search(r'(\d{4}[.-]\d{2}[.-]\d{2})', meta_text)
        if date_match:
            pub_date = date_match.group(1).replace('.', '-')

        # PDF URL
        pdf_url = None
        pdf_link = item.select_one('a[href*=".pdf"], a[onclick*="viewPdf"]')
        if pdf_link:
            pdf_onclick = pdf_link.get('onclick', '')
            pdf_url = self._extract_pdf_url(pdf_onclick)

        return {
            'control_no': control_no or '',
            'title': title,
            'council_name': council_name,
            'pub_date': pub_date,
            'pdf_url': pdf_url,
            'source_url': page_url,
            'meta_text': meta_text[:200],  # 추가 분석용
        }

    def _parse_table_results(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """테이블 형식 검색 결과 파싱"""
        results = []

        # 테이블 행 찾기
        rows = soup.select('table tbody tr, table.list tr')

        for row in rows:
            cells = row.select('td')
            if len(cells) < 3:
                continue

            # 링크 찾기
            link = row.select_one('a[href], a[onclick]')
            if not link:
                continue

            title = link.get_text(strip=True)
            onclick = link.get('onclick', '')
            control_no = self._extract_control_no(onclick)

            results.append({
                'control_no': control_no or '',
                'title': title,
                'council_name': cells[1].get_text(strip=True) if len(cells) > 1 else '',
                'pub_date': cells[2].get_text(strip=True) if len(cells) > 2 else '',
                'pdf_url': None,
                'source_url': page_url,
            })

        return results

    def _extract_control_no(self, onclick: str) -> Optional[str]:
        """onclick에서 제어번호 추출"""
        patterns = [
            r"goDetailSingleDB\(['\"]?(\w+)['\"]?",
            r"goDetail\(['\"]?(\w+)['\"]?",
            r"viewPdfExec\(['\"]?(\w+)['\"]?",
            r"['\"](\w{10,})['\"]",  # 긴 영숫자 ID
        ]

        for pattern in patterns:
            match = re.search(pattern, onclick)
            if match:
                return match.group(1)
        return None

    def _extract_pdf_url(self, onclick: str) -> Optional[str]:
        """onclick에서 PDF URL 추출"""
        # viewPdfExec('제어번호','PROC',...)
        match = re.search(r"viewPdfExec\(['\"](\w+)['\"]", onclick)
        if match:
            control_no = match.group(1)
            return f"{self.BASE_URL}/potal/search/pdfViewer.do?ctrlNo={control_no}&collection=PROC"
        return None

    def fetch_detail(self, control_no: str) -> Optional[Dict[str, Any]]:
        """상세 페이지에서 추가 정보 가져오기"""
        detail_url = f"{self.BASE_URL}/potal/search/searchDetail.do"
        params = {
            'ctrlNo': control_no,
            'collection': 'PROC',
        }

        response = self._get(detail_url, params)
        if not response:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        # 상세 정보 추출
        detail = {
            'content_preview': '',
            'assembly_committee': '',
            'meeting_type': '',
            'region': '',
        }

        # 본문 미리보기
        content_elem = soup.select_one('.content, .detail_content, .view_content')
        if content_elem:
            content_text = content_elem.get_text(separator=' ', strip=True)
            detail['content_preview'] = content_text[:500]

        # 메타 정보 테이블
        meta_rows = soup.select('table.info tr, .detail_info tr, dl.info dd')
        for row in meta_rows:
            text = row.get_text(strip=True)
            if '대수' in text or '위원회' in text:
                detail['assembly_committee'] = text
            elif '회의' in text:
                detail['meeting_type'] = text
            elif any(r in text for r in ['서울', '경기', '부산', '대구', '인천', '광주', '대전', '울산']):
                detail['region'] = text

        return detail

    def crawl(self, max_pages: int = 5, keyword: str = "",
              region: str = None, council_name: str = None,
              year: int = None, fetch_details: bool = False) -> Iterator[ClikMeetingMinutes]:
        """CLIK 크롤링 실행"""
        logger.info("=== CLIK 포털 크롤링 시작 ===")
        logger.info(f"페이지 수: {max_pages}, 지역: {region or '전체'}, 의회: {council_name or '전체'}")

        total_count = 0

        for page in range(1, max_pages + 1):
            search_url = self.build_search_url(
                page=page,
                keyword=keyword,
                region=region,
                council_name=council_name,
                year_from=year,
                year_to=year,
            )

            logger.info(f"[페이지 {page}] 검색 중...")

            response = self._get(search_url)
            if not response:
                logger.warning(f"페이지 {page} 로드 실패")
                continue

            soup = BeautifulSoup(response.content, 'html.parser')
            results = self.parse_search_results(soup, search_url)

            if not results:
                logger.info(f"페이지 {page}: 결과 없음 (마지막 페이지)")
                break

            logger.info(f"페이지 {page}: {len(results)}건 발견")

            for result in results:
                # 상세 정보 가져오기 (선택적)
                detail = {}
                if fetch_details and result.get('control_no'):
                    time.sleep(self.request_delay)
                    detail = self.fetch_detail(result['control_no']) or {}

                # 의회 유형 판단
                council_name_str = result.get('council_name', '')
                council_type = 'metropolitan' if any(x in council_name_str for x in ['특별시', '광역시', '특별자치시', '도의회']) else 'basic'

                # 지역 추출
                region_str = detail.get('region', '')
                if not region_str:
                    for r_code, r_name in self.REGION_CODES.items():
                        if r_name[:2] in council_name_str:
                            region_str = r_name
                            break

                minutes = ClikMeetingMinutes(
                    control_no=result.get('control_no', ''),
                    council_name=council_name_str,
                    council_type=council_type,
                    region=region_str,
                    title=result.get('title', ''),
                    pub_date=result.get('pub_date', ''),
                    assembly_committee=detail.get('assembly_committee', ''),
                    meeting_type=detail.get('meeting_type', ''),
                    content_preview=detail.get('content_preview', ''),
                    pdf_url=result.get('pdf_url'),
                    source_url=result.get('source_url', ''),
                    scraped_at=datetime.now().isoformat(),
                )

                total_count += 1
                logger.info(f"  [{total_count}] {minutes.council_name} | {minutes.title[:40]}...")
                yield minutes

            time.sleep(self.request_delay)

        logger.info(f"=== 크롤링 완료: 총 {total_count}건 ===")

    def save_jsonl(self, results: List[ClikMeetingMinutes], prefix: str = "clik") -> Path:
        """JSONL 형식으로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"{prefix}_{timestamp}.jsonl"

        with open(filename, 'w', encoding='utf-8') as f:
            for item in results:
                line = json.dumps(item.to_dict(), ensure_ascii=False)
                f.write(line + '\n')

        return filename

    def close(self):
        self.session.close()


# ============================================================================
# CLI
# ============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="CLIK 국회지방의회의정포털 크롤러",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python clik_crawler.py --max-pages 5
  python clik_crawler.py --region gyeonggi --max-pages 3
  python clik_crawler.py --council-name 수원시의회 --max-pages 2
  python clik_crawler.py --year 2024 --keyword 예산 --max-pages 10
        """
    )

    parser.add_argument("--max-pages", "-m", type=int, default=5,
                        help="최대 크롤링 페이지 수 (기본: 5)")
    parser.add_argument("--region", "-r", type=str,
                        choices=list(ClikCrawler.REGION_CODES.keys()),
                        help="지역 필터 (예: gyeonggi, seoul)")
    parser.add_argument("--council-name", "-c", type=str,
                        help="의회명 필터 (예: 수원시의회)")
    parser.add_argument("--keyword", "-k", type=str, default="",
                        help="검색 키워드")
    parser.add_argument("--year", "-y", type=int,
                        help="연도 필터 (예: 2024)")
    parser.add_argument("--output", "-o", type=str, default="output",
                        help="출력 디렉토리 (기본: output)")
    parser.add_argument("--details", "-d", action="store_true",
                        help="상세 정보 가져오기 (느림)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="상세 로그 출력")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    crawler = ClikCrawler(output_dir=args.output)

    try:
        results = list(crawler.crawl(
            max_pages=args.max_pages,
            keyword=args.keyword,
            region=args.region,
            council_name=args.council_name,
            year=args.year,
            fetch_details=args.details,
        ))

        if not results:
            logger.warning("수집된 데이터가 없습니다.")
            return 0

        # 저장
        prefix = f"clik_{args.region or 'all'}"
        if args.council_name:
            prefix = f"clik_{args.council_name.replace(' ', '_')}"

        output_file = crawler.save_jsonl(results, prefix)

        logger.info(f"저장 완료: {output_file}")
        logger.info(f"총 {len(results)}건의 회의록 수집")

        # 요약 통계
        councils = {}
        for r in results:
            name = r.council_name or "미분류"
            councils[name] = councils.get(name, 0) + 1

        print("\n=== 의회별 수집 현황 ===")
        for name, count in sorted(councils.items(), key=lambda x: -x[1])[:20]:
            print(f"  {name}: {count}건")

        return 0

    except KeyboardInterrupt:
        logger.info("사용자 중단")
        return 130
    except Exception as e:
        logger.exception(f"크롤링 오류: {e}")
        return 1
    finally:
        crawler.close()


if __name__ == "__main__":
    sys.exit(main())
