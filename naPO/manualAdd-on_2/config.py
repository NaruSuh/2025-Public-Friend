"""
CLIK API 설정
국회지방의회의정포털 Open API
"""

# API 설정
API_KEY = "f293719a372b4afca79ac42e03a82273"
API_BASE_URL = "https://clik.nanet.go.kr/openapi"

# API 엔드포인트
ENDPOINTS = {
    "minutes": f"{API_BASE_URL}/minutes.do",      # 회의록
    "bills": f"{API_BASE_URL}/bills.do",          # 의안정보
    "members": f"{API_BASE_URL}/members.do",      # 의원정보
    "policy": f"{API_BASE_URL}/policy.do",        # 지방정책정보
}

# API 제한
API_LIMITS = {
    "max_per_call": 100,      # 1회 호출 최대 건수
    "max_daily_calls": 1000,  # 1일 최대 호출 횟수
    "max_daily_records": 100000,  # 1일 최대 레코드 수 (100 * 1000)
}

# 디렉토리 설정
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output" / "minutes"
LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"

# 파일 경로
COUNCIL_LIST_FILE = DATA_DIR / "councils.json"        # 의회 목록
PROGRESS_FILE = DATA_DIR / "progress.json"            # 진행 상황
DOCID_INDEX_FILE = DATA_DIR / "docid_index.json"      # 수집된 DOCID 인덱스

# 수집 설정
FETCH_CONFIG = {
    "batch_size": 100,           # API 1회 호출당 건수
    "delay_between_calls": 0.5,  # API 호출 간 딜레이 (초)
    "retry_count": 3,            # 실패 시 재시도 횟수
    "retry_delay": 2,            # 재시도 딜레이 (초)
}

# 디렉토리 생성
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
