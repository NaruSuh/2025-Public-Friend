#!/usr/bin/env python3
"""
의회별 스마트 수집 스크립트

특징:
1. 의회별로 순회하며 수집 (rasmblyId 파라미터 활용)
2. 이미 충분히 수집된 의회는 스킵 (threshold 기준)
3. 의회별 진행상황 저장 → 중단 후 재시작 가능
4. 즉시 파일 저장 (버퍼링 없음)

vs fetch_all_minutes.py:
- fetch_all: 전체 82만건 순차 수집 (API 순서대로)
- 이 스크립트: 의회별 수집, 스킵 로직, 효율적 재시작
"""

import json
import time
import re
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Set, List, Optional
from html import unescape
import logging

from config import OUTPUT_DIR, DATA_DIR, LOG_DIR, FETCH_CONFIG
from api_client import CLIKApiClient

# 로깅 설정
log_file = LOG_DIR / f"collect_council_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CouncilCollector:
    """의회별 스마트 수집기"""

    def __init__(self, skip_threshold: int = 100):
        """
        Args:
            skip_threshold: 이 건수 이상 수집된 의회는 스킵
        """
        self.client = CLIKApiClient()
        self.skip_threshold = skip_threshold

        # 파일 경로
        self.council_progress_file = DATA_DIR / "council_progress.json"
        self.collected_docids_file = DATA_DIR / "collected_docids.txt"

        # 상태 로드
        self.council_progress = self._load_council_progress()
        self.collected_docids = self._load_collected_docids()

        # 통계
        self.stats = {
            'started_at': datetime.now().isoformat(),
            'councils_processed': 0,
            'councils_skipped': 0,
            'records_saved': 0,
            'errors': 0,
        }

    def _load_council_progress(self) -> Dict:
        """의회별 진행상황 로드"""
        if self.council_progress_file.exists():
            with open(self.council_progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'councils': {},  # {council_id: {'collected': n, 'total': m, 'last_updated': ...}}
            'last_council_id': None,
        }

    def _save_council_progress(self):
        """의회별 진행상황 저장"""
        with open(self.council_progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.council_progress, f, indent=2, ensure_ascii=False)

    def _load_collected_docids(self) -> Set[str]:
        """수집된 DOCID 목록 로드"""
        docids = set()
        if self.collected_docids_file.exists():
            with open(self.collected_docids_file, 'r') as f:
                docids = set(line.strip() for line in f if line.strip())
        logger.info(f"수집된 DOCID 로드: {len(docids):,}건")
        return docids

    def _save_docid(self, docid: str):
        """DOCID 즉시 저장 (append)"""
        self.collected_docids.add(docid)
        with open(self.collected_docids_file, 'a') as f:
            f.write(docid + '\n')

    def _html_to_text(self, html: str) -> str:
        """HTML을 텍스트로 변환"""
        if not html:
            return ""
        text = unescape(html)
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<hr\s*/?>', '\n---\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()

    def _save_minute(self, detail: Dict, council_id: str, council_name: str):
        """회의록 즉시 저장"""
        output_file = OUTPUT_DIR / f"{council_id}.jsonl"

        html_content = detail.get('MINTS_HTML', '')
        text_content = self._html_to_text(html_content)

        record = {
            "docid": detail.get('DOCID'),
            "council_id": council_id,
            "council_name": council_name,
            "session": detail.get('RASMBLY_SESN'),
            "meeting_date": detail.get('MTG_DE'),
            "meeting_order": detail.get('MINTS_ODR'),
            "meeting_type": detail.get('MTGNM', ''),
            "title": detail.get('MTR_SJ', ''),
            "full_content": text_content,
            "html_content": html_content,
            "fetched_at": datetime.now().isoformat(),
            "source": "clik_api"
        }

        # 즉시 저장 (append 모드)
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

        return True

    def _get_local_count(self, council_id: str) -> int:
        """로컬에 저장된 의회별 레코드 수"""
        output_file = OUTPUT_DIR / f"{council_id}.jsonl"
        if not output_file.exists():
            return 0
        with open(output_file, 'r') as f:
            return sum(1 for _ in f)

    def discover_councils(self, sample_size: int = 50000) -> List[Dict]:
        """API에서 의회 목록 발견"""
        logger.info("의회 목록 수집 중...")
        councils = {}

        # 여러 위치에서 샘플링
        step = max(1, sample_size // 100)
        for start in range(1, sample_size + 1, step):
            result = self.client.get_minutes_list(start_count=start, list_count=100)
            if not result or not result.get('LIST'):
                continue

            for item in result.get('LIST', []):
                row = item.get('ROW', {})
                rid = row.get('RASMBLY_ID')
                rnm = row.get('RASMBLY_NM')
                if rid and rid not in councils:
                    councils[rid] = {'id': rid, 'name': rnm}

            if len(councils) >= 250:  # 모든 의회 발견
                break

        council_list = sorted(councils.values(), key=lambda x: x['id'])
        logger.info(f"총 {len(council_list)}개 의회 발견")
        return council_list

    def collect_council(self, council_id: str, council_name: str, limit: Optional[int] = None) -> int:
        """특정 의회의 회의록 수집

        Args:
            council_id: 의회 ID (예: "002001")
            council_name: 의회명
            limit: 수집 건수 제한 (None이면 전체)

        Returns:
            수집된 건수
        """
        local_count = self._get_local_count(council_id)

        # API에서 전체 건수 확인
        result = self.client.get_minutes_list(
            start_count=1, list_count=1, rasmbly_id=council_id
        )
        if not result:
            logger.warning(f"{council_id} ({council_name}): API 조회 실패")
            return 0

        total_count = result.get('TOTAL_COUNT', 0)

        # 스킵 조건 확인
        if local_count >= self.skip_threshold:
            logger.info(f"⏭️ {council_id} ({council_name}): {local_count}건 이미 수집, 스킵")
            self.stats['councils_skipped'] += 1
            return 0

        # 목표 건수 계산
        target = total_count
        if limit:
            target = min(limit, total_count - local_count)

        logger.info(f"📥 {council_id} ({council_name}): API {total_count}건, 로컬 {local_count}건, 목표 {target}건")

        saved = 0
        start = 1
        batch_size = FETCH_CONFIG['batch_size']

        while start <= total_count:
            result = self.client.get_minutes_list(
                start_count=start,
                list_count=batch_size,
                rasmbly_id=council_id
            )

            if not result or not result.get('LIST'):
                start += batch_size
                continue

            for item in result.get('LIST', []):
                row = item.get('ROW', {})
                docid = row.get('DOCID')

                if not docid or docid in self.collected_docids:
                    continue

                # 상세 조회
                detail = self.client.get_minutes_detail(docid)
                if detail:
                    try:
                        # 안전한 저장 순서: DOCID 먼저 → 레코드 저장
                        # 크래시 시나리오:
                        # - DOCID만 저장됨 → 재시작 시 스킵 (누락 1건, 중복 0건)
                        # - 둘 다 저장됨 → 정상
                        # 반대 순서면: 레코드는 있는데 DOCID 없음 → 중복 저장 위험
                        self._save_docid(docid)
                        self._save_minute(detail, council_id, council_name)
                        saved += 1
                        self.stats['records_saved'] += 1

                        if saved % 50 == 0:
                            logger.info(f"  {council_id}: {saved}건 저장")

                        if limit and saved >= limit:
                            break
                    except Exception as e:
                        logger.error(f"저장 실패 ({docid}): {e}")
                        self.stats['errors'] += 1

            start += batch_size

            if limit and saved >= limit:
                break

        # 진행상황 저장
        self.council_progress['councils'][council_id] = {
            'name': council_name,
            'collected': local_count + saved,
            'total': total_count,
            'last_updated': datetime.now().isoformat()
        }
        self.council_progress['last_council_id'] = council_id
        self._save_council_progress()

        logger.info(f"✅ {council_id} ({council_name}): {saved}건 수집 완료")
        self.stats['councils_processed'] += 1

        return saved

    def collect_all(
        self,
        councils: Optional[List[Dict]] = None,
        limit_per_council: Optional[int] = None,
        resume: bool = True
    ):
        """전체 의회 순회 수집

        Args:
            councils: 의회 목록 (None이면 자동 발견)
            limit_per_council: 의회당 수집 제한
            resume: True면 마지막 의회부터 재개
        """
        if councils is None:
            councils = self.discover_councils()

        # 재개 위치 찾기
        start_idx = 0
        if resume and self.council_progress.get('last_council_id'):
            last_id = self.council_progress['last_council_id']
            for i, c in enumerate(councils):
                if c['id'] == last_id:
                    start_idx = i + 1
                    logger.info(f"이전 진행 위치에서 재개: {last_id} 다음부터")
                    break

        logger.info("=" * 60)
        logger.info(f"의회별 수집 시작: {len(councils)}개 의회, 스킵 기준 {self.skip_threshold}건")
        logger.info("=" * 60)

        try:
            for i, council in enumerate(councils[start_idx:], start=start_idx + 1):
                cid = council['id']
                cname = council['name']

                logger.info(f"\n[{i}/{len(councils)}] {cid} - {cname}")
                self.collect_council(cid, cname, limit=limit_per_council)

        except KeyboardInterrupt:
            logger.info("\n중단됨 (Ctrl+C)")
        finally:
            self._print_stats()

    def _print_stats(self):
        """통계 출력"""
        self.stats['ended_at'] = datetime.now().isoformat()

        logger.info("\n" + "=" * 60)
        logger.info("수집 완료")
        logger.info("=" * 60)
        logger.info(f"처리된 의회: {self.stats['councils_processed']}개")
        logger.info(f"스킵된 의회: {self.stats['councils_skipped']}개")
        logger.info(f"저장된 레코드: {self.stats['records_saved']:,}건")
        logger.info(f"오류: {self.stats['errors']}건")

        # 통계 파일 저장
        stats_file = LOG_DIR / f"collect_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description='의회별 스마트 수집')
    parser.add_argument('--threshold', type=int, default=100,
                        help='스킵 기준 건수 (기본: 100)')
    parser.add_argument('--limit', type=int, default=None,
                        help='의회당 수집 제한')
    parser.add_argument('--council', type=str, default=None,
                        help='특정 의회만 수집 (예: 002001)')
    parser.add_argument('--no-resume', action='store_true',
                        help='처음부터 시작')
    parser.add_argument('--discover', action='store_true',
                        help='의회 목록만 출력')

    args = parser.parse_args()

    collector = CouncilCollector(skip_threshold=args.threshold)

    if args.discover:
        councils = collector.discover_councils()
        for c in councils:
            print(f"{c['id']}: {c['name']}")
        return

    if args.council:
        # 특정 의회만
        result = collector.client.get_minutes_list(
            start_count=1, list_count=1, rasmbly_id=args.council
        )
        if result and result.get('LIST'):
            name = result['LIST'][0]['ROW']['RASMBLY_NM']
            collector.collect_council(args.council, name, limit=args.limit)
        else:
            logger.error(f"의회를 찾을 수 없음: {args.council}")
    else:
        # 전체 의회
        collector.collect_all(
            limit_per_council=args.limit,
            resume=not args.no_resume
        )


if __name__ == "__main__":
    main()
