#!/usr/bin/env python3
"""
전국 243개 지방의회 일괄 크롤링 스크립트
==========================================
- 17개 광역의회 + 226개 기초의회 순차 크롤링
- 진행 상황 로깅 및 결과 요약 리포트 생성
- 실패한 의회 재시도 지원

Usage:
    python batch_crawl.py --max-pages 3
    python batch_crawl.py --max-pages 5 --type metropolitan
    python batch_crawl.py --max-pages 2 --type basic
    python batch_crawl.py --resume  # 실패한 의회만 재시도
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# 크롤러 모듈 임포트
from council_crawler import get_all_councils, get_crawler, ResultSaver

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('batch_crawl.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class BatchCrawler:
    """전체 의회 일괄 크롤링 관리자"""

    def __init__(self, output_dir: str = "output", max_pages: int = 3):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_pages = max_pages
        self.results: Dict[str, Dict[str, Any]] = {}
        self.start_time = None

        # 상태 파일
        self.status_file = self.output_dir / "crawl_status.json"

    def load_status(self) -> Dict[str, Any]:
        """이전 크롤링 상태 로드"""
        if self.status_file.exists():
            with open(self.status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"completed": [], "failed": [], "results": {}}

    def save_status(self):
        """크롤링 상태 저장"""
        status = {
            "last_updated": datetime.now().isoformat(),
            "completed": [code for code, r in self.results.items() if r.get("success")],
            "failed": [code for code, r in self.results.items() if not r.get("success")],
            "results": self.results
        }
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(status, ensure_ascii=False, indent=2, fp=f)

    def crawl_council(self, council_code: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """단일 의회 크롤링"""
        result = {
            "code": council_code,
            "name": config.get("name", ""),
            "type": config.get("type", ""),
            "success": False,
            "count": 0,
            "error": None,
            "duration": 0,
            "output_file": None
        }

        start = time.time()

        try:
            crawler = get_crawler(council_code)
            if not crawler:
                result["error"] = "크롤러 생성 실패"
                return result

            # 크롤링 실행
            items = list(crawler.crawl(max_pages=self.max_pages))
            result["count"] = len(items)

            if items:
                # 결과 저장 (JSONL + Markdown 이중 출력)
                saver = ResultSaver(str(self.output_dir))
                output_file = saver.save_jsonl(council_code, items)
                md_file = saver.save_markdown(council_code, items)
                result["output_file"] = str(output_file)
                result["md_file"] = str(md_file)
                result["success"] = True
            else:
                result["success"] = False  # 0건이면 실패로 처리
                result["error"] = "수집된 데이터 없음 (URL 확인 필요)"

            crawler.close()

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"[{council_code}] 크롤링 오류: {e}")

        result["duration"] = round(time.time() - start, 2)
        return result

    def run(self, council_type: str = None, resume: bool = False):
        """전체 크롤링 실행"""
        self.start_time = datetime.now()
        all_councils = get_all_councils()

        # 이전 상태 로드
        prev_status = self.load_status()
        completed = set(prev_status.get("completed", []))

        # 크롤링 대상 필터링
        if council_type == "metropolitan":
            targets = {k: v for k, v in all_councils.items() if v.get("type") == "metropolitan"}
        elif council_type == "basic":
            targets = {k: v for k, v in all_councils.items() if v.get("type") == "basic"}
        else:
            targets = all_councils

        # resume 모드: 실패한 것만 재시도
        if resume:
            failed = set(prev_status.get("failed", []))
            targets = {k: v for k, v in targets.items() if k in failed}
            logger.info(f"재시도 모드: {len(targets)}개 의회")

        total = len(targets)
        success_count = 0
        fail_count = 0
        total_items = 0

        logger.info("=" * 60)
        logger.info(f"전국 지방의회 일괄 크롤링 시작")
        logger.info(f"대상: {total}개 의회 | 페이지 수: {self.max_pages}")
        logger.info("=" * 60)

        for idx, (code, config) in enumerate(targets.items(), 1):
            council_name = config.get("name", code)
            council_type_str = "광역" if config.get("type") == "metropolitan" else "기초"

            logger.info(f"\n[{idx}/{total}] {council_name} ({council_type_str}) 크롤링 시작...")

            result = self.crawl_council(code, config)
            self.results[code] = result

            if result["success"]:
                success_count += 1
                total_items += result["count"]
                logger.info(f"  ✓ 완료: {result['count']}건 수집 ({result['duration']}초)")
            else:
                fail_count += 1
                logger.warning(f"  ✗ 실패: {result['error']}")

            # 상태 저장 (10개마다)
            if idx % 10 == 0:
                self.save_status()
                logger.info(f"  [진행률: {idx}/{total} ({idx*100//total}%)]")

            # 의회 간 딜레이
            time.sleep(1)

        # 최종 상태 저장
        self.save_status()

        # 결과 리포트 생성
        self.generate_report(total, success_count, fail_count, total_items)

    def generate_report(self, total: int, success: int, fail: int, items: int):
        """크롤링 결과 리포트 생성"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        report = f"""
