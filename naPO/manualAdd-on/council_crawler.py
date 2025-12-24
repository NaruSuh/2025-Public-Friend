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

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

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
            "list_table": "table tbody tr",
            "meeting_link": "td a[href*='mntsViewer']",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "title": "td:nth-of-type(4) a",
            "meeting_date": "td:nth-of-type(5)",
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
            "list_table": "table.normal_list tbody tr",
            "meeting_link": "td a[href*='recordView']",
            "assembly_num": "td:nth-of-type(2)",
            "session_num": "td:nth-of-type(3)",
            "meeting_type": "td:nth-of-type(4)",
            "committee": "td:nth-of-type(5)",
            "meeting_date": "td:nth-of-type(6)",
            "title": "td a[href*='recordView']",
        },
        "detail_selectors": {
            "content": ".view_content, .record_view, #recordContent, .record_area",
            "title": ".view_title, h3.title, .title",
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
        "list_url": "/assem/index.busan?menuCd=DOM_000000101000000000",
        "detail_url": "/assem/user/assem/minute/preView.busan",
        "type": "metropolitan",
        "crawler_type": "busan_metro",
        "selectors": {
            "list_table": "table.list tbody tr",
            "meeting_link": "td a[href*='preView']",
            "assembly_num": "td:nth-of-type(2)",
            "session_num": "td:nth-of-type(3)",
            "meeting_type": "td:nth-of-type(4)",
            "committee": "td:nth-of-type(5)",
            "meeting_date": "td:nth-of-type(6)",
            "title": "td:nth-of-type(7) a",
        },
        "detail_selectors": {
            "content": ".view_content, .minute_content, #minute_content",
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
        "base_url": "https://www.icouncil.go.kr",
        "list_url": "/committee/sub/meeting.jsp",
        "detail_url": "/committee/sub/meetingView.jsp",
        "type": "metropolitan",
        "crawler_type": "incheon_metro",
        "selectors": {
            "list_table": "table.tbl_board tbody tr",
            "meeting_link": "td a",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content, .record_content, .board_content",
            "title": ".view_title, .board_title",
        },
        "pagination": {
            "param": "page",
            "type": "query",
        },
        "id_param": "idx",
        "request_delay": 2.0,
    },
    
    "daegu": {
        "name": "대구광역시의회",
        "admin_code": "27000",
        "base_url": "https://council.daegu.go.kr",
        "list_url": "/kr/minutes/late",
        "detail_url": "/viewer/minutes.do",
        "type": "metropolitan",
        "crawler_type": "assembly",
        "selectors": {
            "list_table": "table.normal_list tbody tr, table.tbl_type1 tbody tr",
            "meeting_link": "td a[href*='minutes']",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content, .record_area",
            "title": ".view_title, h3.title",
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
        "base_url": "https://gjcouncil.go.kr",
        "list_url": "/kr/minutes/search.do",
        "detail_url": "/viewer/minutes.do",
        "type": "metropolitan",
        "crawler_type": "assembly",
        "selectors": {
            "list_table": "table.normal_list tbody tr",
            "meeting_link": "td a[href*='minutes']",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content, .record_area",
            "title": ".view_title, h3.title",
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
        "base_url": "https://www.council.ulsan.kr",
        "list_url": "/minutes/assembly/minutes/late.do",
        "detail_url": "/minutes/viewer/minutes.do",
        "type": "metropolitan",
        "crawler_type": "assembly",
        "selectors": {
            "list_table": "table.normal_list tbody tr",
            "meeting_link": "td a[href*='minutes']",
            "assembly_num": "td:nth-of-type(2)",
            "session_num": "td:nth-of-type(3)",
            "meeting_type": "td:nth-of-type(4)",
            "title": "td a[href*='minutes']",
            "meeting_date": "td:nth-of-type(6)",
        },
        "detail_selectors": {
            "content": ".view_content, .record_area",
            "title": ".view_title, h3.title",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "uid",
        "request_delay": 2.0,
    },
    
    "sejong": {
        "name": "세종특별자치시의회",
        "admin_code": "36110",
        "base_url": "https://council.sejong.go.kr",
        "list_url": "/cms/mntsLatelyList.do",
        "detail_url": "/cms/mntsViewer.do",
        "type": "metropolitan",
        "crawler_type": "ems",
        "selectors": {
            "list_table": "table tbody tr",
            "meeting_link": "td a[href*='mntsViewer']",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "title": "td:nth-of-type(4) a",
            "meeting_date": "td:nth-of-type(5)",
        },
        "detail_selectors": {
            "content": ".view_content, .record_area, #contents",
            "title": ".view_title, h3.title",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "mntsId",
        "request_delay": 2.0,
    },
    
    "gangwon": {
        "name": "강원특별자치도의회",
        "admin_code": "51000",
        "base_url": "https://council.gangwon.kr",
        "list_url": "/kr/minutes/search.do",
        "detail_url": "/viewer/minutes.do",
        "type": "metropolitan",
        "crawler_type": "assembly",
        "selectors": {
            "list_table": "table.normal_list tbody tr",
            "meeting_link": "td a[href*='minutes']",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content, .record_area",
            "title": ".view_title, h3.title",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "uid",
        "request_delay": 2.0,
    },
    
    "chungbuk": {
        "name": "충청북도의회",
        "admin_code": "43000",
        "base_url": "https://council.chungbuk.kr",
        "list_url": "/assembly/minutes/late.do",
        "detail_url": "/viewer/minutes.do",
        "type": "metropolitan",
        "crawler_type": "assembly",
        "selectors": {
            "list_table": "table.normal_list tbody tr",
            "meeting_link": "td a[href*='minutes']",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content, .record_area",
            "title": ".view_title, h3.title",
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
        "list_url": "/kr/minutes/late.do",
        "detail_url": "/viewer/minutes.do",
        "type": "metropolitan",
        "crawler_type": "assembly",
        "selectors": {
            "list_table": "table.normal_list tbody tr",
            "meeting_link": "td a[href*='minutes']",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content, .record_area",
            "title": ".view_title, h3.title",
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
        "base_url": "https://r.jbstatecouncil.jeonbuk.kr",
        "list_url": "/main.do",
        "detail_url": "/viewer/minutes.do",
        "type": "metropolitan",
        "crawler_type": "jeonbuk_metro",
        "selectors": {
            "list_table": "table.normal_list tbody tr, table.tbl_list tbody tr",
            "meeting_link": "td a[href*='minutes']",
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
        "list_url": "/main.do",
        "detail_url": "/assem/viewer.do",
        "type": "metropolitan",
        "crawler_type": "jeonnam_metro",
        "selectors": {
            "list_table": "a[href*='viewer']",
            "meeting_link": "a[href*='viewer']",
        },
        "detail_selectors": {
            "content": ".view_content, .record_area, #contents",
            "title": ".view_title, h3.title",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "cdUid",
        "request_delay": 2.0,
    },
    
    "gyeongbuk": {
        "name": "경상북도의회",
        "admin_code": "47000",
        "base_url": "https://council.gb.go.kr",
        "list_url": "/minutes/text/late",
        "detail_url": "/viewer/minutes.do",
        "type": "metropolitan",
        "crawler_type": "assembly",
        "selectors": {
            "list_table": "table.normal_list tbody tr, table.tbl_type1 tbody tr",
            "meeting_link": "td a[href*='minutes']",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content, .record_area",
            "title": ".view_title, h3.title",
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
        "list_url": "/kr/assembly/late.do",
        "detail_url": "/record/recordView.do",
        "type": "metropolitan",
        "crawler_type": "assembly",
        "selectors": {
            "list_table": "table.normal_list tbody tr",
            "meeting_link": "td a[href*='record']",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content, .record_area",
            "title": ".view_title, h3.title",
        },
        "pagination": {
            "param": "pageNo",
            "type": "query",
        },
        "id_param": "key",
        "request_delay": 2.0,
    },
    
    "jeju": {
        "name": "제주특별자치도의회",
        "admin_code": "50000",
        "base_url": "https://record.council.jeju.kr",
        "list_url": "/source/minutes/pages/meeting.html",
        "detail_url": "/source/minutes/pages/view.html",
        "type": "metropolitan",
        "crawler_type": "jeju_metro",
        "selectors": {
            "list_table": "table.tbl_list tbody tr, table tbody tr",
            "meeting_link": "td a",
            "assembly_num": "td:nth-of-type(1)",
            "session_num": "td:nth-of-type(2)",
            "meeting_type": "td:nth-of-type(3)",
            "committee": "td:nth-of-type(4)",
            "meeting_date": "td:nth-of-type(5)",
            "title": "td:nth-of-type(6) a",
        },
        "detail_selectors": {
            "content": ".view_content, .record_area",
            "title": ".view_title, h3.title",
        },
        "pagination": {
            "param": "page",
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
# YAML 설정 로더
# ============================================================================
def load_basic_councils_from_yaml() -> Dict[str, Dict[str, Any]]:
    """basic_councils.yaml에서 226개 기초의회 설정 로드"""
    if not YAML_AVAILABLE:
        logger.warning("PyYAML이 설치되지 않아 기초의회 설정을 로드할 수 없습니다.")
        return {}

    yaml_path = Path(__file__).parent / "basic_councils.yaml"
    if not yaml_path.exists():
        logger.warning(f"기초의회 설정 파일이 없습니다: {yaml_path}")
        return {}

    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"YAML 로드 실패: {e}")
        return {}

    councils = {}
    common = data.get('common', {})
    default_selectors = common.get('default_selectors', {})
    detail_selectors = common.get('detail_selectors', {})

    # 각 지역 그룹 처리
    region_groups = [
        'seoul_districts', 'busan_districts', 'daegu_districts', 'incheon_districts',
        'gwangju_districts', 'daejeon_districts', 'ulsan_districts',
        'gyeonggi_cities', 'gangwon_cities', 'chungbuk_cities', 'chungnam_cities',
        'jeonbuk_cities', 'jeonnam_cities', 'gyeongbuk_cities', 'gyeongnam_cities'
    ]

    for group in region_groups:
        if group not in data:
            continue

        for council in data[group]:
            code = council['code']
            councils[code] = {
                'name': council['name'],
                'admin_code': council['admin_code'],
                'base_url': council['base_url'],
                'list_url': council.get('list_url', '/record/list.do'),
                'detail_url': council.get('detail_url', '/record/view.do'),
                'type': 'basic',
                'crawler_type': council.get('crawler_type', 'default'),
                'selectors': council.get('selectors', default_selectors),
                'detail_selectors': council.get('detail_selectors', detail_selectors),
                'pagination': council.get('pagination', common.get('pagination', {'param': 'pageNo', 'type': 'query'})),
                'id_param': council.get('id_param', 'uid'),
                'request_delay': council.get('request_delay', common.get('request_delay', 2.0)),
            }

    logger.info(f"기초의회 {len(councils)}개 설정 로드 완료")
    return councils


def get_all_councils() -> Dict[str, Dict[str, Any]]:
    """광역의회 + 기초의회 전체 설정 반환"""
    all_councils = COUNCILS.copy()
    basic_councils = load_basic_councils_from_yaml()
    all_councils.update(basic_councils)
    return all_councils


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

        # 경기도의회 특수 테이블 구조 (5컬럼: 번호, 회기, 차수, 제목, 날짜)
        rows = soup.select("table tbody tr")

        for row in rows:
            cells = row.select("td")
            if len(cells) < 4:  # 최소 4개 TD
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
                "assembly_num": cells[0].get_text(strip=True) if len(cells) > 0 else "",
                "session_num": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                "meeting_type": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                "title": link.get_text(strip=True),
                "meeting_date": cells[4].get_text(strip=True) if len(cells) > 4 else "",
                "committee": "",
            })

        return meetings


class SeoulCouncilCrawler(BaseCouncilCrawler):
    """서울시의회 전용 크롤러"""

    def _extract_id_from_url(self, url: str) -> Optional[str]:
        """서울시의회는 key 파라미터 사용"""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        return params.get("key", [None])[0]


class EmsCouncilCrawler(BaseCouncilCrawler):
    """EMS 시스템 사용 의회 크롤러 (수원, 용인 등)"""

    def parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """EMS 시스템 목록 페이지 파싱"""
        meetings = []

        # EMS 테이블 구조
        rows = soup.select("table tbody tr")

        for row in rows:
            cells = row.select("td")
            if len(cells) < 5:
                continue

            # 링크 찾기
            link = row.select_one("a[href]")
            if not link:
                continue

            href = link.get("href", "")
            detail_url = urljoin(page_url, href)
            meeting_id = self._extract_id_from_url(detail_url)

            meetings.append({
                "detail_url": detail_url,
                "meeting_id": meeting_id or "",
                "assembly_num": cells[0].get_text(strip=True) if len(cells) > 0 else "",
                "session_num": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                "meeting_type": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                "committee": cells[3].get_text(strip=True) if len(cells) > 3 else "",
                "meeting_date": cells[4].get_text(strip=True) if len(cells) > 4 else "",
                "title": link.get_text(strip=True),
            })

        return meetings


class AssemblyCouncilCrawler(BaseCouncilCrawler):
    """Assembly 타입 의회 크롤러 (성남 등)"""

    def parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """Assembly 시스템 목록 페이지 파싱"""
        meetings = []

        rows = soup.select("table tbody tr")

        for row in rows:
            cells = row.select("td")
            if len(cells) < 5:
                continue

            link = row.select_one("a[href]")
            if not link:
                continue

            href = link.get("href", "")
            detail_url = urljoin(page_url, href)

            # onclick에서 ID 추출 시도
            onclick = link.get("onclick", "")
            meeting_id = self._extract_id_from_onclick(onclick) or self._extract_id_from_url(detail_url)

            meetings.append({
                "detail_url": detail_url,
                "meeting_id": meeting_id or "",
                "assembly_num": cells[0].get_text(strip=True) if len(cells) > 0 else "",
                "session_num": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                "meeting_type": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                "committee": cells[3].get_text(strip=True) if len(cells) > 3 else "",
                "meeting_date": cells[4].get_text(strip=True) if len(cells) > 4 else "",
                "title": link.get_text(strip=True),
            })

        return meetings


class AnsanCouncilCrawler(BaseCouncilCrawler):
    """안산시의회 전용 크롤러"""

    def parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """안산시의회 회의록 페이지 파싱"""
        meetings = []

        # 안산시의회는 a 태그에 직접 회의록 링크
        links = soup.select("a[href*='SvcMntsViewer']")

        for link in links:
            href = link.get("href", "")
            detail_url = urljoin(page_url, href)

            # schSn 파라미터 추출
            match = re.search(r'schSn=(\d+)', href)
            meeting_id = match.group(1) if match else ""

            title = link.get_text(strip=True)

            # 제목에서 정보 추출
            # 예: "[임시]제300회 본회의 제3차"
            session_match = re.search(r'제(\d+)회', title)
            session_num = f"제{session_match.group(1)}회" if session_match else ""

            meetings.append({
                "detail_url": detail_url,
                "meeting_id": meeting_id,
                "assembly_num": "",
                "session_num": session_num,
                "meeting_type": "본회의" if "본회의" in title else "위원회",
                "committee": "",
                "meeting_date": "",
                "title": title,
            })

        return meetings


class HwaseongCouncilCrawler(BaseCouncilCrawler):
    """화성시의회 전용 크롤러"""

    def parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """화성시의회 회의록 페이지 파싱"""
        meetings = []

        rows = soup.select("table tbody tr, table tr")

        for row in rows:
            cells = row.select("td")
            if len(cells) < 4:
                continue

            link = row.select_one("a[href], a[onclick]")
            if not link:
                continue

            href = link.get("href", "")
            onclick = link.get("onclick", "")

            # onclick에서 회의록 ID 추출
            if onclick:
                match = re.search(r"goView\(['\"]?(\d+)['\"]?\)", onclick)
                if match:
                    meeting_id = match.group(1)
                    detail_url = f"{self.base_url}/cnts/mnt/mntsView.php?bbsCd=mnt&bbsSubCd=mnt01&schSn={meeting_id}"
                else:
                    meeting_id = ""
                    detail_url = page_url
            else:
                detail_url = urljoin(page_url, href)
                meeting_id = self._extract_id_from_url(detail_url)

            meetings.append({
                "detail_url": detail_url,
                "meeting_id": meeting_id or "",
                "assembly_num": cells[0].get_text(strip=True) if len(cells) > 0 else "",
                "session_num": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                "meeting_type": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                "committee": cells[3].get_text(strip=True) if len(cells) > 3 else "",
                "meeting_date": cells[4].get_text(strip=True) if len(cells) > 4 else "",
                "title": link.get_text(strip=True),
            })

        return meetings


class DobongCouncilCrawler(BaseCouncilCrawler):
    """도봉구/은평구/강서구/강동구 전용 크롤러 (meeting/confer 타입)"""

    def parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """meeting/confer 타입 목록 페이지 파싱"""
        meetings = []

        rows = soup.select("table tbody tr")

        for row in rows:
            cells = row.select("td")
            if len(cells) < 4:
                continue

            link = row.select_one("a[href], a[onclick]")
            if not link:
                continue

            href = link.get("href", "")
            onclick = link.get("onclick", "")

            if href and not href.startswith("javascript"):
                detail_url = urljoin(page_url, href)
            elif onclick:
                # onclick에서 URL 추출
                match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", onclick)
                if match:
                    detail_url = urljoin(page_url, match.group(1))
                else:
                    detail_url = page_url
            else:
                detail_url = page_url

            meeting_id = self._extract_id_from_url(detail_url)

            meetings.append({
                "detail_url": detail_url,
                "meeting_id": meeting_id or "",
                "assembly_num": cells[0].get_text(strip=True) if len(cells) > 0 else "",
                "session_num": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                "meeting_type": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                "committee": cells[3].get_text(strip=True) if len(cells) > 3 else "",
                "meeting_date": cells[4].get_text(strip=True) if len(cells) > 4 else "",
                "title": link.get_text(strip=True),
            })

        return meetings


class SeodaemunCouncilCrawler(BaseCouncilCrawler):
    """서대문구의회 전용 크롤러"""

    def parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """서대문구의회 목록 페이지 파싱"""
        meetings = []

        rows = soup.select("table tbody tr")

        for row in rows:
            cells = row.select("td")
            if len(cells) < 4:
                continue

            link = row.select_one("a[href]")
            if not link:
                continue

            href = link.get("href", "")
            detail_url = urljoin(page_url, href)
            meeting_id = self._extract_id_from_url(detail_url)

            meetings.append({
                "detail_url": detail_url,
                "meeting_id": meeting_id or "",
                "assembly_num": cells[0].get_text(strip=True) if len(cells) > 0 else "",
                "session_num": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                "meeting_type": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                "committee": cells[3].get_text(strip=True) if len(cells) > 3 else "",
                "meeting_date": cells[4].get_text(strip=True) if len(cells) > 4 else "",
                "title": link.get_text(strip=True),
            })

        return meetings


class SeongdongCouncilCrawler(BaseCouncilCrawler):
    """성동구의회 전용 크롤러 (영상회의록 시스템)"""

    def parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """성동구의회 영상회의록 목록 파싱"""
        meetings = []

        # 영상회의록 링크 추출
        links = soup.select("a[href*='view'], a[onclick*='view']")

        for link in links:
            href = link.get("href", "")
            onclick = link.get("onclick", "")

            if href and not href.startswith("#"):
                detail_url = urljoin(page_url, href)
            elif onclick:
                match = re.search(r"goView\(['\"]?(\d+)['\"]?\)", onclick)
                if match:
                    detail_url = f"{self.base_url}/cast/minutes/view?ntime={match.group(1)}"
                else:
                    continue
            else:
                continue

            title = link.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            meetings.append({
                "detail_url": detail_url,
                "meeting_id": "",
                "assembly_num": "",
                "session_num": "",
                "meeting_type": "",
                "committee": "",
                "meeting_date": "",
                "title": title,
            })

        return meetings


class YangcheonCouncilCrawler(BaseCouncilCrawler):
    """양천구의회 전용 크롤러"""

    def parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """양천구의회 목록 파싱"""
        meetings = []

        # 양천구는 다른 구조 사용
        links = soup.select("a[href*='record'], a[onclick*='view']")

        for link in links:
            href = link.get("href", "")
            onclick = link.get("onclick", "")

            if href and not href.startswith("javascript"):
                detail_url = urljoin(page_url, href)
            elif onclick:
                match = re.search(r"uid=(\d+)", onclick)
                if match:
                    detail_url = f"{self.base_url}/record/main?uid={match.group(1)}"
                else:
                    continue
            else:
                continue

            title = link.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            meetings.append({
                "detail_url": detail_url,
                "meeting_id": "",
                "assembly_num": "",
                "session_num": "",
                "meeting_type": "",
                "committee": "",
                "meeting_date": "",
                "title": title,
            })

        return meetings


class GeumcheonCouncilCrawler(BaseCouncilCrawler):
    """금천구의회 전용 크롤러 (4컬럼 테이블)"""

    def parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """금천구의회 목록 파싱 (번호, 대수, 회의명, 회의일자)"""
        meetings = []

        rows = soup.select("table.normal_list tbody tr")

        for row in rows:
            cells = row.select("td")
            if len(cells) < 3:
                continue

            link = row.select_one("td.sbj a[href]")
            if not link:
                link = row.select_one("a[href]")
            if not link:
                continue

            href = link.get("href", "")
            detail_url = urljoin(page_url, href)
            meeting_id = self._extract_id_from_url(detail_url)

            # 회의일자 파싱
            meeting_date = ""
            if len(cells) >= 4:
                meeting_date = cells[3].get_text(strip=True)
            elif len(cells) >= 3:
                meeting_date = cells[2].get_text(strip=True)

            meetings.append({
                "detail_url": detail_url,
                "meeting_id": meeting_id or "",
                "assembly_num": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                "session_num": "",
                "meeting_type": "",
                "committee": "",
                "meeting_date": meeting_date,
                "title": link.get_text(strip=True),
            })

        return meetings


class CouncilBookCrawler(BaseCouncilCrawler):
    """CouncilBook 시스템 크롤러 (영도구, 서구, 동래구 등)"""

    def parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """CouncilBook 시스템 목록 파싱"""
        meetings = []

        rows = soup.select("table tbody tr")

        for row in rows:
            cells = row.select("td")
            if len(cells) < 4:
                continue

            # 회의명 링크 찾기
            link = row.select_one("a[href], a[onclick]")
            if not link:
                continue

            href = link.get("href", "")
            onclick = link.get("onclick", "")

            if href and not href.startswith("#"):
                detail_url = urljoin(page_url, href)
            elif onclick:
                # ajaxMtrList('3181') 형태 파싱
                match = re.search(r"ajaxMtrList\(['\"]?(\d+)['\"]?\)", onclick)
                if match:
                    detail_url = f"{self.base_url}/source/pages/simple/simple.do?mints_sn={match.group(1)}"
                else:
                    continue
            else:
                continue

            meeting_id = self._extract_id_from_url(detail_url)

            meetings.append({
                "detail_url": detail_url,
                "meeting_id": meeting_id or "",
                "assembly_num": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                "session_num": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                "meeting_type": "",
                "committee": cells[4].get_text(strip=True) if len(cells) > 4 else "",
                "meeting_date": cells[5].get_text(strip=True) if len(cells) > 5 else "",
                "title": link.get_text(strip=True),
            })

        return meetings


class BusanBoardCrawler(BaseCouncilCrawler):
    """부산 게시판 형식 크롤러 (중구, 동구, 북구 등)"""

    def parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """부산 게시판 형식 목록 파싱"""
        meetings = []

        # 게시판 목록 형식
        rows = soup.select("table tbody tr, .board_list tbody tr, .list_wrap li")

        for row in rows:
            link = row.select_one("a[href]")
            if not link:
                continue

            href = link.get("href", "")
            if not href or href.startswith("javascript"):
                continue

            detail_url = urljoin(page_url, href)
            title = link.get_text(strip=True)

            if not title or len(title) < 3:
                continue

            # 날짜 추출 시도
            date_cell = row.select_one(".date, td:last-child, .regdate")
            meeting_date = date_cell.get_text(strip=True) if date_cell else ""

            meetings.append({
                "detail_url": detail_url,
                "meeting_id": self._extract_id_from_url(detail_url) or "",
                "assembly_num": "",
                "session_num": "",
                "meeting_type": "",
                "committee": "",
                "meeting_date": meeting_date,
                "title": title,
            })

        return meetings


class BusanjinCrawler(BaseCouncilCrawler):
    """부산진구의회 전용 크롤러"""

    def parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """부산진구의회 목록 파싱"""
        meetings = []

        rows = soup.select("table tbody tr")

        for row in rows:
            cells = row.select("td")
            if len(cells) < 4:
                continue

            link = row.select_one("a[onclick]")
            if not link:
                continue

            onclick = link.get("onclick", "")
            # fn_popup_page(353,2,5,1,'임시회','안전복지위원회',0,1,'','')
            match = re.search(r"fn_popup_page\((\d+),(\d+),(\d+),(\d+),'([^']*)','([^']*)'", onclick)
            if match:
                session = match.group(1)
                committee = match.group(6)
                detail_url = f"{self.base_url}/minutes/content/pop.php?ntime={session}&contype=2&subtype={match.group(3)}&num={match.group(4)}"
            else:
                continue

            meetings.append({
                "detail_url": detail_url,
                "meeting_id": session,
                "assembly_num": "",
                "session_num": cells[0].get_text(strip=True) if len(cells) > 0 else "",
                "meeting_type": "",
                "committee": committee,
                "meeting_date": cells[3].get_text(strip=True) if len(cells) > 3 else "",
                "title": link.get_text(strip=True),
            })

        return meetings


class JeonbukMetroCrawler(BaseCouncilCrawler):
    """전북특별자치도의회 전용 크롤러 (ul/li 구조)"""

    def parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """전북특별자치도의회 ul/li 구조 파싱"""
        meetings = []

        # a[href*='viewer'] 링크 찾기
        links = soup.select("a[href*='viewer']")

        for link in links:
            href = link.get("href", "")
            if not href:
                continue

            detail_url = urljoin(page_url, href)

            # span에서 정보 추출
            span = link.select_one("span.fll:not(.icon)")
            if span:
                text = span.get_text(separator=' ', strip=True)
            else:
                text = link.get_text(strip=True)

            # 텍스트에서 정보 파싱: "제12대 422회 [임시회] 2차"
            import re
            assembly_match = re.search(r'제(\d+)대', text)
            session_match = re.search(r'(\d+)회', text)
            type_match = re.search(r'\[(정례회|임시회)\]', text)
            order_match = re.search(r'(\d+)차', text)

            assembly_num = f"제{assembly_match.group(1)}대" if assembly_match else ""
            session_num = f"{session_match.group(1)}회" if session_match else ""
            meeting_type = type_match.group(1) if type_match else ""
            order = f"{order_match.group(1)}차" if order_match else ""

            title = f"{session_num} {meeting_type} {order}".strip()
            if not title:
                title = text[:50]

            meetings.append({
                "detail_url": detail_url,
                "meeting_id": self._extract_id_from_url(detail_url) or "",
                "assembly_num": assembly_num,
                "session_num": session_num,
                "meeting_type": meeting_type,
                "committee": "",
                "meeting_date": "",
                "title": title,
            })

        return meetings


class JeonnamMetroCrawler(BaseCouncilCrawler):
    """전라남도의회 전용 크롤러 (ul/li 구조)"""

    def parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """전라남도의회 ul/li 구조 파싱"""
        meetings = []

        # a[href*='viewer'] 링크 찾기
        links = soup.select("a[href*='viewer']")

        for link in links:
            href = link.get("href", "")
            if not href:
                continue

            detail_url = urljoin(page_url, href)

            # span에서 정보 추출
            span = link.select_one("span.fll:not(.icon)")
            if span:
                text = span.get_text(separator=' ', strip=True)
            else:
                text = link.get_text(strip=True)

            # 텍스트에서 정보 파싱
            import re
            assembly_match = re.search(r'제(\d+)대', text)
            session_match = re.search(r'(\d+)회', text)
            type_match = re.search(r'\[(정례회|임시회)\]', text)
            order_match = re.search(r'(\d+)차', text)
            committee_match = re.search(r'(본회의|위원회)', text)

            assembly_num = f"제{assembly_match.group(1)}대" if assembly_match else ""
            session_num = f"{session_match.group(1)}회" if session_match else ""
            meeting_type = type_match.group(1) if type_match else ""
            order = f"{order_match.group(1)}차" if order_match else ""
            committee = committee_match.group(1) if committee_match else ""

            title = f"{session_num} {meeting_type} {order} {committee}".strip()
            if not title:
                title = text[:50]

            meetings.append({
                "detail_url": detail_url,
                "meeting_id": self._extract_id_from_url(detail_url) or "",
                "assembly_num": assembly_num,
                "session_num": session_num,
                "meeting_type": meeting_type,
                "committee": committee,
                "meeting_date": "",
                "title": title,
            })

        return meetings


class IncheonMetroCrawler(BaseCouncilCrawler):
    """인천광역시의회 전용 크롤러 (5컬럼: 번호, 회기, 제목, 회의록, 날짜)"""

    def parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """인천광역시의회 목록 파싱"""
        meetings = []
        import re

        # 테이블 행 선택
        rows = soup.select("table.general_board tbody tr")

        for row in rows:
            cells = row.select("td")
            if len(cells) < 5:
                continue

            # 컬럼: 번호(0), 회기(1), 제목(2), 회의록링크(3), 날짜(4)
            assembly_num = cells[0].get_text(strip=True)
            session_num = cells[1].get_text(strip=True)

            # 제목 (TD3) - 줄바꿈과 공백 정리
            title_text = cells[2].get_text(separator=' ', strip=True)
            title_text = re.sub(r'\s+', ' ', title_text)  # 다중 공백을 단일 공백으로

            # 회의록 링크 (TD4)
            link = cells[3].select_one("a")
            if not link:
                continue

            detail_url = link.get("href", "")
            if not detail_url:
                continue

            if not detail_url.startswith("http"):
                detail_url = urljoin(page_url, detail_url)

            # 날짜 (TD5) - "2025.11.20 Thu요일" 형식
            date_text = cells[4].get_text(strip=True)
            date_match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})', date_text)
            meeting_date = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}" if date_match else ""

            # 제목에서 회차와 위원회 분리
            # "제2차 의회운영위원회" -> meeting_type: "제2차", committee: "의회운영위원회"
            type_match = re.search(r'(제?\d+차)', title_text)
            meeting_type = type_match.group(1) if type_match else ""

            # 위원회 이름 추출
            committee_match = re.search(r'(본회의|[\w]+위원회)', title_text)
            committee = committee_match.group(1) if committee_match else ""

            meetings.append({
                "detail_url": detail_url,
                "meeting_id": self._extract_id_from_url(detail_url) or "",
                "assembly_num": assembly_num,
                "session_num": session_num,
                "meeting_type": meeting_type,
                "committee": committee,
                "meeting_date": meeting_date,
                "title": title_text,
            })

        return meetings


class BusanMetroCrawler(BaseCouncilCrawler):
    """부산광역시의회 전용 크롤러"""

    def parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """부산광역시의회 목록 파싱"""
        meetings = []

        # table.list 내의 모든 행
        rows = soup.select("table.list tbody tr")

        for row in rows:
            cells = row.select("td")
            if len(cells) < 6:
                continue

            # 회의록보기 링크 찾기
            link = row.select_one("td a[href*='preView']")
            if not link:
                continue

            href = link.get("href", "")
            detail_url = urljoin(page_url, href)

            meetings.append({
                "detail_url": detail_url,
                "meeting_id": self._extract_id_from_url(detail_url) or "",
                "assembly_num": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                "session_num": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                "meeting_type": cells[3].get_text(strip=True) if len(cells) > 3 else "",
                "committee": cells[4].get_text(strip=True) if len(cells) > 4 else "",
                "meeting_date": cells[5].get_text(strip=True) if len(cells) > 5 else "",
                "title": link.get_text(strip=True) or cells[6].get_text(strip=True) if len(cells) > 6 else "",
            })

        return meetings


# ============================================================================
# 크롤러 팩토리
# ============================================================================
def get_crawler(council_code: str) -> Optional[BaseCouncilCrawler]:
    """의회 코드로 크롤러 인스턴스 생성"""
    all_councils = get_all_councils()

    if council_code not in all_councils:
        logger.error(f"지원하지 않는 의회 코드: {council_code}")
        logger.info("사용 가능한 의회 목록은 --list 옵션으로 확인하세요.")
        return None

    config = all_councils[council_code]

    # crawler_type 기반 크롤러 선택
    crawler_type = config.get('crawler_type', 'default')

    type_crawlers = {
        "ems": EmsCouncilCrawler,
        "assembly": AssemblyCouncilCrawler,
        "ansan": AnsanCouncilCrawler,
        "hwaseong": HwaseongCouncilCrawler,
        "goyang": BaseCouncilCrawler,
        "dobong": DobongCouncilCrawler,
        "seodaemun": SeodaemunCouncilCrawler,
        "seongdong": SeongdongCouncilCrawler,
        "yangcheon": YangcheonCouncilCrawler,
        "geumcheon": GeumcheonCouncilCrawler,
        # 부산 자치구의회
        "councilbook": CouncilBookCrawler,
        "busan_board": BusanBoardCrawler,
        "busanjin": BusanjinCrawler,
        "saha": BusanBoardCrawler,  # 사하구도 게시판 형식
        "yeonje": BusanBoardCrawler,  # 연제구도 게시판 형식
        "sasang": BusanBoardCrawler,  # 사상구도 게시판 형식
        # 광역의회 전용
        "busan_metro": BusanMetroCrawler,
        "jeonbuk_metro": JeonbukMetroCrawler,
        "jeonnam_metro": JeonnamMetroCrawler,
        "incheon_metro": IncheonMetroCrawler,
    }

    # 의회별 특수 크롤러 매핑 (레거시)
    special_crawlers = {
        "gyeonggi": GyeonggiCouncilCrawler,
        "seoul": SeoulCouncilCrawler,
    }

    # 우선순위: 의회코드 > crawler_type > 기본
    if council_code in special_crawlers:
        crawler_class = special_crawlers[council_code]
    elif crawler_type in type_crawlers:
        crawler_class = type_crawlers[crawler_type]
    else:
        crawler_class = BaseCouncilCrawler

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
    all_councils = get_all_councils()

    print("\n=== 지원 의회 목록 ===\n")

    # 광역의회
    metropolitan = [(code, cfg) for code, cfg in all_councils.items() if cfg.get("type") == "metropolitan"]
    print(f"[ 광역의회 ({len(metropolitan)}개) ]")
    for code, config in sorted(metropolitan, key=lambda x: x[1]['admin_code']):
        print(f"  {code:15} : {config['name']} ({config['admin_code']})")

    # 기초의회
    basic = [(code, cfg) for code, cfg in all_councils.items() if cfg.get("type") == "basic"]
    print(f"\n[ 기초의회 ({len(basic)}개) ]")

    # 지역별 그룹핑
    regions = {}
    for code, config in basic:
        admin_code = config['admin_code']
        region_code = admin_code[:2]
        if region_code not in regions:
            regions[region_code] = []
        regions[region_code].append((code, config))

    region_names = {
        '11': '서울', '26': '부산', '27': '대구', '28': '인천',
        '29': '광주', '30': '대전', '31': '울산', '41': '경기',
        '51': '강원', '43': '충북', '44': '충남', '52': '전북',
        '46': '전남', '47': '경북', '48': '경남'
    }

    for region_code in sorted(regions.keys()):
        region_name = region_names.get(region_code, region_code)
        councils = regions[region_code]
        print(f"\n  [{region_name}] ({len(councils)}개)")
        for code, config in sorted(councils, key=lambda x: x[1]['admin_code']):
            print(f"    {code:18} : {config['name']}")

    print(f"\n총 {len(all_councils)}개 의회 지원")
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
