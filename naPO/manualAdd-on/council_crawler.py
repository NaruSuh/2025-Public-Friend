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
import random
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
    content_preview: str  # 본문 미리보기 (500자) - 하위호환용
    full_content: str = ""  # 전체 회의록 본문
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
        self.session.verify = False  # SSL 인증서 검증 비활성화
        self.timeout = timeout
        self.max_retries = max_retries
        # SSL 경고 무시
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """GET 요청 with 재시도"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout, verify=False, **kwargs)
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
        for param in ["uid", "id", "mntsId", "key", "nttId", "bbsSn", "minuteSid", "MINTS_SN", "schSn"]:
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

        # 전체 본문 추출
        full_content = self._extract_full_content(soup, url)

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
            content_preview=full_content[:500] if full_content else "",
            full_content=full_content,
            pdf_url=pdf_url,
            hwp_url=hwp_url,
            source_url=url,
            scraped_at=datetime.now().isoformat(),
        )

    def _extract_full_content(self, soup: BeautifulSoup, url: str) -> str:
        """전체 회의록 본문 추출 - 기본 구현"""
        # 본문 추출 - 여러 셀렉터 시도
        content_selector = self.detail_selectors.get("content", ".view_content")
        content_elem = soup.select_one(content_selector)

        if not content_elem:
            # 대체 셀렉터 목록
            alt_selectors = [
                "section.content #canvas",  # 서울시의회 형식
                "#canvas",
                ".content-wrapper .content",
                ".record_area",
                ".view_content",
                ".record_content",
                ".minutes_content",
                ".content",
                "#content",
                "article",
                ".bodyBx-1",  # 부산시의회 형식
            ]
            for alt_sel in alt_selectors:
                content_elem = soup.select_one(alt_sel)
                if content_elem and len(content_elem.get_text(strip=True)) > 100:
                    break

        if not content_elem:
            return ""

        # HTML을 깔끔한 텍스트로 변환
        return self._html_to_text(content_elem)

    def _html_to_text(self, elem) -> str:
        """HTML 요소를 깔끔한 텍스트로 변환"""
        if not elem:
            return ""

        # 불필요한 요소 제거 (스크립트, 스타일, 검색 UI 등)
        for tag in elem.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            tag.decompose()

        # 검색 관련 UI 요소 제거
        for selector in ['.search', '.sidebar', '.util', '.bt_', '.btn', 'form', 'input', 'button']:
            for el in elem.select(selector):
                el.decompose()

        # br 태그를 줄바꿈으로 변환
        for br in elem.find_all('br'):
            br.replace_with('\n')

        # hr 태그를 구분선으로 변환
        for hr in elem.find_all('hr'):
            hr.replace_with('\n---\n')

        # 제목 태그에 줄바꿈 추가
        for tag in elem.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            tag.insert_before('\n\n')
            tag.insert_after('\n')

        # div, p 태그에 줄바꿈 추가
        for tag in elem.find_all(['div', 'p']):
            text = tag.get_text(strip=True)
            if text:
                tag.insert_after('\n')

        # 텍스트 추출
        text = elem.get_text(separator=' ')

        # 정리
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            # 중복 공백 제거
            line = re.sub(r'\s+', ' ', line)
            if line:
                lines.append(line)

        # 연속된 빈 줄 제거
        result = '\n'.join(lines)
        result = re.sub(r'\n{3,}', '\n\n', result)

        return result.strip()

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

    def _extract_full_content(self, soup: BeautifulSoup, url: str) -> str:
        """서울시의회 전체 회의록 본문 추출"""
        # section.content 내의 #canvas div에서 전체 내용 추출
        canvas = soup.select_one("section.content #canvas")
        if canvas:
            return self._html_to_text(canvas)

        # 폴백: .content 시도
        content = soup.select_one(".content")
        if content:
            return self._html_to_text(content)

        # 최종 폴백
        return super()._extract_full_content(soup, url)


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

        # tbody가 있으면 tbody tr, 없으면 table tr
        rows = soup.select("table tbody tr")
        if not rows:
            rows = soup.select("table tr")

        for row in rows:
            cells = row.select("td")
            if len(cells) < 2:  # 최소 2개 셀만 필요
                continue

            link = row.select_one("a[href]")
            if not link:
                continue

            href = link.get("href", "")
            if not href or href == "#" or href.startswith("javascript:void"):
                continue

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
            link = row.select_one("a[href], a[onclick], a[data-uid]")
            if not link:
                continue

            href = link.get("href", "")
            onclick = link.get("onclick", "")
            data_uid = link.get("data-uid", "")

            if data_uid:
                # data-uid 속성 기반 (남구 등)
                detail_url = f"{self.base_url}/record/main?uid={data_uid}"
            elif href and href.startswith("javascript:fn_egov_selectView"):
                # fn_egov_selectView('975') 형태 파싱 (수영구)
                match = re.search(r"fn_egov_selectView\(['\"]?(\d+)['\"]?\)", href)
                if match:
                    bi_id = match.group(1)
                    detail_url = f"{self.base_url}/minutes/source/pages/bill/bill.do?BI_ID={bi_id}&search=view"
                else:
                    continue
            elif href and not href.startswith("#") and not href.startswith("javascript"):
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

            meeting_id = data_uid or self._extract_id_from_url(detail_url)

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


class XcomCrawler(BaseCouncilCrawler):
    """Xcom 회의록 시스템 크롤러 (파주, 이천, 청주 등)"""

    def parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """Xcom 시스템 목록 파싱"""
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
            if not href or href.startswith("#"):
                continue

            # /minutes/xcom/web/minutesViewer.php?id=3814 형태
            # /minutes/city/xcom/web/minutesViewer.php?id=3162 형태
            # /minutes/svc/web/cms/mnts/SvcMntsViewer.php?schSn=3828 형태
            detail_url = urljoin(self.base_url, href)

            # ID 추출
            meeting_id = ""
            if "id=" in href:
                match = re.search(r'id=(\d+)', href)
                if match:
                    meeting_id = match.group(1)
            elif "schSn=" in href:
                match = re.search(r'schSn=(\d+)', href)
                if match:
                    meeting_id = match.group(1)

            # 테이블 구조: 연번, 회기, 차수, 회의명, 회의일
            meetings.append({
                "detail_url": detail_url,
                "meeting_id": meeting_id,
                "assembly_num": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                "session_num": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                "meeting_type": "",
                "committee": "",
                "meeting_date": cells[4].get_text(strip=True) if len(cells) > 4 else "",
                "title": link.get_text(strip=True),
            })

        return meetings

    def _extract_full_content(self, soup: BeautifulSoup, url: str) -> str:
        """Xcom 뷰어에서 전체 내용 추출"""
        content_parts = []

        # 본문 영역 찾기 - 다양한 선택자 시도
        content_area = None
        for selector in ['#content', '.viewer_content', '.minutes_content', '.content', 'body']:
            content_area = soup.select_one(selector)
            if content_area:
                break

        if content_area:
            # 불필요한 요소 제거
            for tag in content_area.select('script, style, nav, header, footer, .sidenav, .skipNav, #top, #menu, .setting, .fnc_menu'):
                tag.decompose()

            text = content_area.get_text(separator='\n', strip=True)
            # 정리
            lines = []
            for line in text.split('\n'):
                line = line.strip()
                if line and len(line) > 1:
                    # 메뉴 항목 제외
                    if line in ['바로가기', '본문으로 바로가기', '메뉴 바로가기', '설정메뉴', '기능메뉴', '맨위로 이동', '닫기']:
                        continue
                    if line.startswith('발언자 선택') or line.startswith('안건선택') or line.startswith('안건 선택'):
                        continue
                    lines.append(line)
            content_parts.append('\n'.join(lines))

        return '\n\n'.join(content_parts)


class JeonbukMetroCrawler(BaseCouncilCrawler):
    """전북특별자치도의회 전용 크롤러 (AJAX JSON API 사용)"""

    def crawl(self, max_pages: int = 5, start_page: int = 1) -> Iterator[MeetingMinutes]:
        """전북특별자치도의회 AJAX API로 목록 가져오기"""
        council_name = self.config.get("name", self.council_code)
        logger.info(f"=== {council_name} 크롤링 시작 ===")
        logger.info(f"페이지 범위: {start_page} ~ {start_page + max_pages - 1}")

        for page_num in range(start_page, start_page + max_pages):
            try:
                api_url = f"{self.base_url}/assem/recent/LoadingList.json"

                params = {
                    "searchCtGroup": "",
                    "searchCdImsi": "",  # 전북은 빈 문자열로 해야 정상 동작
                    "pageIndex": page_num,
                    "recordCountPerPage": 20
                }

                response = self.client.session.post(api_url, data=params, timeout=30)
                if response.status_code != 200:
                    logger.warning(f"페이지 {page_num} API 호출 실패: {response.status_code}")
                    continue

                data = response.json()
                meetings_list = data.get("list", [])

                if not meetings_list:
                    logger.info(f"페이지 {page_num}: 데이터 없음")
                    break

                logger.info(f"페이지 {page_num}: {len(meetings_list)}건 발견")

                for item in meetings_list:
                    try:
                        cd_uid = item.get("cdUid")
                        if not cd_uid:
                            continue

                        detail_url = f"{self.base_url}/assem/viewer.do?cdUid={cd_uid}"

                        # 메타데이터 구성
                        assembly_num = f"제{item.get('csDaesoo', '')}대"
                        session_num = f"{item.get('csSession', '')}회"
                        meeting_type = item.get("csTypeNm", "")
                        committee = item.get("ctNm", "")
                        meeting_date = item.get("cdDate", "").replace(".", "-")
                        chasoo = item.get("cdChasoo", "")

                        title = f"{session_num} {meeting_type} {chasoo}차 {committee}".strip()

                        meta = {
                            "detail_url": detail_url,
                            "meeting_id": str(cd_uid),
                            "assembly_num": assembly_num,
                            "session_num": session_num,
                            "meeting_type": meeting_type,
                            "committee": committee,
                            "meeting_date": meeting_date,
                            "title": title,
                        }

                        # 상세 페이지 가져오기
                        time.sleep(random.uniform(1.5, 3.0))
                        detail_resp = self.client.session.get(detail_url, timeout=30)

                        if detail_resp.status_code == 200:
                            detail_soup = BeautifulSoup(detail_resp.text, 'html.parser')
                            result = self.parse_detail_page(detail_soup, detail_url, meta)
                            logger.info(f"  [{meetings_list.index(item)+1}] {meeting_date} | {title}...")
                            yield result
                        else:
                            logger.warning(f"상세 페이지 로드 실패: {detail_url}")

                    except Exception as e:
                        logger.error(f"항목 처리 오류: {e}")
                        continue

                time.sleep(random.uniform(2.0, 4.0))

            except Exception as e:
                logger.error(f"페이지 {page_num} 처리 오류: {e}")
                continue

    def parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """전북특별자치도의회는 AJAX 사용으로 이 메서드 사용 안함"""
        return []

    def _extract_full_content(self, soup: BeautifulSoup, url: str) -> str:
        """전북특별자치도의회 전체 회의록 본문 추출"""
        content_parts = []

        # headBox에서 회의 정보 추출
        head_box = soup.select_one("#headBox")
        if head_box:
            title_div = head_box.select_one(".fz36")
            if title_div:
                content_parts.append(title_div.get_text(strip=True))

            date_div = head_box.select_one("#date")
            if date_div:
                content_parts.append(date_div.get_text(strip=True))
            place_div = head_box.select_one("#place")
            if place_div:
                content_parts.append(place_div.get_text(strip=True))

            purpose_box = head_box.select_one("#purposeBox")
            if purpose_box:
                content_parts.append("\n의사일정")
                content_parts.append(purpose_box.get_text(separator='\n', strip=True))

            content_parts.append("\n---\n")

        # bodyBox에서 실제 회의 내용 추출
        body_box = soup.select_one("#bodyBox")
        if body_box:
            for con93 in body_box.select(".con93"):
                speaker = con93.select_one("label a, .labelAColor, .labelQColor")
                if speaker:
                    speaker_name = speaker.get_text(strip=True)
                    content_parts.append(f"\n○ {speaker_name}")

                for item_div in con93.select(".item"):
                    for lineht in item_div.select(".lineht"):
                        text = lineht.get_text(strip=True)
                        if text:
                            content_parts.append(text)

            for time_div in body_box.select("#time .por"):
                time_text = time_div.get_text(strip=True)
                if time_text:
                    content_parts.append(f"\n{time_text}\n")

        # tailBox에서 출석 정보 추출
        tail_box = soup.select_one("#tailBox")
        if tail_box:
            attend_member = tail_box.select_one("#attendMember")
            if attend_member:
                content_parts.append("\n---\n")
                content_parts.append(attend_member.get_text(separator='\n', strip=True))

        if content_parts:
            return '\n'.join(content_parts)

        return super()._extract_full_content(soup, url)


class JeonnamMetroCrawler(BaseCouncilCrawler):
    """전라남도의회 전용 크롤러 (AJAX JSON API 사용)"""

    def crawl(self, max_pages: int = 5, start_page: int = 1) -> Iterator[MeetingMinutes]:
        """전라남도의회 AJAX API로 목록 가져오기"""
        council_name = self.config.get("name", self.council_code)
        logger.info(f"=== {council_name} 크롤링 시작 ===")
        logger.info(f"페이지 범위: {start_page} ~ {start_page + max_pages - 1}")

        for page_num in range(start_page, start_page + max_pages):
            try:
                # AJAX API 호출 (각 카테고리별로 호출)
                # ctGroup: '' (전체), 'B' (본회의), 'S' (상임위), 'T' (특별위), 'Y' (예결위)
                api_url = f"{self.base_url}/assem/recent/LoadingList.json"

                params = {
                    "searchCtGroup": "",  # 전체
                    "searchCdImsi": "Y",  # 임시회의록 포함
                    "pageIndex": page_num,
                    "recordCountPerPage": 20
                }

                response = self.client.session.post(api_url, data=params, timeout=30)
                if response.status_code != 200:
                    logger.warning(f"페이지 {page_num} API 호출 실패: {response.status_code}")
                    continue

                data = response.json()
                meetings_list = data.get("list", [])

                if not meetings_list:
                    logger.info(f"페이지 {page_num}: 데이터 없음")
                    break

                logger.info(f"페이지 {page_num}: {len(meetings_list)}건 발견")

                for item in meetings_list:
                    try:
                        cd_uid = item.get("cdUid")
                        if not cd_uid:
                            continue

                        detail_url = f"{self.base_url}/assem/viewer.do?cdUid={cd_uid}"

                        # 메타데이터 구성
                        assembly_num = f"제{item.get('csDaesoo', '')}대"
                        session_num = f"{item.get('csSession', '')}회"
                        meeting_type = item.get("csTypeNm", "")
                        committee = item.get("ctNm", "")
                        meeting_date = item.get("cdDate", "").replace(".", "-")
                        chasoo = item.get("cdChasoo", "")

                        title = f"{session_num} {meeting_type} {chasoo}차 {committee}".strip()

                        meta = {
                            "detail_url": detail_url,
                            "meeting_id": str(cd_uid),
                            "assembly_num": assembly_num,
                            "session_num": session_num,
                            "meeting_type": meeting_type,
                            "committee": committee,
                            "meeting_date": meeting_date,
                            "title": title,
                        }

                        # 상세 페이지 가져오기
                        time.sleep(random.uniform(1.5, 3.0))
                        detail_resp = self.client.session.get(detail_url, timeout=30)

                        if detail_resp.status_code == 200:
                            detail_soup = BeautifulSoup(detail_resp.text, 'html.parser')
                            result = self.parse_detail_page(detail_soup, detail_url, meta)
                            logger.info(f"  [{meetings_list.index(item)+1}] {meeting_date} | {title}...")
                            yield result
                        else:
                            logger.warning(f"상세 페이지 로드 실패: {detail_url}")

                    except Exception as e:
                        logger.error(f"항목 처리 오류: {e}")
                        continue

                time.sleep(random.uniform(2.0, 4.0))

            except Exception as e:
                logger.error(f"페이지 {page_num} 처리 오류: {e}")
                continue

    def parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """전라남도의회는 AJAX 사용으로 이 메서드 사용 안함"""
        return []

    def _extract_full_content(self, soup: BeautifulSoup, url: str) -> str:
        """전라남도의회 전체 회의록 본문 추출"""
        content_parts = []

        # headBox에서 회의 정보 추출
        head_box = soup.select_one("#headBox")
        if head_box:
            # 회의 제목
            title_div = head_box.select_one(".fz36")
            if title_div:
                content_parts.append(title_div.get_text(strip=True))

            # 일시, 장소
            date_div = head_box.select_one("#date")
            if date_div:
                content_parts.append(date_div.get_text(strip=True))
            place_div = head_box.select_one("#place")
            if place_div:
                content_parts.append(place_div.get_text(strip=True))

            # 의사일정
            purpose_box = head_box.select_one("#purposeBox")
            if purpose_box:
                content_parts.append("\n의사일정")
                content_parts.append(purpose_box.get_text(separator='\n', strip=True))

            content_parts.append("\n---\n")

        # bodyBox에서 실제 회의 내용 추출
        body_box = soup.select_one("#bodyBox")
        if body_box:
            # 각 발언 블록 처리
            for con93 in body_box.select(".con93"):
                # 발언자 추출
                speaker = con93.select_one("label a, .labelAColor, .labelQColor")
                if speaker:
                    speaker_name = speaker.get_text(strip=True)
                    content_parts.append(f"\n○ {speaker_name}")

                # 발언 내용 추출
                for item_div in con93.select(".item"):
                    for lineht in item_div.select(".lineht"):
                        text = lineht.get_text(strip=True)
                        if text:
                            content_parts.append(text)

            # 시간 정보 추출
            for time_div in body_box.select("#time .por"):
                time_text = time_div.get_text(strip=True)
                if time_text:
                    content_parts.append(f"\n{time_text}\n")

        # tailBox에서 출석 정보 추출
        tail_box = soup.select_one("#tailBox")
        if tail_box:
            attend_member = tail_box.select_one("#attendMember")
            if attend_member:
                content_parts.append("\n---\n")
                content_parts.append(attend_member.get_text(separator='\n', strip=True))

        if content_parts:
            return '\n'.join(content_parts)

        # 폴백: 전체 텍스트
        return super()._extract_full_content(soup, url)


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

    def _extract_full_content(self, soup: BeautifulSoup, url: str) -> str:
        """인천광역시의회 전체 회의록 본문 추출 (전라남도와 동일한 시스템)"""
        content_parts = []

        # headBox에서 회의 정보 추출
        head_box = soup.select_one("#headBox")
        if head_box:
            # 회의 제목
            title_div = head_box.select_one(".fz36")
            if title_div:
                content_parts.append(title_div.get_text(strip=True))

            # 일시, 장소
            date_div = head_box.select_one("#date")
            if date_div:
                content_parts.append(date_div.get_text(strip=True))
            place_div = head_box.select_one("#place")
            if place_div:
                content_parts.append(place_div.get_text(strip=True))

            # 의사일정
            purpose_box = head_box.select_one("#purposeBox")
            if purpose_box:
                content_parts.append("\n의사일정")
                content_parts.append(purpose_box.get_text(separator='\n', strip=True))

            content_parts.append("\n---\n")

        # bodyBox에서 실제 회의 내용 추출
        body_box = soup.select_one("#bodyBox")
        if body_box:
            # 각 발언 블록 처리
            for con93 in body_box.select(".con93"):
                # 발언자 추출
                speaker = con93.select_one("label a, .labelAColor, .labelQColor")
                if speaker:
                    speaker_name = speaker.get_text(strip=True)
                    content_parts.append(f"\n○ {speaker_name}")

                # 발언 내용 추출
                for item_div in con93.select(".item"):
                    for lineht in item_div.select(".lineht"):
                        text = lineht.get_text(strip=True)
                        if text:
                            content_parts.append(text)

            # 시간 정보 추출
            for time_div in body_box.select("#time .por"):
                time_text = time_div.get_text(strip=True)
                if time_text:
                    content_parts.append(f"\n{time_text}\n")

        # tailBox에서 출석 정보 추출
        tail_box = soup.select_one("#tailBox")
        if tail_box:
            attend_member = tail_box.select_one("#attendMember")
            if attend_member:
                content_parts.append("\n---\n")
                content_parts.append(attend_member.get_text(separator='\n', strip=True))

        if content_parts:
            return '\n'.join(content_parts)

        # 폴백: 전체 텍스트
        return super()._extract_full_content(soup, url)


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

    def _extract_full_content(self, soup: BeautifulSoup, url: str) -> str:
        """부산광역시의회 전체 회의록 본문 추출"""
        content_parts = []

        # 회의록 헤더 정보 (headBx)
        head_box = soup.select_one("#headBx")
        if head_box:
            header_text = head_box.get_text(separator='\n', strip=True)
            if header_text:
                content_parts.append(header_text)
                content_parts.append("\n---\n")

        # 모든 bodyBx-1 요소에서 발언 내용 추출
        body_elements = soup.select(".bodyBx-1")

        for elem in body_elements:
            # 발언자 정보
            speaker = elem.select_one(".member a, .member")
            if speaker:
                speaker_name = speaker.get_text(strip=True)
                if speaker_name:
                    content_parts.append(f"\n{speaker_name}")

            # 발언 내용
            text_div = elem.select_one(".text")
            if text_div:
                text = text_div.get_text(strip=True)
                if text:
                    content_parts.append(text)
            else:
                # .text가 없으면 직접 텍스트 추출
                direct_text = elem.get_text(strip=True)
                # 발언자 이름을 제외한 내용만
                if direct_text and speaker:
                    speaker_name = speaker.get_text(strip=True)
                    direct_text = direct_text.replace(speaker_name, '', 1).strip()
                if direct_text:
                    content_parts.append(direct_text)

        # 시간 정보
        time_areas = soup.select(".timeArea")
        for time_area in time_areas:
            time_text = time_area.get_text(strip=True)
            if time_text:
                # 이미 추가된 내용에 포함되어 있을 수 있으므로 확인
                pass

        if not content_parts:
            # 폴백: 기본 추출 방식 사용
            return super()._extract_full_content(soup, url)

        # 결과 조합
        result = '\n'.join(content_parts)
        # 연속 줄바꿈 정리
        result = re.sub(r'\n{3,}', '\n\n', result)
        return result.strip()


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
        # Xcom 시스템 (파주, 이천, 청주 등)
        "xcom": XcomCrawler,
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
        filename = self.output_dir / f"{council_code}.jsonl"

        with open(filename, "w", encoding="utf-8") as f:
            for item in results:
                line = json.dumps(item.to_dict(), ensure_ascii=False)
                f.write(line + "\n")

        return filename

    def save_json(self, council_code: str, results: List[MeetingMinutes]) -> Path:
        """JSON 형식으로 저장"""
        filename = self.output_dir / f"{council_code}.json"

        data = [item.to_dict() for item in results]

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, ensure_ascii=False, indent=2, fp=f)

        return filename

    def save_markdown(self, council_code: str, results: List[MeetingMinutes]) -> Path:
        """마크다운 형식으로 저장 (사람이 읽기 쉬운 형식)"""
        filename = self.output_dir / f"{council_code}.md"

        if not results:
            return filename

        council_name = results[0].council_name

        with open(filename, "w", encoding="utf-8") as f:
            # 헤더
            f.write(f"# {council_name} 회의록\n\n")
            f.write(f"수집건수: {len(results)}건\n\n")
            f.write("---\n\n")

            # 각 회의록
            for idx, item in enumerate(results, 1):
                f.write(f"## {idx}. {item.title}\n\n")

                # 메타 정보
                f.write("| 항목 | 내용 |\n")
                f.write("|------|------|\n")
                f.write(f"| 의회 | {item.council_name} |\n")
                if item.meeting_date:
                    f.write(f"| 일시 | {item.meeting_date} |\n")
                if item.assembly_number:
                    f.write(f"| 대수 | {item.assembly_number} |\n")
                if item.session_number:
                    f.write(f"| 회기 | {item.session_number} |\n")
                if item.meeting_type:
                    f.write(f"| 회의종류 | {item.meeting_type} |\n")
                if item.committee_name:
                    f.write(f"| 위원회 | {item.committee_name} |\n")
                if item.source_url:
                    f.write(f"| 원문URL | {item.source_url} |\n")
                if item.pdf_url:
                    f.write(f"| PDF | {item.pdf_url} |\n")
                if item.hwp_url:
                    f.write(f"| HWP | {item.hwp_url} |\n")

                f.write("\n")

                # 회의 내용 (전문 또는 미리보기)
                f.write("### 회의 내용\n\n")
                if item.full_content:
                    # 전체 내용 저장
                    f.write(f"{item.full_content}\n\n")
                elif item.content_preview:
                    # 하위호환: 미리보기만 있는 경우
                    f.write(f"{item.content_preview}\n\n")
                else:
                    f.write("(회의 내용을 가져올 수 없습니다)\n\n")

                f.write("---\n\n")

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
    parser.add_argument("--format", "-f", choices=["json", "jsonl", "both"], default="both", help="출력 형식: jsonl, json, both(jsonl+md) (기본: both)")
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

        if args.format == "both":
            # JSONL + Markdown 이중 출력 (기본값)
            output_file = saver.save_jsonl(args.council, results)
            md_file = saver.save_markdown(args.council, results)
            logger.info(f"저장 완료: {output_file}")
            logger.info(f"저장 완료: {md_file}")
        elif args.format == "jsonl":
            output_file = saver.save_jsonl(args.council, results)
            logger.info(f"저장 완료: {output_file}")
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
