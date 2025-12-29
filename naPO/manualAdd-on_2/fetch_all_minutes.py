#!/usr/bin/env python3
"""
CLIK API 전체 회의록 수집 스크립트
- 492,885건 전체 수집
- 중단 후 재시작 지원
- 진행 상황 자동 저장
"""

import json
import time
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Set
from html import unescape
import logging

from config import (
    OUTPUT_DIR, DATA_DIR, LOG_DIR, FETCH_CONFIG, API_LIMITS
)
from api_client import CLIKApiClient

# 로깅 설정
log_file = LOG_DIR / f"fetch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MinutesFetcher:
    """회의록 전체 수집기"""

    def __init__(self):
        self.client = CLIKApiClient()
        self.progress_file = DATA_DIR / "progress.json"
        self.collected_docids_file = DATA_DIR / "collected_docids.txt"
        self.collected_docids: Set[str] = set()
        self.progress = self._load_progress()
        self._load_collected_docids()

        # 통계
        self.stats = {
            'started_at': datetime.now().isoformat(),
            'total_fetched': 0,
            'total_saved': 0,
            'errors': 0,
            'api_calls': 0,
        }

    def _load_progress(self) -> Dict:
        """진행 상황 로드"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                progress = json.load(f)
                logger.info(f"진행 상황 복원: start_count={progress.get('last_start_count', 1)}")
                return progress
        return {
            'last_start_count': 1,
            'total_count': 0,
            'fetched_count': 0,
            'last_updated': None,
        }

    def _save_progress(self):
        """진행 상황 저장"""
        self.progress['last_updated'] = datetime.now().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2, ensure_ascii=False)

    def _load_collected_docids(self):
        """수집된 DOCID 목록 로드"""
        if self.collected_docids_file.exists():
            with open(self.collected_docids_file, 'r') as f:
                self.collected_docids = set(line.strip() for line in f if line.strip())
            logger.info(f"수집된 DOCID 로드: {len(self.collected_docids):,}건")

    def _save_collected_docid(self, docid: str):
        """수집된 DOCID 추가 저장"""
        self.collected_docids.add(docid)
        with open(self.collected_docids_file, 'a') as f:
            f.write(docid + '\n')

    def _html_to_text(self, html: str) -> str:
        """HTML을 텍스트로 변환"""
        if not html:
            return ""

        # HTML 엔티티 디코딩
        text = unescape(html)

        # 주요 태그를 줄바꿈으로 변환
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</li>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<hr\s*/?>', '\n---\n', text, flags=re.IGNORECASE)

        # 모든 HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)

        # 연속 공백/줄바꿈 정리
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)

        return text.strip()

    def _get_council_code(self, rasmbly_id: str, rasmbly_nm: str) -> str:
        """RASMBLY_ID를 council_code로 변환"""
        # 의회명에서 코드 추출 시도
        name = rasmbly_nm.replace('의회', '').strip()

        # 시/군/구 제거
        for suffix in ['시', '군', '구']:
            if name.endswith(suffix):
                name = name[:-1]
                break

        # 도/광역시 접두사 제거
        prefixes = ['서울특별시', '부산광역시', '대구광역시', '인천광역시', '광주광역시',
                   '대전광역시', '울산광역시', '세종특별자치시', '경기도', '강원도',
                   '충청북도', '충청남도', '전라북도', '전라남도', '경상북도', '경상남도', '제주특별자치도']
        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[len(prefix):].strip()
                break

        # 영문 코드 생성 (간단한 매핑)
        return rasmbly_id  # 일단 RASMBLY_ID 그대로 사용

    def _save_minute(self, detail: Dict, rasmbly_id: str, rasmbly_nm: str):
        """회의록 저장"""
        # 의회별 파일에 저장
        output_file = OUTPUT_DIR / f"{rasmbly_id}.jsonl"

        # 텍스트 추출
        html_content = detail.get('MINTS_HTML', '')
        text_content = self._html_to_text(html_content)

        record = {
            "docid": detail.get('DOCID'),
            "council_id": rasmbly_id,
            "council_name": rasmbly_nm,
            "session": detail.get('RASMBLY_SESN'),        # 회기
            "meeting_date": detail.get('MTG_DE'),          # 회의일자
            "meeting_order": detail.get('MINTS_ODR'),      # 차수
            "meeting_type": detail.get('MTGNM', ''),       # 회의유형 (본회의/위원회)
            "title": detail.get('MTR_SJ', ''),             # 안건 제목
            "full_content": text_content,                   # 전문 (텍스트)
            "html_content": html_content,                   # 전문 (HTML 원본)
            "fetched_at": datetime.now().isoformat(),
            "source": "clik_api"
        }

        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

        return True

    def fetch_all(self, start_from: Optional[int] = None, limit: Optional[int] = None):
        """전체 회의록 수집"""
        logger.info("=" * 60)
        logger.info("CLIK API 전체 회의록 수집 시작")
        logger.info("=" * 60)

        # 전체 건수 확인
        total_count = self.client.get_total_count()
        self.progress['total_count'] = total_count
        logger.info(f"전체 회의록 수: {total_count:,}건")

        # 시작 위치 결정
        start_count = start_from or self.progress.get('last_start_count', 1)
        logger.info(f"시작 위치: {start_count}")

        batch_size = FETCH_CONFIG['batch_size']
        fetched = 0
        saved = 0
        errors = 0

        try:
            while start_count <= total_count:
                # 목록 조회
                result = self.client.get_minutes_list(
                    start_count=start_count,
                    list_count=batch_size
                )

                if not result or not result.get('LIST'):
                    logger.warning(f"목록 조회 실패: start_count={start_count}")
                    errors += 1
                    start_count += batch_size
                    continue

                # 각 회의록 상세 조회
                for item in result.get('LIST', []):
                    row = item.get('ROW', {})
                    docid = row.get('DOCID')
                    rasmbly_id = row.get('RASMBLY_ID')
                    rasmbly_nm = row.get('RASMBLY_NM')

                    if not docid:
                        continue

                    # 이미 수집된 경우 스킵
                    if docid in self.collected_docids:
                        continue

                    # 상세 조회
                    detail = self.client.get_minutes_detail(docid)
                    fetched += 1

                    if detail:
                        try:
                            self._save_minute(detail, rasmbly_id, rasmbly_nm)
                            self._save_collected_docid(docid)
                            saved += 1
                        except Exception as e:
                            logger.error(f"저장 실패 ({docid}): {e}")
                            errors += 1
                    else:
                        errors += 1

                    # 진행 상황 출력
                    if saved % 100 == 0:
                        pct = (start_count + fetched) / total_count * 100
                        logger.info(
                            f"진행: {start_count + fetched:,}/{total_count:,} ({pct:.1f}%) | "
                            f"저장: {saved:,} | 오류: {errors}"
                        )

                    # 제한 확인
                    if limit and saved >= limit:
                        logger.info(f"제한 도달: {limit}건")
                        break

                # 진행 상황 저장
                self.progress['last_start_count'] = start_count + batch_size
                self.progress['fetched_count'] = self.progress.get('fetched_count', 0) + len(result.get('LIST', []))
                self._save_progress()

                start_count += batch_size

                if limit and saved >= limit:
                    break

        except KeyboardInterrupt:
            logger.info("\n중단됨 (Ctrl+C)")
        finally:
            # 최종 통계
            self.stats['total_fetched'] = fetched
            self.stats['total_saved'] = saved
            self.stats['errors'] = errors
            self.stats['api_calls'] = self.client.call_count
            self.stats['ended_at'] = datetime.now().isoformat()

            logger.info("\n" + "=" * 60)
            logger.info("수집 완료")
            logger.info("=" * 60)
            logger.info(f"총 조회: {fetched:,}건")
            logger.info(f"총 저장: {saved:,}건")
            logger.info(f"오류: {errors}건")
            logger.info(f"API 호출: {self.client.call_count:,}회")
            logger.info(f"진행 상황 저장됨: {self.progress_file}")

            # 통계 저장
            stats_file = LOG_DIR / f"stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)

        return saved


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='CLIK API 전체 회의록 수집')
    parser.add_argument('--start', type=int, help='시작 위치 (기본: 마지막 진행 위치)')
    parser.add_argument('--limit', type=int, help='수집 건수 제한')
    parser.add_argument('--reset', action='store_true', help='진행 상황 초기화')

    args = parser.parse_args()

    fetcher = MinutesFetcher()

    if args.reset:
        if fetcher.progress_file.exists():
            fetcher.progress_file.unlink()
            logger.info("진행 상황 초기화됨")
        fetcher.progress = {'last_start_count': 1}

    fetcher.fetch_all(start_from=args.start, limit=args.limit)


if __name__ == "__main__":
    main()