================================================================================
                     전국 지방의회 크롤링 결과 보고서
================================================================================

■ 실행 정보
  - 시작 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
  - 종료 시간: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
  - 소요 시간: {duration:.1f}초 ({duration/60:.1f}분)
  - 페이지 수: {self.max_pages}

■ 크롤링 결과
  - 대상 의회: {total}개
  - 성공: {success}개 ({success*100//total if total else 0}%)
  - 실패: {fail}개 ({fail*100//total if total else 0}%)
  - 수집 회의록: {items}건

■ 광역의회 결과
"""
        # 광역의회
        metro_results = [(k, v) for k, v in self.results.items() if v.get("type") == "metropolitan"]
        for code, r in sorted(metro_results, key=lambda x: x[1].get("name", "")):
            status = "✓" if r["success"] else "✗"
            report += f"  {status} {r['name']}: {r['count']}건\n"

        report += "\n■ 기초의회 결과 (지역별)\n"

        # 기초의회 (지역별 그룹화)
        basic_results = [(k, v) for k, v in self.results.items() if v.get("type") == "basic"]

        # 지역별 집계
        region_stats = {}
        for code, r in basic_results:
            # admin_code에서 지역코드 추출
            admin_code = r.get("admin_code", "00")[:2] if "admin_code" in r else "00"
            if admin_code not in region_stats:
                region_stats[admin_code] = {"success": 0, "fail": 0, "items": 0}
            if r["success"]:
                region_stats[admin_code]["success"] += 1
                region_stats[admin_code]["items"] += r["count"]
            else:
                region_stats[admin_code]["fail"] += 1

        region_names = {
            '11': '서울', '26': '부산', '27': '대구', '28': '인천',
            '29': '광주', '30': '대전', '31': '울산', '41': '경기',
            '51': '강원', '43': '충북', '44': '충남', '52': '전북',
            '46': '전남', '47': '경북', '48': '경남'
        }

        for region_code in sorted(region_stats.keys()):
            stats = region_stats[region_code]
            name = region_names.get(region_code, region_code)
            total_r = stats["success"] + stats["fail"]
            report += f"  [{name}] {stats['success']}/{total_r}개 성공, {stats['items']}건\n"

        # 실패 목록
        failed = [r for r in self.results.values() if not r["success"]]
        if failed:
            report += "\n■ 실패 의회 목록\n"
            for r in failed:
                report += f"  - {r['name']}: {r['error']}\n"

        report += "\n" + "=" * 80

        # 리포트 저장
        report_file = self.output_dir / f"crawl_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(report)
        logger.info(f"리포트 저장: {report_file}")


def main():
    parser = argparse.ArgumentParser(
        description="전국 243개 지방의회 일괄 크롤링",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--max-pages", "-m", type=int, default=3,
                        help="의회당 최대 크롤링 페이지 수 (기본: 3)")
    parser.add_argument("--type", "-t", choices=["metropolitan", "basic"],
                        help="크롤링 대상 (metropolitan: 광역, basic: 기초)")
    parser.add_argument("--output", "-o", type=str, default="output",
                        help="출력 디렉토리 (기본: output)")
    parser.add_argument("--resume", "-r", action="store_true",
                        help="실패한 의회만 재시도")

    args = parser.parse_args()

    crawler = BatchCrawler(output_dir=args.output, max_pages=args.max_pages)

    try:
        crawler.run(council_type=args.type, resume=args.resume)
    except KeyboardInterrupt:
        logger.info("\n사용자 중단. 현재까지 결과 저장 중...")
        crawler.save_status()
        logger.info("상태 저장 완료. --resume 옵션으로 재시도 가능.")
        return 130

    return 0


if __name__ == "__main__":
    sys.exit(main())
