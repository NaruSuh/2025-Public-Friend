#!/usr/bin/env python3
"""
전국 243개 지방의회 회의록 크롤러 PoC
=====================================
- 17개 광역의회 + 226개 기초의회 대상
- 단일 파일로 실행 가능
- 의회별 설정을 COUNCILS dict로 관리
- 확장 가능한 구조

Usage:
    python council_crawler.py --council gyeonggi --max-pages 5
    python council_crawler.py --council seoul --max-pages 3
    python council_crawler.py --list  # 지원 의회 목록
"""

import argparse
import json
import logging
import re
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional, Dict, Any, List
from urllib.parse import urljoin, parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

# ============================================================================
# 로깅 설정
# ============================================================================
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
class MeetingMinutes:
    """회의록 데이터 모델"""
    council_code: str
    council_name: str
    admin_code: str
    meeting_id: str
    assembly_number: str  # 대수 (제11대)
    session_number: str   # 회기 (제333회)
    meeting_type: str     # 본회의/상임위/특별위
    committee_name: str   # 위원회명
    meeting_date: str     # YYYY-MM-DD
    title: str
    content_preview: str  # 본문 미리보기 (500자)
    pdf_url: Optional[str] = None
    hwp_url: Optional[str] = None
    source_url: str = ""
    scraped_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# ============================================================================
