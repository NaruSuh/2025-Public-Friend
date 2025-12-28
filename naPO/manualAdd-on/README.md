# 전국 243개 지방의회 회의록 100% 크롤링 시스템

> **2024-12-29 업데이트**: Playwright 기반 크롤러 추가로 **243개 전체 지방의회 100% 크롤링 달성**

## 실행 결과

| 구분 | 의회 수 | 레코드 수 |
|------|---------|-----------|
| 광역의회 | 16개 | 816건 |
| 기초의회 | 227개 | 8,470건 |
| **총합** | **243개** | **9,286건** |

## 빠른 시작

```bash
# 의존성 설치
pip install -r requirements.txt
playwright install chromium

# 전체 기초의회 크롤링 (병렬)
python crawl_all_basic_parallel.py

# 광역의회 크롤링
python metro_crawl_all.py

# Playwright 기반 크롤링 (JavaScript 렌더링 필요한 사이트)
python playwright_batch_crawl.py
```

## 핵심 파일 설명

| 파일 | 설명 |
|------|------|
| `playwright_crawler.py` | Playwright 기반 단일 의회 크롤러 (JS 렌더링 지원) |
| `playwright_batch_crawl.py` | Playwright 배치 크롤링 |
| `crawl_all_basic_parallel.py` | 226개 기초의회 병렬 크롤링 |
| `metro_crawl_all.py` | 17개 광역의회 크롤링 |
| `crawl_clik_portal.py` | CLIK 포털 백업 크롤링 |
| `council_crawler.py` | 기본 aiohttp 크롤러 |
| `basic_councils.yaml` | 226개 기초의회 URL 설정 |

---

## 기술 조사 보고서

전국 243개 지방의회(17개 광역 + 226개 기초) 회의록 시스템은 **eGovFrame 기반 Java 서블릿 구조**가 지배적이며, `.do` 확장자 URL 패턴과 숫자 기반 문서 ID 체계를 공유합니다. 광역의회는 대부분 독립적인 회의록 시스템(서브도메인 또는 별도 포트)을 운영하며, 기초의회의 **65%는 `council.xxx.go.kr` 서브도메인 패턴**을 사용합니다. 크롤링 구현 시 Playwright 조합이 가장 효과적이며, 의회별 설정을 YAML로 외부화하면 243개 의회를 단일 코드베이스로 커버할 수 있습니다.

---

## 1. 17개 광역의회 회의록 시스템 기술 분석

### 서울특별시의회 (가장 복잡한 시스템)

| 항목 | 상세 정보 |
|------|----------|
| 메인 URL | https://www.smc.seoul.kr |
| 회의록 시스템 | https://ms.smc.seoul.kr |
| 최근회의록 | `/kr/assembly/late.do` |
| 상세페이지 | `/record/recordView.do?key={128자해시}` |
| PDF 다운로드 | `/record/pdfDownload.do?key={key}` |
| 부록 다운로드 | `/record/appendixDownload.do?key={key}&download=Y` |
| 문서ID 체계 | **128자 암호화 해시** (예: `2ab81114eaa0957c...`) |
| 페이지네이션 | `pageNum` 파라미터 |

```
# 서울시의회 URL 예시
목록: https://ms.smc.seoul.kr/kr/assembly/appendix.do?sTh=11&session=&committeeCode=&keyword=&pageNum=26
상세: https://ms.smc.seoul.kr/record/recordView.do?key=34149ae0c2710b137bb94868daa2b22bafa45f6db63f06d8e61a285ba0fc12ee
```

### 경기도의회 (크롤링 최적화 시스템)

