"""
CLIK API 클라이언트
"""

import requests
import time
import json
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging

from config import (
    API_KEY, ENDPOINTS, API_LIMITS, FETCH_CONFIG, LOG_DIR
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f"api_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CLIKApiClient:
    """CLIK Open API 클라이언트"""

    def __init__(self):
        self.api_key = API_KEY
        self.session = requests.Session()
        self.call_count = 0
        self.last_call_time = 0

    def _make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """API 요청 실행"""
        params['key'] = self.api_key
        params['type'] = 'json'

        # 호출 간 딜레이
        elapsed = time.time() - self.last_call_time
        if elapsed < FETCH_CONFIG['delay_between_calls']:
            time.sleep(FETCH_CONFIG['delay_between_calls'] - elapsed)

        for attempt in range(FETCH_CONFIG['retry_count']):
            try:
                response = self.session.get(endpoint, params=params, timeout=30)
                self.last_call_time = time.time()
                self.call_count += 1

                if response.status_code == 200:
                    data = response.json()

                    # API 응답이 리스트인 경우 첫 번째 요소 사용
                    if isinstance(data, list) and len(data) > 0:
                        data = data[0]

                    if data.get('RESULT_CODE') == 'SUCCESS':
                        return data
                    else:
                        logger.warning(f"API 오류: {data.get('RESULT_MESSAGE')}")
                        return None
                else:
                    logger.warning(f"HTTP 오류: {response.status_code}")

            except requests.exceptions.RequestException as e:
                logger.warning(f"요청 실패 (시도 {attempt + 1}): {e}")
                time.sleep(FETCH_CONFIG['retry_delay'])

        return None

    def get_minutes_list(
        self,
        start_count: int = 1,
        list_count: int = 100,
        search_type: str = "ALL",
        search_keyword: str = "",
        rasmbly_id: str = ""
    ) -> Optional[Dict]:
        """회의록 목록 조회

        Note: CLIK API는 searchKeyword가 비어있으면 오류를 반환함.
        전체 조회를 위해 기본값 '*' 또는 '회의' 사용.
        """
        # searchKeyword가 비어있으면 전체 검색을 위한 기본값 사용
        # '회의'는 가장 범용적인 키워드로 827,210건 반환 (전체 데이터)
        if not search_keyword:
            search_keyword = "회의"

        params = {
            'displayType': 'list',
            'startCount': start_count,
            'listCount': min(list_count, API_LIMITS['max_per_call']),
            'searchType': search_type,
            'searchKeyword': search_keyword,
        }

        if rasmbly_id:
            params['rasmblyId'] = rasmbly_id

        return self._make_request(ENDPOINTS['minutes'], params)

    def get_minutes_detail(self, docid: str) -> Optional[Dict]:
        """회의록 상세 조회 (전문 포함)"""
        params = {
            'displayType': 'detail',
            'docid': docid,
        }
        return self._make_request(ENDPOINTS['minutes'], params)

    def get_total_count(self) -> int:
        """전체 회의록 수 조회"""
        result = self.get_minutes_list(start_count=1, list_count=1)
        if result:
            return result.get('TOTAL_COUNT', 0)
        return 0

    def get_councils_from_minutes(self) -> List[Dict]:
        """회의록에서 의회 목록 추출"""
        councils = {}

        # 여러 페이지에서 의회 정보 수집
        for start in range(1, 10001, 100):
            result = self.get_minutes_list(start_count=start, list_count=100)
            if not result or not result.get('LIST'):
                break

            for item in result['LIST']:
                row = item.get('ROW', {})
                rasmbly_id = row.get('RASMBLY_ID')
                rasmbly_nm = row.get('RASMBLY_NM')

                if rasmbly_id and rasmbly_id not in councils:
                    councils[rasmbly_id] = {
                        'id': rasmbly_id,
                        'name': rasmbly_nm,
                        'first_seen': row.get('MTG_DE'),
                    }

            logger.info(f"의회 수집 중: {len(councils)}개 발견 (start={start})")

            # 충분히 수집되면 중단
            if len(councils) >= 250:
                break

        return list(councils.values())


def test_api():
    """API 테스트"""
    client = CLIKApiClient()

    print("=" * 60)
    print("CLIK API 테스트")
    print("=" * 60)

    # 1. 전체 건수 조회
    total = client.get_total_count()
    print(f"\n전체 회의록 수: {total:,}건")

    # 2. 목록 조회 테스트
    result = client.get_minutes_list(start_count=1, list_count=3)
    if result:
        print(f"\n목록 조회 성공: {result.get('LIST_COUNT')}건")
        for item in result.get('LIST', []):
            row = item.get('ROW', {})
            print(f"  - {row.get('RASMBLY_NM')} / {row.get('MTGNM')} ({row.get('MTG_DE')})")

    # 3. 상세 조회 테스트
    if result and result.get('LIST'):
        docid = result['LIST'][0]['ROW']['DOCID']
        detail = client.get_minutes_detail(docid)
        if detail:
            html_len = len(detail.get('MINTS_HTML', ''))
            print(f"\n상세 조회 성공: DOCID={docid}")
            print(f"  - 제목: {detail.get('MTR_SJ', '')[:50]}...")
            print(f"  - HTML 길이: {html_len:,}자")

    print(f"\n총 API 호출 횟수: {client.call_count}회")


if __name__ == "__main__":
    test_api()
