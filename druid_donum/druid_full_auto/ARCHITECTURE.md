# Universal Board Crawler - Architecture Document

**Version**: 2.0.0
**Last Updated**: 2025-10-05
**Status**: Design Phase

---

## Executive Summary

**현재 상태**: 산림청 입찰정보 게시판 전용 크롤러
**목표**: 범용 게시판 크롤러 플랫폼으로 확장

### 핵심 비전
사용자가 **어떤 웹사이트의 게시판이든** 설정만으로 크롤링 가능한 플러그인 기반 범용 시스템

---

## Current System Analysis

### 기존 시스템 구조
```
druid_full_auto/
├── app.py           # Streamlit UI (500+ lines)
├── main.py          # ForestBidCrawler 클래스 (산림청 전용)
├── requirements.txt
└── .streamlit/config.toml
```

### 문제점
1. **하드코딩된 파싱 로직**: 산림청 HTML 구조에 종속
2. **단일 사이트 전용**: 다른 사이트 추가 시 코드 전체 수정 필요
3. **모놀리식 구조**: UI/크롤러/파싱 로직이 밀결합
4. **확장성 부족**: 새로운 사이트마다 fork 필요

---

## Target Architecture (v2.0)

### 디렉토리 구조
```
universal-board-crawler/
├── docs/
│   ├── ARCHITECTURE.md          # 이 문서
│   ├── LLM_COLLABORATION.md     # 멀티 LLM CLI 협업 가이드
│   ├── PLUGIN_DEVELOPMENT.md    # 플러그인 개발 가이드
│   ├── API_REFERENCE.md         # API 문서
│   └── CURRENT_STATUS.md        # 현재 진행 상황
│
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── base_crawler.py      # 추상 베이스 클래스
│   │   ├── parser_factory.py    # 파서 팩토리 패턴
│   │   ├── data_exporter.py     # Excel/CSV 내보내기
│   │   └── session_manager.py   # 세션/캐시 관리
│   │
│   ├── plugins/
│   │   ├── __init__.py
│   │   ├── base_plugin.py       # 플러그인 인터페이스
│   │   ├── forest_korea/        # 산림청 플러그인
│   │   │   ├── __init__.py
│   │   │   ├── crawler.py
│   │   │   ├── parser.py
│   │   │   └── config.yaml
│   │   └── template/            # 플러그인 템플릿
│   │       ├── crawler.py
│   │       ├── parser.py
│   │       └── config.yaml
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── streamlit_app.py     # 메인 UI
│   │   ├── components/          # 재사용 가능 UI 컴포넌트
│   │   │   ├── date_selector.py
│   │   │   ├── status_monitor.py
│   │   │   └── data_preview.py
│   │   └── themes/
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       ├── validators.py
│       └── html_helpers.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── plugins/
│
├── .llm/                         # LLM 협업 설정
│   ├── claude_context.md        # Claude Code 전용 컨텍스트
│   ├── gemini_context.md        # Gemini CLI 전용 컨텍스트
│   ├── codex_context.md         # Codex CLI 전용 컨텍스트
│   ├── task_assignments.yaml    # 작업 분담 명세
│   └── sync_protocol.md         # 동기화 프로토콜
│
├── config/
│   ├── app_config.yaml
│   └── plugins_registry.yaml
│
├── requirements.txt
├── setup.py
├── README.md
└── CHANGELOG.md
```

---

## Core Abstractions

### 1. BaseCrawler (추상 클래스)
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import date

class BaseCrawler(ABC):
    """모든 크롤러가 상속해야 하는 기본 클래스"""

    @abstractmethod
    def fetch_page(self, url: str, params: Dict) -> BeautifulSoup:
        """페이지 가져오기"""
        pass

    @abstractmethod
    def parse_list(self, soup: BeautifulSoup) -> List[Dict]:
        """리스트 페이지 파싱"""
        pass

    @abstractmethod
    def parse_detail(self, soup: BeautifulSoup, item: Dict) -> Dict:
        """상세 페이지 파싱"""
        pass

    @abstractmethod
    def build_params(self, page: int, start_date: date, end_date: date) -> Dict:
        """요청 파라미터 생성 (사이트마다 다름)"""
        pass