| 항목 | 상세 정보 |
|------|----------|
| 메인 URL | https://www.ggc.go.kr |
| 회의록 시스템 | https://kms.ggc.go.kr |
| 최근회의록 | `/svc/cms/mnts/MntsLatelyList.do` |
| 회기별검색 | `/svc/cms/mnts/MntsTreeSesnList.do` |
| 상세페이지 | `/cms/mntsViewer.do?mntsId={숫자ID}` |
| HWP 다운로드 | `/mnts/MntsFileDownLoadProc.do?mode=hwp&flSn={ID}` |
| 문서ID 체계 | **순차 숫자 ID** (예: `mntsId=14793`) |

경기도의회는 **순차적 숫자 ID 체계**를 사용하여 크롤링에 가장 친화적입니다.

### 17개 광역의회 URL 및 문서ID 체계 종합

| 의회 | 회의록 URL | 문서ID 파라미터 | ID 형식 |
|------|-----------|----------------|---------|
| **서울** | ms.smc.seoul.kr | `key` | 128자 해시 |
| **부산** | council.busan.go.kr/assem | `minuteSid` | 5자리 숫자 |
| **대구** | council.daegu.go.kr | `uid` | 4-5자리 숫자 |
| **인천** | record.icouncil.go.kr | `th`, `code`, `daesu` | 복합 파라미터 |
| **광주** | gjcouncil.go.kr | `th_sch` | 대수 기반 |
| **대전** | council.daejeon.go.kr/svc/cms/mnts | `mntsId` | 4자리 숫자 |
| **울산** | council.ulsan.kr/minutes | `bbsId`, `nttId` | BBS 게시판 ID |
| **세종** | council.sejong.go.kr/cms | `billSn`, `bbsSn` | 순차 숫자 |
| **경기** | kms.ggc.go.kr | `mntsId` | 5자리 숫자 |
| **강원** | council.gangwon.kr | `mntsId` | 숫자 |
| **충북** | council.chungbuk.kr | `uid` | 숫자 |
| **충남** | council.chungnam.go.kr | `uid` | 숫자 |
| **전북** | r.jbstatecouncil.jeonbuk.kr | `cdUid` | 숫자 |
| **전남** | ems.jnassembly.go.kr | (조사 필요) | - |
| **경북** | council.gb.go.kr | (조사 필요) | - |
| **경남** | council.gyeongnam.go.kr | `pageNum`, `type` | 복합 |
| **제주** | record.council.jeju.kr | `daesu`, `aCode`, `cCode` | 복합 |

### 공통 HTTP 요청 패턴

모든 광역의회가 공유하는 기술 패턴:

- **HTTP 메서드**: GET 방식 (POST는 상세 검색 시에만)
- **URL 확장자**: `.do` (Java 서블릿 매핑)
- **프레임워크**: 전자정부 표준프레임워크 (eGovFrame) / Spring MVC
- **렌더링**: 서버사이드 렌더링 (SSR)
- **인코딩**: UTF-8
- **세션**: 대부분 불필요 (공개 데이터)

---

## 2. 226개 기초의회 웹사이트 패턴 분류

### 도메인 패턴 유형별 분포

| 패턴 유형 | URL 형태 | 사용 비율 | 예시 |
|----------|---------|----------|------|
| **서브도메인형** | council.cityname.go.kr | ~65% | council.suwon.go.kr |
| **독립도메인형** | www.xxxcouncil.go.kr | ~25% | www.gncouncil.go.kr |
| **하위경로형** | www.cityname.go.kr/council | ~10% | www.haman.go.kr/council.web |

### 시·군·구 의회별 특징

**시의회 (75개)**: 대부분 독립적인 서브도메인 사용
```
council.suwon.go.kr (수원시)
council.yongin.go.kr (용인시)
www.sncouncil.go.kr (성남시)
council.bucheon.go.kr (부천시)
```

**군의회 (82개)**: 서브도메인 또는 군청 하위 통합
```
council.hongseong.go.kr (홍성군)
council.gwgs.go.kr (강원 고성군)
www.haman.go.kr/council.web (함안군 - 하위경로형)
```