# 의회별 설정 (COUNCILS)
# ============================================================================
COUNCILS: Dict[str, Dict[str, Any]] = {
    # -------------------------------------------------------------------------
    # 광역의회
    # -------------------------------------------------------------------------
    "gyeonggi": {
        "name": "경기도의회",
        "admin_code": "41000",
        "base_url": "https://kms.ggc.go.kr",
        "list_url": "/svc/cms/mnts/MntsLatelyList.do",
        "detail_url": "/cms/mntsViewer.do",
        "type": "metropolitan",
        "selectors": {
            "list_table": "table.list tbody tr",
            "meeting_link": "td a[href*='mntsViewer']",
            "assembly_num": "td:nth-of-type(2)",
            "session_num": "td:nth-of-type(3)",
            "meeting_type": "td:nth-of-type(4)",
            "committee": "td:nth-of-type(5)",
            "meeting_date": "td:nth-of-type(6)",
            "title": "td:nth-of-type(7) a",
        },
        "detail_selectors": {
            "content": ".view_content, .record_area, #contents",
            "title": "h3.title, .view_title",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "mntsId",
        "file_download": {
            "hwp": "/mnts/MntsFileDownLoadProc.do?mode=hwp&flSn={id}",
        },
        "request_delay": 2.0,
    },
    
    "seoul": {
        "name": "서울특별시의회",
        "admin_code": "11000",
        "base_url": "https://ms.smc.seoul.kr",
        "list_url": "/kr/assembly/late.do",
        "detail_url": "/record/recordView.do",
        "type": "metropolitan",
        "selectors": {
            "list_table": "table.list tbody tr, table.tbl_list tbody tr",
            "meeting_link": "td a[href*='recordView'], td a[onclick*='fn_view']",
            "assembly_num": "td:nth-of-type(2)",
            "session_num": "td:nth-of-type(3)",
            "meeting_type": "td:nth-of-type(4)",
            "committee": "td:nth-of-type(5)",
            "meeting_date": "td:nth-of-type(6)",
            "title": "td:nth-of-type(7) a",
        },
        "detail_selectors": {
            "content": ".view_content, .record_view, #recordContent",
            "title": ".view_title, h3.title",
        },
        "pagination": {
            "param": "pageNum",
            "type": "query",
        },
        "id_param": "key",
        "file_download": {
            "pdf": "/record/pdfDownload.do?key={id}",
        },
        "request_delay": 2.0,
    },
    
    "busan": {
        "name": "부산광역시의회",
        "admin_code": "26000",
        "base_url": "https://council.busan.go.kr",
        "list_url": "/assem/minute/minute_all.jsp",
        "detail_url": "/assem/minute/minute_view.jsp",
        "type": "metropolitan",
        "selectors": {
            "list_table": "table.list tbody tr",
            "meeting_link": "td a[href*='minute_view']",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content, .minute_content",
            "title": ".view_title, h3",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "minuteSid",
        "request_delay": 2.0,
    },
    
    "incheon": {
        "name": "인천광역시의회",
        "admin_code": "28000",
        "base_url": "https://record.icouncil.go.kr",
        "list_url": "/record/record_list.do",
        "detail_url": "/record/record_view.do",
        "type": "metropolitan",
        "selectors": {
            "list_table": "table.list tbody tr",
            "meeting_link": "td a[href*='record_view']",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content, .record_content",
            "title": ".view_title",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "recordId",
        "request_delay": 2.0,
    },
    
    "daegu": {
        "name": "대구광역시의회",
        "admin_code": "27000",
        "base_url": "https://council.daegu.go.kr",
        "list_url": "/kr/minutes/minutes.do",
        "detail_url": "/kr/minutes/minutesView.do",
        "type": "metropolitan",
        "selectors": {
            "list_table": "table.list tbody tr",
            "meeting_link": "td a[href*='minutesView']",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content",
            "title": ".view_title",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "uid",
        "request_delay": 2.0,
    },
    
    "gwangju": {
        "name": "광주광역시의회",
        "admin_code": "29000",
        "base_url": "https://council.gwangju.go.kr",
        "list_url": "/record/record.do",
        "detail_url": "/record/recordView.do",
        "type": "metropolitan",
        "selectors": {
            "list_table": "table.list tbody tr",
            "meeting_link": "td a",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content",
            "title": ".view_title",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "uid",
        "request_delay": 2.0,
    },
    
    "daejeon": {
        "name": "대전광역시의회",
        "admin_code": "30000",
        "base_url": "https://council.daejeon.go.kr",
        "list_url": "/svc/cms/mnts/MntsLatelyList.do",
        "detail_url": "/cms/mntsViewer.do",
        "type": "metropolitan",
        "selectors": {
            "list_table": "table.list tbody tr",
            "meeting_link": "td a[href*='mntsViewer']",
            "assembly_num": "td:nth-of-type(2)",
            "session_num": "td:nth-of-type(3)",
            "meeting_type": "td:nth-of-type(4)",
            "committee": "td:nth-of-type(5)",
            "meeting_date": "td:nth-of-type(6)",
            "title": "td:nth-of-type(7) a",
        },
        "detail_selectors": {
            "content": ".view_content",
            "title": ".view_title",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "mntsId",
        "request_delay": 2.0,
    },
    
    "ulsan": {
        "name": "울산광역시의회",
        "admin_code": "31000",
        "base_url": "https://council.ulsan.go.kr",
        "list_url": "/minutes/list.do",
        "detail_url": "/minutes/view.do",
        "type": "metropolitan",
        "selectors": {
            "list_table": "table.list tbody tr",
            "meeting_link": "td a",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content",
            "title": ".view_title",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "nttId",
        "request_delay": 2.0,
    },
    
    "sejong": {
        "name": "세종특별자치시의회",
        "admin_code": "36110",
        "base_url": "https://council.sejong.go.kr",
        "list_url": "/cms/mnts/list.do",
        "detail_url": "/cms/mnts/view.do",
        "type": "metropolitan",
        "selectors": {
            "list_table": "table.list tbody tr",
            "meeting_link": "td a",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content",
            "title": ".view_title",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "billSn",
        "request_delay": 2.0,
    },
    
    "gangwon": {
        "name": "강원특별자치도의회",
        "admin_code": "51000",
        "base_url": "https://council.gangwon.kr",
        "list_url": "/assembly/minutes/list.do",
        "detail_url": "/assembly/minutes/view.do",
        "type": "metropolitan",
        "selectors": {
            "list_table": "table.list tbody tr",
            "meeting_link": "td a",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content",
            "title": ".view_title",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "mntsId",
        "request_delay": 2.0,
    },
    
    "chungbuk": {
        "name": "충청북도의회",
        "admin_code": "43000",
        "base_url": "https://council.chungbuk.go.kr",
        "list_url": "/record/list.do",
        "detail_url": "/record/view.do",
        "type": "metropolitan",
        "selectors": {
            "list_table": "table.list tbody tr",
            "meeting_link": "td a",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content",
            "title": ".view_title",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "uid",
        "request_delay": 2.0,
    },
    
    "chungnam": {
        "name": "충청남도의회",
        "admin_code": "44000",
        "base_url": "https://council.chungnam.go.kr",
        "list_url": "/record/list.do",
        "detail_url": "/record/view.do",
        "type": "metropolitan",
        "selectors": {
            "list_table": "table.list tbody tr",
            "meeting_link": "td a",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content",
            "title": ".view_title",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "uid",
        "request_delay": 2.0,
    },
    
    "jeonbuk": {
        "name": "전북특별자치도의회",
        "admin_code": "52000",
        "base_url": "https://council.jeonbuk.go.kr",
        "list_url": "/record/list.do",
        "detail_url": "/record/view.do",
        "type": "metropolitan",
        "selectors": {
            "list_table": "table.list tbody tr",
            "meeting_link": "td a",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content",
            "title": ".view_title",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "uid",
        "request_delay": 2.0,
    },
    
    "jeonnam": {
        "name": "전라남도의회",
        "admin_code": "46000",
        "base_url": "https://ems.jnassembly.go.kr",
        "list_url": "/record/list.do",
        "detail_url": "/record/view.do",
        "type": "metropolitan",
        "selectors": {
            "list_table": "table.list tbody tr",
            "meeting_link": "td a",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content",
            "title": ".view_title",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "uid",
        "request_delay": 2.0,
    },
    
    "gyeongbuk": {
        "name": "경상북도의회",
        "admin_code": "47000",
        "base_url": "https://council.gb.go.kr",
        "list_url": "/record/list.do",
        "detail_url": "/record/view.do",
        "type": "metropolitan",
        "selectors": {
            "list_table": "table.list tbody tr",
            "meeting_link": "td a",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content",
            "title": ".view_title",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "uid",
        "request_delay": 2.0,
    },
    
    "gyeongnam": {
        "name": "경상남도의회",
        "admin_code": "48000",
        "base_url": "https://council.gyeongnam.go.kr",
        "list_url": "/record/list.do",
        "detail_url": "/record/view.do",
        "type": "metropolitan",
        "selectors": {
            "list_table": "table.list tbody tr",
            "meeting_link": "td a",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content",
            "title": ".view_title",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "uid",
        "request_delay": 2.0,
    },
    
    "jeju": {
        "name": "제주특별자치도의회",
        "admin_code": "50000",
        "base_url": "https://record.council.jeju.kr",
        "list_url": "/record/list.do",
        "detail_url": "/record/view.do",
        "type": "metropolitan",
        "selectors": {
            "list_table": "table.list tbody tr",
            "meeting_link": "td a",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content",
            "title": ".view_title",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "uid",
        "request_delay": 2.0,
    },
    
    # -------------------------------------------------------------------------
    # 기초의회 예시 (경기도 내)
    # -------------------------------------------------------------------------
    "suwon": {
        "name": "수원시의회",
        "admin_code": "41110",
        "base_url": "https://council.suwon.go.kr",
        "list_url": "/record/list.do",
        "detail_url": "/record/view.do",
        "type": "basic",
        "parent": "gyeonggi",
        "selectors": {
            "list_table": "table.list tbody tr",
            "meeting_link": "td a",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content",
            "title": ".view_title",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "uid",
        "request_delay": 2.0,
    },
    
    "seongnam": {
        "name": "성남시의회",
        "admin_code": "41130",
        "base_url": "https://www.sncouncil.go.kr",
        "list_url": "/record/list.do",
        "detail_url": "/record/view.do",
        "type": "basic",
        "parent": "gyeonggi",
        "selectors": {
            "list_table": "table.list tbody tr",
            "meeting_link": "td a",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content",
            "title": ".view_title",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "uid",
        "request_delay": 2.0,
    },
}

# ============================================================================
# HTTP 클라이언트
# ============================================================================
class HttpClient:
    """HTTP 요청 클라이언트"""
    
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        self.timeout = timeout
        self.max_retries = max_retries
    
    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """GET 요청 with 재시도"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout, **kwargs)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"요청 실패 (시도 {attempt + 1}/{self.max_retries}): {url} - {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 지수 백오프
        return None
    
    def close(self):
        self.session.close()

# ============================================================================
# 기본 크롤러 클래스
# ============================================================================
class BaseCouncilCrawler(ABC):
    """지방의회 크롤러 기본 클래스"""
    
    def __init__(self, council_code: str, config: Dict[str, Any]):
        self.council_code = council_code
        self.config = config
        self.client = HttpClient()
        self.base_url = config["base_url"]
        self.selectors = config.get("selectors", {})
        self.detail_selectors = config.get("detail_selectors", {})
        self.request_delay = config.get("request_delay", 2.0)
    
    def get_list_url(self, page: int = 1) -> str:
        """목록 페이지 URL 생성"""
        list_path = self.config["list_url"]
        url = urljoin(self.base_url, list_path)
        
        if page > 1:
            param = self.config.get("pagination", {}).get("param", "pageNo")
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{param}={page}"
        
        return url
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """페이지 가져오기"""
        response = self.client.get(url)
        if response:
            return BeautifulSoup(response.content, "html.parser")
        return None
    
    def parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """목록 페이지 파싱 - 회의 목록 추출"""
        meetings = []
        
        # 테이블 행 찾기
        table_selector = self.selectors.get("list_table", "table tbody tr")
        rows = soup.select(table_selector)
        
        if not rows:
            # 대체 셀렉터 시도
            alt_selectors = [
                "table.list tbody tr",
                "table.tbl_list tbody tr",
                "table tbody tr",
                ".list_table tbody tr",
                "#list tbody tr",
            ]
            for alt_sel in alt_selectors:
                rows = soup.select(alt_sel)
                if rows:
                    logger.debug(f"대체 셀렉터 사용: {alt_sel}")
                    break
        
        for row in rows:
            try:
                meeting_info = self._extract_meeting_info(row, page_url)
                if meeting_info:
                    meetings.append(meeting_info)
            except Exception as e:
                logger.debug(f"행 파싱 실패: {e}")
                continue
        
        return meetings
    
    def _extract_meeting_info(self, row: BeautifulSoup, page_url: str) -> Optional[Dict[str, Any]]:
        """테이블 행에서 회의 정보 추출"""
        # 링크 찾기
        link_selector = self.selectors.get("meeting_link", "a")
        link_elem = row.select_one(link_selector)
        
        if not link_elem:
            # 대체: 행 내 아무 링크나 찾기
            link_elem = row.select_one("a[href]")
        
        if not link_elem:
            return None
        
        # URL 추출
        href = link_elem.get("href", "")
        onclick = link_elem.get("onclick", "")
        
        detail_url = None
        meeting_id = None
        
        if href and href != "#" and not href.startswith("javascript:"):
            detail_url = urljoin(page_url, href)
            meeting_id = self._extract_id_from_url(detail_url)
        elif onclick:
            # onclick에서 ID 추출 시도
            meeting_id = self._extract_id_from_onclick(onclick)
            if meeting_id:
                detail_url = self._build_detail_url(meeting_id)
        
        if not detail_url:
            return None
        
        # 셀 데이터 추출
        cells = row.select("td")
        
        return {
            "detail_url": detail_url,
            "meeting_id": meeting_id or "",
            "assembly_num": self._get_cell_text(cells, 0),
            "session_num": self._get_cell_text(cells, 1),
            "meeting_type": self._get_cell_text(cells, 2),
            "committee": self._get_cell_text(cells, 3),
            "meeting_date": self._get_cell_text(cells, 4),
            "title": link_elem.get_text(strip=True),
        }
    
    def _get_cell_text(self, cells: List, index: int) -> str:
        """셀 텍스트 안전하게 추출"""
        if index < len(cells):
            return cells[index].get_text(strip=True)
        return ""
    
    def _extract_id_from_url(self, url: str) -> Optional[str]:
        """URL에서 ID 파라미터 추출"""
        id_param = self.config.get("id_param", "uid")
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        if id_param in params:
            return params[id_param][0]
        
        # 대체: 일반적인 ID 파라미터들 시도
        for param in ["uid", "id", "mntsId", "key", "nttId", "bbsSn", "minuteSid"]:
            if param in params:
                return params[param][0]
        
        return None
    
    def _extract_id_from_onclick(self, onclick: str) -> Optional[str]:
        """onclick 속성에서 ID 추출"""
        # 다양한 패턴 시도
        patterns = [
            r"fn_view\(['\"]?(\d+)['\"]?\)",
            r"goView\(['\"]?(\d+)['\"]?\)",
            r"view\(['\"]?(\d+)['\"]?\)",
            r"['\"](\d{4,})['\"]",
            r"\((\d+)\)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, onclick)
            if match:
                return match.group(1)
        
        return None
    
    def _build_detail_url(self, meeting_id: str) -> str:
        """상세 페이지 URL 생성"""
        detail_path = self.config.get("detail_url", "/view.do")
        id_param = self.config.get("id_param", "uid")
        url = urljoin(self.base_url, detail_path)
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}{id_param}={meeting_id}"
    
    def parse_detail_page(self, soup: BeautifulSoup, url: str, meta: Dict[str, Any]) -> MeetingMinutes:
        """상세 페이지 파싱"""
        # 제목 추출
        title_selector = self.detail_selectors.get("title", ".view_title, h3.title")
        title_elem = soup.select_one(title_selector)
        title = title_elem.get_text(strip=True) if title_elem else meta.get("title", "")
        
        # 본문 추출
        content_selector = self.detail_selectors.get("content", ".view_content")
        content_elem = soup.select_one(content_selector)
        
        if not content_elem:
            # 대체 셀렉터
            for alt_sel in [".view_content", ".record_content", ".content", "#content", "article"]:
                content_elem = soup.select_one(alt_sel)
                if content_elem:
                    break
        
        content_text = ""
        if content_elem:
            content_text = content_elem.get_text(separator=" ", strip=True)
            content_text = re.sub(r"\s+", " ", content_text)
        
        # 파일 다운로드 URL 생성
        pdf_url = None
        hwp_url = None
        meeting_id = meta.get("meeting_id", "")
        
        file_download = self.config.get("file_download", {})
        if "pdf" in file_download and meeting_id:
            pdf_url = urljoin(self.base_url, file_download["pdf"].format(id=meeting_id))
        if "hwp" in file_download and meeting_id:
            hwp_url = urljoin(self.base_url, file_download["hwp"].format(id=meeting_id))
        
        # 날짜 정규화
        meeting_date = self._normalize_date(meta.get("meeting_date", ""))
        
        return MeetingMinutes(
            council_code=self.council_code,
            council_name=self.config["name"],
            admin_code=self.config["admin_code"],
            meeting_id=meeting_id,
            assembly_number=meta.get("assembly_num", ""),
            session_number=meta.get("session_num", ""),
            meeting_type=meta.get("meeting_type", ""),
            committee_name=meta.get("committee", ""),
            meeting_date=meeting_date,
            title=title,
            content_preview=content_text[:500] if content_text else "",
            pdf_url=pdf_url,
            hwp_url=hwp_url,
            source_url=url,
            scraped_at=datetime.now().isoformat(),
        )
    
    def _normalize_date(self, date_str: str) -> str:
        """날짜 문자열 정규화 (YYYY-MM-DD)"""
        if not date_str:
            return ""
        
        # 다양한 형식 처리
        date_str = re.sub(r"[년월]", "-", date_str)
        date_str = re.sub(r"[일\s].*", "", date_str)
        date_str = re.sub(r"\.", "-", date_str)
        date_str = date_str.strip()
        
        # YYYY-MM-DD 형식 검증
        if re.match(r"^\d{4}-\d{1,2}-\d{1,2}$", date_str):
            parts = date_str.split("-")
            return f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
        
        return date_str
    
    def crawl(self, max_pages: int = 5, start_page: int = 1) -> Iterator[MeetingMinutes]:
        """크롤링 실행"""
        logger.info(f"=== {self.config['name']} 크롤링 시작 ===")
        logger.info(f"페이지 범위: {start_page} ~ {start_page + max_pages - 1}")
        
        total_count = 0
        
        for page in range(start_page, start_page + max_pages):
            list_url = self.get_list_url(page)
            logger.info(f"[페이지 {page}] {list_url}")
            
            # 목록 페이지 가져오기
            soup = self.fetch_page(list_url)
            if not soup:
                logger.warning(f"페이지 {page} 로드 실패")
                continue
            
            # 목록 파싱
            meetings = self.parse_list_page(soup, list_url)
            
            if not meetings:
                logger.info(f"페이지 {page}: 회의록 없음 (마지막 페이지)")
                break
            
            logger.info(f"페이지 {page}: {len(meetings)}건 발견")
            
            # 각 회의록 상세 페이지 크롤링
            for meeting_info in meetings:
                detail_url = meeting_info["detail_url"]
                
                time.sleep(self.request_delay)  # Rate limiting
                
                detail_soup = self.fetch_page(detail_url)
                if not detail_soup:
                    logger.warning(f"상세 페이지 로드 실패: {detail_url}")
                    continue
                
                try:
                    minutes = self.parse_detail_page(detail_soup, detail_url, meeting_info)
                    total_count += 1
                    logger.info(f"  [{total_count}] {minutes.meeting_date} | {minutes.title[:30]}...")
                    yield minutes
                except Exception as e:
                    logger.error(f"상세 페이지 파싱 오류: {detail_url} - {e}")
            
            time.sleep(self.request_delay)
        
        logger.info(f"=== 크롤링 완료: 총 {total_count}건 ===")
    
    def close(self):
        self.client.close()

# ============================================================================
# 의회별 특수 크롤러 (필요시 확장)
# ============================================================================
class GyeonggiCouncilCrawler(BaseCouncilCrawler):
    """경기도의회 전용 크롤러"""
    
    def parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """경기도의회 목록 페이지 특화 파싱"""
        meetings = []
        
        # 경기도의회 특수 테이블 구조
        rows = soup.select("table tbody tr")
        
        for row in rows:
            cells = row.select("td")
            if len(cells) < 6:
                continue
            
            # 링크 찾기
            link = row.select_one("a[href*='mntsViewer']")
            if not link:
                link = row.select_one("a[href]")
            
            if not link:
                continue
            
            href = link.get("href", "")
            detail_url = urljoin(page_url, href)
            meeting_id = self._extract_id_from_url(detail_url)
            
            meetings.append({
                "detail_url": detail_url,
                "meeting_id": meeting_id or "",
                "assembly_num": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                "session_num": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                "meeting_type": cells[3].get_text(strip=True) if len(cells) > 3 else "",
                "committee": cells[4].get_text(strip=True) if len(cells) > 4 else "",
                "meeting_date": cells[5].get_text(strip=True) if len(cells) > 5 else "",
                "title": link.get_text(strip=True),
            })
        
        return meetings


class SeoulCouncilCrawler(BaseCouncilCrawler):
    """서울시의회 전용 크롤러"""
    
    def _extract_id_from_url(self, url: str) -> Optional[str]:
        """서울시의회는 key 파라미터 사용"""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        return params.get("key", [None])[0]

# ============================================================================
# 크롤러 팩토리
# ============================================================================
def get_crawler(council_code: str) -> Optional[BaseCouncilCrawler]:
    """의회 코드로 크롤러 인스턴스 생성"""
    if council_code not in COUNCILS:
        logger.error(f"지원하지 않는 의회 코드: {council_code}")
        return None
    
    config = COUNCILS[council_code]
    
    # 의회별 특수 크롤러 매핑
    special_crawlers = {
        "gyeonggi": GyeonggiCouncilCrawler,
        "seoul": SeoulCouncilCrawler,
    }
    
    crawler_class = special_crawlers.get(council_code, BaseCouncilCrawler)
    return crawler_class(council_code, config)

# ============================================================================
# 결과 저장
# ============================================================================
class ResultSaver:
    """크롤링 결과 저장"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save_jsonl(self, council_code: str, results: List[MeetingMinutes]) -> Path:
        """JSONL 형식으로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"{council_code}_{timestamp}.jsonl"
        
        with open(filename, "w", encoding="utf-8") as f:
            for item in results:
                line = json.dumps(item.to_dict(), ensure_ascii=False)
                f.write(line + "\n")
        
        return filename
    
    def save_json(self, council_code: str, results: List[MeetingMinutes]) -> Path:
        """JSON 형식으로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"{council_code}_{timestamp}.json"
        
        data = [item.to_dict() for item in results]
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, ensure_ascii=False, indent=2, fp=f)
        
        return filename

# ============================================================================
# CLI 인터페이스
# ============================================================================
def list_councils():
    """지원 의회 목록 출력"""
    print("\n=== 지원 의회 목록 ===\n")
    
    # 광역의회
    print("[ 광역의회 (17개) ]")
    for code, config in COUNCILS.items():
        if config.get("type") == "metropolitan":
            print(f"  {code:12} : {config['name']} ({config['admin_code']})")
    
    # 기초의회
    print("\n[ 기초의회 (샘플) ]")
    for code, config in COUNCILS.items():
        if config.get("type") == "basic":
            print(f"  {code:12} : {config['name']} ({config['admin_code']})")
    
    print("\n* 기초의회는 COUNCILS dict에 설정 추가 필요")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="전국 지방의회 회의록 크롤러 PoC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python council_crawler.py --council gyeonggi --max-pages 3
  python council_crawler.py --council seoul --max-pages 5 --output ./data
  python council_crawler.py --list
        """
    )
    
    parser.add_argument("--council", "-c", type=str, help="의회 코드 (예: gyeonggi, seoul)")
    parser.add_argument("--max-pages", "-m", type=int, default=3, help="최대 크롤링 페이지 수 (기본: 3)")
    parser.add_argument("--start-page", "-s", type=int, default=1, help="시작 페이지 (기본: 1)")
    parser.add_argument("--output", "-o", type=str, default="output", help="출력 디렉토리 (기본: output)")
    parser.add_argument("--format", "-f", choices=["json", "jsonl"], default="jsonl", help="출력 형식 (기본: jsonl)")
    parser.add_argument("--list", "-l", action="store_true", help="지원 의회 목록 출력")
    parser.add_argument("--verbose", "-v", action="store_true", help="상세 로그 출력")
    
    args = parser.parse_args()
    
    # 로그 레벨 설정
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 의회 목록 출력
    if args.list:
        list_councils()
        return 0
    
    # 의회 코드 필수 체크
    if not args.council:
        parser.print_help()
        print("\n오류: --council 옵션이 필요합니다. --list로 지원 의회 확인")
        return 1
    
    # 크롤러 생성
    crawler = get_crawler(args.council)
    if not crawler:
        return 1
    
    try:
        # 크롤링 실행
        results = list(crawler.crawl(
            max_pages=args.max_pages,
            start_page=args.start_page,
        ))
        
        if not results:
            logger.warning("수집된 데이터가 없습니다.")
            return 0
        
        # 결과 저장
        saver = ResultSaver(args.output)
        
        if args.format == "jsonl":
            output_file = saver.save_jsonl(args.council, results)
        else:
            output_file = saver.save_json(args.council, results)
        
        logger.info(f"저장 완료: {output_file}")
        logger.info(f"총 {len(results)}건의 회의록 수집")
        
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