```

### 2. Plugin Interface
```python
class BoardPlugin(ABC):
    """게시판 플러그인 인터페이스"""

    @property
    @abstractmethod
    def name(self) -> str:
        """플러그인 이름"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """플러그인 버전"""
        pass

    @abstractmethod
    def get_crawler(self) -> BaseCrawler:
        """크롤러 인스턴스 반환"""
        pass

    @abstractmethod
    def validate_config(self, config: Dict) -> bool:
        """설정 검증"""
        pass
```

### 3. Plugin Configuration (YAML)
```yaml
# plugins/forest_korea/config.yaml
plugin:
  name: "forest_korea"
  display_name: "산림청 입찰정보"
  version: "1.0.0"
  author: "NaruSuh"

site:
  base_url: "https://www.forest.go.kr"
  list_url: "https://www.forest.go.kr/kfsweb/cop/bbs/selectBoardList.do"
  detail_url: "https://www.forest.go.kr/kfsweb/cop/bbs/selectBoardArticle.do"

crawling:
  supports_date_filter: true
  date_param_format: "YYYY-MM-DD"
  date_param_names:
    start: "ntcStartDt"
    end: "ntcEndDt"
  max_items_per_page: 10

parsing:
  list_selector: "table tbody tr"
  fields:
    - name: "number"
      selector: "td:nth-child(1)"
      type: "text"
    - name: "title"
      selector: "a"
      type: "text"
    - name: "date"
      selector: "td:nth-child(4)"
      type: "date"
      regex: "(\d{4}-\d{2}-\d{2})"
```

---

## Multi-LLM Collaboration Strategy

### 역할 분담

#### Claude Code (리드 아키텍트)
- **책임**: 전체 아키텍처 설계 및 코어 시스템 구현
- **작업**:
  - `src/core/` 모듈 개발
  - 플러그인 인터페이스 설계
  - 복잡한 리팩토링
- **강점**: 긴 컨텍스트, 리팩토링, 아키텍처 설계

#### Gemini CLI (플러그인 개발자)
- **책임**: 개별 사이트 플러그인 개발
- **작업**:
  - `src/plugins/` 하위 플러그인 구현
  - HTML 파싱 로직
  - 사이트별 특수 처리
- **강점**: 빠른 코드 생성, 패턴 인식

#### Codex CLI (테스트 & 문서화)
- **책임**: 테스트 코드 작성 및 문서 생성
- **작업**:
  - `tests/` 디렉토리 전체
  - API 문서 자동 생성
  - 예제 코드 작성
- **강점**: 테스트 커버리지, 문서 자동화

### 협업 프로토콜

1. **작업 시작 전**: `.llm/task_assignments.yaml` 확인
2. **작업 중**: `docs/CURRENT_STATUS.md` 실시간 업데이트
3. **작업 완료 후**: 다음 LLM을 위한 컨텍스트 작성
4. **충돌 방지**: 파일 단위 잠금 (`.llm/locks/`)

---

## Migration Path (기존 → 신규)

### Phase 1: 준비 (1주)
- [ ] 문서 작성 완료
- [ ] 디렉토리 구조 생성
- [ ] 코어 추상 클래스 정의

### Phase 2: 리팩토링 (2주)
- [ ] 기존 `main.py` → `plugins/forest_korea/crawler.py`로 이동
- [ ] UI 로직 분리 (`app.py` → `src/ui/`)
- [ ] 플러그인 시스템 구현

### Phase 3: 확장 (2주)
- [ ] 2-3개 추가 사이트 플러그인 개발
- [ ] UI에서 플러그인 선택 기능
- [ ] 설정 파일 기반 동적 로딩

### Phase 4: 최적화 (1주)
- [ ] 성능 튜닝
- [ ] 에러 핸들링 강화
- [ ] 문서 완성도 향상

---

## Success Criteria

1. **확장성**: 새 사이트 추가 시 10분 내 플러그인 작성 가능
2. **안정성**: 기존 산림청 크롤러 기능 100% 유지
3. **협업성**: 3개 LLM CLI가 충돌 없이 동시 작업 가능
4. **사용성**: 비개발자도 config.yaml만 수정으로 사이트 추가 가능

---

## Risk & Mitigation

| 리스크 | 영향 | 완화 방안 |
|--------|------|-----------|
| 기존 기능 깨짐 | 🔴 High | 통합 테스트 100% 커버리지 |
| LLM 간 충돌 | 🟡 Medium | 파일 잠금 시스템 |
| 과도한 복잡성 | 🟡 Medium | YAGNI 원칙, 점진적 구현 |
| 성능 저하 | 🟢 Low | 프로파일링, 캐싱 |

---

## Next Steps

1. `LLM_COLLABORATION.md` 작성 (멀티 CLI 워크플로우)
2. `PLUGIN_DEVELOPMENT.md` 작성 (플러그인 개발 가이드)
3. 코어 추상 클래스 구현
4. 산림청 플러그인으로 마이그레이션