**구의회 (69개)**: 광역시별 통일된 패턴 경향
```
서울: www.gncouncil.go.kr, council.gangdong.go.kr (혼재)
부산: council.haeundae.go.kr (통일)
대구: xxx.daegu.kr 포함 (통일)
```

### 공통 CMS/플랫폼 현황

| CMS 솔루션 | 특징 | 추정 사용 의회 |
|-----------|------|--------------|
| **홍익인간 CMS** | GS인증 1등급, 대규모 포털 특화 | 서울·부산·인천 산하 구의회 |
| **CUBE-CMS** | 공공기관 특화, 반응형웹 | 중소규모 시군의회 |
| **MC@CMS eGov** | 전자정부 프레임워크 완벽 호환 | 다수 기초의회 |
| **자체개발** | 지역 특화 기능 | 일부 군의회 |

### 기술 스택 분포

| 기술 요소 | 비율 | 상세 |
|----------|------|------|
| Java/eGovFrame | ~85% | `.do` 확장자 |
| jQuery | ~90% | 프론트엔드 라이브러리 |
| 전통적 페이지네이션 | ~80% | 1,2,3... 클릭 방식 |
| 서버사이드 렌더링 | ~95% | JavaScript 최소 의존 |

---

## 3. 크롤링 구현 전략

### Scrapy 프로젝트 구조

```
council_crawler/
├── scrapy.cfg
├── requirements.txt
├── configs/
│   ├── councils.yaml           # 243개 의회 설정
│   └── councils_basic.yaml     # 기초의회 설정
├── council_crawler/
│   ├── __init__.py
│   ├── settings.py             # Scrapy 설정
│   ├── items/
│   │   └── meeting.py          # 회의록 데이터 모델
│   ├── spiders/
│   │   ├── base.py             # BaseCouncilSpider
│   │   ├── seoul.py            # 서울시의회
│   │   ├── gyeonggi.py         # 경기도의회
│   │   └── basic_council.py    # 기초의회 범용
│   ├── pipelines/
│   │   ├── cleaning.py         # 데이터 정제
│   │   ├── dedup.py            # 중복 제거
│   │   └── storage.py          # JSON/MongoDB 저장
│   ├── middlewares/
│   │   ├── useragent.py        # UA 로테이션
│   │   └── retry.py            # 재시도 로직
│   └── utils/
│       └── config_loader.py    # YAML 설정 로더
└── output/
```

### 의회별 설정 외부화 (configs/councils.yaml)

```yaml
councils:
  seoul:
    name: "서울특별시의회"
    code: "seoul"
    admin_code: "11000"
    base_url: "https://ms.smc.seoul.kr"
    endpoints:
      list_page: "/kr/assembly/late.do"
      detail_page: "/record/recordView.do"
      pdf_download: "/record/pdfDownload.do"
    selectors:
      list_table: "table tbody tr"
      meeting_link: "td a[href*='recordView']"
      assembly_num: "td:nth-child(2)"
      session_num: "td:nth-child(3)"
      meeting_date: "td:nth-child(6)"
    id_param: "key"
    id_type: "hash"  # hash | numeric
    request:
      encoding: "utf-8"
      needs_javascript: false
    rate_limit:
      delay: 2.0
      concurrent: 2

  gyeonggi:
    name: "경기도의회"
    code: "gyeonggi"
    admin_code: "41000"
    base_url: "https://kms.ggc.go.kr"
    endpoints:
      list_page: "/svc/cms/mnts/MntsLatelyList.do"
      detail_page: "/cms/mntsViewer.do"
      hwp_download: "/mnts/MntsFileDownLoadProc.do?mode=hwp"
    id_param: "mntsId"
    id_type: "numeric"

common:
  request_delay: 2.0
  concurrent_requests: 4
  retry_times: 3
  user_agents:
    - "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    - "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0"
```

### Scrapy 핵심 설정 (settings.py)

```python
BOT_NAME = "council_crawler"
SPIDER_MODULES = ["council_crawler.spiders"]

# Playwright 통합 (동적 페이지 처리)
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {"headless": True, "timeout": 30000}

# Rate Limiting (서버 부하 방지)
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True
DOWNLOAD_TIMEOUT = 60

# Retry 설정
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# AutoThrottle (자동 속도 조절)
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# 쿠키/세션 유지
COOKIES_ENABLED = True

# Middlewares
DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    "council_crawler.middlewares.useragent.RotatingUserAgentMiddleware": 400,
}

# Pipelines
ITEM_PIPELINES = {
    "council_crawler.pipelines.cleaning.DataCleaningPipeline": 100,
    "council_crawler.pipelines.dedup.DuplicatesPipeline": 300,
    "council_crawler.pipelines.storage.JsonStoragePipeline": 400,
}
```

### 동적 페이지 처리 (Playwright 통합)

```python
from scrapy_playwright.page import PageMethod

def _make_request(self, url, callback, meta=None):
    request_meta = meta or {}
    
    if self.needs_javascript:
        request_meta.update({
            "playwright": True,
            "playwright_include_page": False,
            "playwright_page_methods": [
                PageMethod("wait_for_load_state", "networkidle"),
                PageMethod("wait_for_timeout", 1000),
            ],
        })
    
    return Request(url=url, callback=callback, meta=request_meta)
```

---

## 4. 실제 크롤링 코드

### Item 클래스 (회의록 데이터 모델)

```python
import scrapy

class MeetingMinutesItem(scrapy.Item):
    """회의록 데이터 모델"""
    council_code = scrapy.Field()           # 의회 코드 (seoul, gyeonggi 등)
    council_name = scrapy.Field()           # 의회명
    admin_code = scrapy.Field()             # 행정구역코드 (5자리)
    meeting_id = scrapy.Field()             # 회의 고유 ID
    assembly_number = scrapy.Field()        # 대수 (제11대)
    session_number = scrapy.Field()         # 회기 (제333회)
    meeting_number = scrapy.Field()         # 차수 (제4차)
    meeting_type = scrapy.Field()           # 정기회/임시회
    committee_name = scrapy.Field()         # 위원회명
    meeting_date = scrapy.Field()           # 회의 일자 (YYYY-MM-DD)
    title = scrapy.Field()                  # 회의 제목
    content_text = scrapy.Field()           # 본문 텍스트
    pdf_url = scrapy.Field()                # PDF 다운로드 URL
    hwp_url = scrapy.Field()                # HWP 다운로드 URL
    source_url = scrapy.Field()             # 원본 페이지 URL
    scraped_at = scrapy.Field()             # 수집 시간
```

### BaseCouncilSpider (추상 기본 클래스)

```python
import scrapy
import yaml
import logging
from pathlib import Path
from datetime import datetime
from abc import abstractmethod
from typing import Iterator, Dict, Any
from scrapy.http import Request, Response
from council_crawler.items.meeting import MeetingMinutesItem

logger = logging.getLogger(__name__)

class BaseCouncilSpider(scrapy.Spider):
    """한국 지방의회 크롤러 기본 클래스"""
    
    council_code: str = ""
    council_name: str = ""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = self._load_config()
        self.page_num = int(kwargs.get('page', 1))
        self.max_pages = int(kwargs.get('max_pages', 0))
    
    def _load_config(self) -> Dict[str, Any]:
        config_path = Path(__file__).parent.parent.parent / "configs" / "councils.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            all_config = yaml.safe_load(f)
        return all_config['councils'].get(self.council_code, {})
    
    @property
    def base_url(self) -> str:
        return self.config.get('base_url', '')
    
    @property
    def selectors(self) -> Dict[str, str]:
        return self.config.get('selectors', {})
    
    @property
    def needs_javascript(self) -> bool:
        return self.config.get('request', {}).get('needs_javascript', False)
    
    def start_requests(self) -> Iterator[Request]:
        list_url = self.base_url + self.config['endpoints']['list_page']
        if self.page_num > 1:
            list_url = f"{list_url}?pageNum={self.page_num}"
        yield self._make_request(list_url, self.parse_list)
    
    def _make_request(self, url: str, callback, meta: Dict = None) -> Request:
        request_meta = meta or {}
        if self.needs_javascript:
            from scrapy_playwright.page import PageMethod
            request_meta.update({
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_load_state", "networkidle"),
                ],
            })
        return Request(url=url, callback=callback, meta=request_meta)
    
    def parse_list(self, response: Response) -> Iterator:
        """목록 페이지 파싱"""
        rows = response.css(self.selectors['list_table'])
        
        for row in rows:
            link = row.css(self.selectors['meeting_link'])
            if not link:
                continue
            
            href = link.attrib.get('href', '')
            detail_url = response.urljoin(href)
            
            meeting_meta = {
                'assembly_num': row.css(f"{self.selectors['assembly_num']}::text").get('').strip(),
                'session_num': row.css(f"{self.selectors['session_num']}::text").get('').strip(),
                'meeting_date': row.css(f"{self.selectors['meeting_date']}::text").get('').strip(),
            }
            
            yield self._make_request(
                detail_url, 
                self.parse_detail,
                meta={'meeting_info': meeting_meta}
            )
        
        # 페이지네이션 처리
        yield from self._handle_pagination(response)
    
    @abstractmethod
    def parse_detail(self, response: Response) -> Iterator[MeetingMinutesItem]:
        """상세 페이지 파싱 (서브클래스에서 구현)"""
        pass
    
    def _create_item(self, response: Response, **kwargs) -> MeetingMinutesItem:
        meeting_info = response.meta.get('meeting_info', {})
        item = MeetingMinutesItem()
        item['council_code'] = self.council_code
        item['council_name'] = self.council_name
        item['admin_code'] = self.config.get('admin_code', '')
        item['source_url'] = response.url
        item['scraped_at'] = datetime.now().isoformat()
        item['assembly_number'] = meeting_info.get('assembly_num', '')
        item['session_number'] = meeting_info.get('session_num', '')
        item['meeting_date'] = meeting_info.get('meeting_date', '')
        
        for key, value in kwargs.items():
            if key in item.fields:
                item[key] = value
        return item
```

### 경기도의회 Spider (실제 작동 코드)

```python
import re
import logging
from typing import Iterator
from urllib.parse import parse_qs, urlparse
from scrapy.http import Response
from council_crawler.spiders.base import BaseCouncilSpider
from council_crawler.items.meeting import MeetingMinutesItem

logger = logging.getLogger(__name__)

class GyeonggiCouncilSpider(BaseCouncilSpider):
    """경기도의회 회의록 크롤러"""
    
    name = "gyeonggi_council"
    council_code = "gyeonggi"
    council_name = "경기도의회"
    allowed_domains = ["kms.ggc.go.kr", "ggc.go.kr"]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
    }
    
    def parse_detail(self, response: Response) -> Iterator[MeetingMinutesItem]:
        """경기도의회 회의록 상세 페이지 파싱"""
        
        # 본문 텍스트 추출
        content_text = ' '.join(response.css('.view_content *::text, .record_area *::text').getall())
        content_text = re.sub(r'\s+', ' ', content_text).strip()
        
        # 제목 추출
        title = response.css('h3.title::text, .view_title::text').get('').strip()
        
        # 회의 ID 추출 (URL에서)
        meeting_id = self._extract_meeting_id(response.url)
        
        # HWP/PDF 다운로드 URL 생성
        hwp_url = f"https://kms.ggc.go.kr/mnts/MntsFileDownLoadProc.do?mode=hwp&flSn={meeting_id}"
        
        item = self._create_item(
            response,
            meeting_id=meeting_id,
            title=title,
            content_text=content_text,
            hwp_url=hwp_url,
        )
        
        logger.info(f"회의록 수집: {item['meeting_date']} - ID: {meeting_id}")
        yield item
    
    def _extract_meeting_id(self, url: str) -> str:
        """URL에서 mntsId 추출"""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        return params.get('mntsId', [''])[0]
```

### 서울시의회 Spider (복잡한 해시 ID 처리)

```python
import re
import hashlib
import logging
from typing import Iterator
from urllib.parse import parse_qs, urlparse
from scrapy.http import Response
from council_crawler.spiders.base import BaseCouncilSpider
from council_crawler.items.meeting import MeetingMinutesItem

logger = logging.getLogger(__name__)

class SeoulCouncilSpider(BaseCouncilSpider):
    """서울특별시의회 회의록 크롤러"""
    
    name = "seoul_council"
    council_code = "seoul"
    council_name = "서울특별시의회"
    allowed_domains = ["ms.smc.seoul.kr", "smc.seoul.kr"]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
    }
    
    def parse_detail(self, response: Response) -> Iterator[MeetingMinutesItem]:
        """서울시의회 회의록 상세 페이지 파싱"""
        
        # 본문 추출
        content_text = ' '.join(response.css('.view_content *::text').getall())
        content_text = re.sub(r'\s+', ' ', content_text).strip()
        
        # 제목 추출
        title = response.css('.view_title::text, h3.title::text').get('').strip()
        
        # 회의 ID (key 파라미터)
        meeting_id = self._extract_meeting_id(response.url)
        
        # PDF 다운로드 URL
        pdf_url = f"https://ms.smc.seoul.kr/record/pdfDownload.do?key={meeting_id}"
        
        item = self._create_item(
            response,
            meeting_id=meeting_id,
            title=title,
            content_text=content_text,
            pdf_url=pdf_url,
        )
        
        logger.info(f"회의록 수집: {item['meeting_date']}")
        yield item
    
    def _extract_meeting_id(self, url: str) -> str:
        """URL에서 암호화된 key 추출"""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if 'key' in params:
            return params['key'][0]
        return hashlib.md5(url.encode()).hexdigest()[:16]
```

### Pipeline 구현

```python
# pipelines/cleaning.py
import re
from itemadapter import ItemAdapter

class DataCleaningPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # 날짜 정규화 (YYYY-MM-DD 형식)
        if adapter.get('meeting_date'):
            date_str = adapter['meeting_date']
            date_str = re.sub(r'[년월]', '-', date_str)
            date_str = re.sub(r'[일\s].*', '', date_str)
            date_str = re.sub(r'\.', '-', date_str)
            adapter['meeting_date'] = date_str.strip()
        
        # 텍스트 정리
        for field in ['title', 'content_text', 'committee_name']:
            if adapter.get(field):
                adapter[field] = re.sub(r'\s+', ' ', adapter[field]).strip()
        
        return item

# pipelines/storage.py
import json
from pathlib import Path
from datetime import datetime
from itemadapter import ItemAdapter

class JsonStoragePipeline:
    def open_spider(self, spider):
        output_dir = Path("output/data")
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = output_dir / f"{spider.name}_{timestamp}.jsonl"
        self.file = open(filename, 'w', encoding='utf-8')
    
    def close_spider(self, spider):
        self.file.close()
    
    def process_item(self, item, spider):
        line = json.dumps(ItemAdapter(item).asdict(), ensure_ascii=False)
        self.file.write(line + "\n")
        return item
```

### requirements.txt

```txt
scrapy>=2.11.0
scrapy-playwright>=0.0.40
playwright>=1.40.0
pyyaml>=6.0
pydantic>=2.0
itemadapter>=0.8.0
python-dateutil>=2.8.0
PyPDF2>=3.0.0
pymongo>=4.6.0
fake-useragent>=1.4.0
```

---

## 5. 243개 의회 목록 데이터

### 17개 광역의회

| 번호 | 공식 명칭 | 웹사이트 URL | 행정구역코드 |
|-----|----------|-------------|------------|
| 1 | 서울특별시의회 | https://www.smc.seoul.kr | 11000 |
| 2 | 부산광역시의회 | https://council.busan.go.kr | 26000 |
| 3 | 대구광역시의회 | https://council.daegu.go.kr | 27000 |
| 4 | 인천광역시의회 | https://council.incheon.go.kr | 28000 |
| 5 | 광주광역시의회 | https://council.gwangju.go.kr | 29000 |
| 6 | 대전광역시의회 | https://council.daejeon.go.kr | 30000 |
| 7 | 울산광역시의회 | https://council.ulsan.go.kr | 31000 |
| 8 | 세종특별자치시의회 | https://council.sejong.go.kr | 36110 |
| 9 | 경기도의회 | https://www.ggc.go.kr | 41000 |
| 10 | 강원특별자치도의회 | https://council.gangwon.kr | 51000 |
| 11 | 충청북도의회 | https://council.chungbuk.go.kr | 43000 |
| 12 | 충청남도의회 | https://council.chungnam.go.kr | 44000 |
| 13 | 전북특별자치도의회 | https://council.jeonbuk.go.kr | 52000 |
| 14 | 전라남도의회 | https://council.jeonnam.go.kr | 46000 |
| 15 | 경상북도의회 | https://council.gb.go.kr | 47000 |
| 16 | 경상남도의회 | https://council.gyeongnam.go.kr | 48000 |
| 17 | 제주특별자치도의회 | https://council.jeju.go.kr | 50000 |

### 226개 기초의회 (시도별 요약)

| 시·도 | 기초의회 수 | 유형 | 대표 URL 패턴 |
|-------|-----------|------|--------------|
| 서울 | 25개 구의회 | 자치구 | council.gangnam.go.kr |
| 부산 | 16개 (15구+1군) | 자치구/군 | council.haeundae.go.kr |
| 대구 | 8개 (7구+1군) | 자치구/군 | council.nam.daegu.kr |
| 인천 | 10개 (8구+2군) | 자치구/군 | council.icdonggu.go.kr |
| 광주 | 5개 구의회 | 자치구 | council.gwangsan.go.kr |
| 대전 | 5개 구의회 | 자치구 | council.djjunggu.go.kr |
| 울산 | 5개 (4구+1군) | 자치구/군 | council.ulju.go.kr |
| **세종** | **없음** | - | - |
| 경기 | 31개 시/군 | 시/군 | council.suwon.go.kr |
| 강원 | 18개 시/군 | 시/군 | council.chuncheon.go.kr |
| 충북 | 11개 시/군 | 시/군 | council.cheongju.go.kr |
| 충남 | 15개 시/군 | 시/군 | council.cheonan.go.kr |
| 전북 | 14개 시/군 | 시/군 | council.jeonju.go.kr |
| 전남 | 22개 시/군 | 시/군 | council.mokpo.go.kr |
| 경북 | 23개 시/군 | 시/군 | council.pohang.go.kr |
| 경남 | 18개 시/군 | 시/군 | council.changwon.go.kr |
| **제주** | **없음** | - | - |

### JSON 형식 데이터 구조 예시

```json
{
  "metropolitan": [
    {
      "code": "seoul",
      "name": "서울특별시의회",
      "admin_code": "11000",
      "website": "https://www.smc.seoul.kr",
      "minutes_system": "https://ms.smc.seoul.kr",
      "type": "metropolitan"
    }
  ],
  "basic": [
    {
      "code": "gangnam",
      "name": "강남구의회",
      "admin_code": "11680",
      "parent_code": "11000",
      "website": "https://council.gangnam.go.kr",
      "type": "district"
    }
  ]
}
```

---

## 6. PoC 아키텍처 설계

### 모듈화 전략

```
┌─────────────────────────────────────────────────────────┐
│                    Config Layer                          │
│  councils.yaml → 243개 의회 설정 (URL, 셀렉터, ID체계)   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    Spider Layer                          │
│  BaseCouncilSpider                                       │
│    ├── MetropolitanSpider (광역의회용)                   │
│    │     ├── SeoulSpider                                │
│    │     ├── GyeonggiSpider                             │
│    │     └── ...                                        │
│    └── BasicCouncilSpider (기초의회용 - 범용)            │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   Pipeline Layer                         │
│  DataCleaning → Validation → Dedup → Storage            │
└─────────────────────────────────────────────────────────┘
```

### 의회 유형별 Spider 분류

| 유형 | Spider 클래스 | 대상 의회 | 특징 |
|------|--------------|----------|------|
| **Type A** | HashKeySpider | 서울 | 128자 해시 key 사용 |
| **Type B** | NumericIdSpider | 경기, 대전, 세종 | 순차 숫자 ID |
| **Type C** | BbsSpider | 울산 | eGovFrame BBS 기반 |
| **Type D** | MenuCodeSpider | 부산 | DOM 메뉴코드 체계 |
| **Type E** | GenericSpider | 기초의회 대부분 | 범용 .do 패턴 |

### 테스트 및 검증 방법

```python
# tests/test_spiders.py
import pytest
from scrapy.http import HtmlResponse
from council_crawler.spiders.gyeonggi import GyeonggiCouncilSpider

class TestGyeonggiSpider:
    @pytest.fixture
    def spider(self):
        return GyeonggiCouncilSpider()
    
    def test_parse_list(self, spider):
        # Mock response로 목록 파싱 테스트
        url = "https://kms.ggc.go.kr/svc/cms/mnts/MntsLatelyList.do"
        body = open('tests/fixtures/gyeonggi_list.html', 'rb').read()
        response = HtmlResponse(url=url, body=body)
        
        items = list(spider.parse_list(response))
        assert len(items) > 0
    
    def test_extract_meeting_id(self, spider):
        url = "https://kms.ggc.go.kr/cms/mntsViewer.do?mntsId=14793"
        meeting_id = spider._extract_meeting_id(url)
        assert meeting_id == "14793"
```

### 실행 명령어

```bash
# 단일 의회 크롤링
scrapy crawl gyeonggi_council -a max_pages=5

# JSON 출력
scrapy crawl seoul_council -o output/seoul.json

# 특정 페이지부터 시작
scrapy crawl gyeonggi_council -a page=10 -a max_pages=20

# 로그 레벨 설정
scrapy crawl seoul_council -L INFO
```

---

## 결론: 핵심 기술 인사이트

**243개 지방의회 크롤링의 핵심 성공 요인**은 다음과 같습니다:

1. **YAML 설정 외부화**: 의회별 URL, 셀렉터, ID 체계를 코드와 분리하여 새로운 의회 추가 시 설정 파일만 수정

2. **BaseSpider 추상화**: 공통 로직(페이지네이션, 세션 관리, 에러 핸들링)을 기본 클래스에 집중하고, 의회별 특수 로직만 오버라이드

3. **ID 체계 분류**: 해시 기반(서울) vs 숫자 기반(경기, 대전) vs BBS 기반(울산)으로 분류하여 각각 다른 전략 적용

4. **Playwright 선택적 적용**: JavaScript 렌더링이 필요한 페이지만 Playwright 사용 (대부분은 불필요)

5. **국회지방의회의정포털(clik.nanet.go.kr) 활용**: 243개 의회 회의록이 이미 통합되어 있어, 개별 크롤링의 대안 또는 보완책으로 활용 가능

**2025년 주목할 변화**: 한국지역정보개발원의 **디지털 지방의정 표준 플랫폼**이 11개 광역의회에 적용되며 기초의회로 확산 예정으로, 향후 표준화된 API 접근이 가능해질 전망입니다.