#!/usr/bin/env python3
"""
16개 광역의회 회의록 일괄 수집 스크립트
제주도 제외, 지난 1개월간 회의록을 .md 파일로 저장
"""

import sys
import time
from datetime import datetime
from pathlib import Path

# 현재 디렉토리의 council_crawler 모듈 import
from council_crawler import get_crawler, ResultSaver, logger

# 16개 광역의회 코드 (제주 제외)
METRO_COUNCILS = [
    'seoul',     # 서울특별시의회
    'busan',     # 부산광역시의회
    'daegu',     # 대구광역시의회
    'incheon',   # 인천광역시의회
    'gwangju',   # 광주광역시의회
    'daejeon',   # 대전광역시의회
    'ulsan',     # 울산광역시의회
    'sejong',    # 세종특별자치시의회
    'gyeonggi',  # 경기도의회
    'chungbuk',  # 충청북도의회
    'chungnam',  # 충청남도의회
    'jeonnam',   # 전라남도의회
    'gyeongbuk', # 경상북도의회
    'gyeongnam', # 경상남도의회
    'gangwon',   # 강원특별자치도의회
    'jeonbuk',   # 전북특별자치도의회
]

def crawl_all_metro(max_pages: int = 5, output_dir: str = "output/metro_minutes"):
    """16개 광역의회 일괄 크롤링"""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    saver = ResultSaver(output_dir)

    results_summary = []
    failed_councils = []

    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("16개 광역의회 회의록 일괄 수집 시작")
    logger.info(f"시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"페이지 수: {max_pages} (약 1개월 분량)")
    logger.info("=" * 60)

    for idx, council_code in enumerate(METRO_COUNCILS, 1):
        logger.info(f"\n[{idx}/{len(METRO_COUNCILS)}] {council_code} 크롤링 시작...")

        crawler = get_crawler(council_code)
        if not crawler:
            logger.error(f"{council_code}: 크롤러 생성 실패")
            failed_councils.append(council_code)
            continue

        try:
            results = list(crawler.crawl(max_pages=max_pages))

            if results:
                # JSONL 저장
                jsonl_file = saver.save_jsonl(council_code, results)
                # Markdown 저장
                md_file = saver.save_markdown(council_code, results)

                council_name = results[0].council_name
                results_summary.append({
                    'code': council_code,
                    'name': council_name,
                    'count': len(results),
                    'md_file': str(md_file),
                })
                logger.info(f"✓ {council_name}: {len(results)}건 저장 완료")
            else:
                logger.warning(f"✗ {council_code}: 수집된 데이터 없음")
                failed_councils.append(council_code)

        except Exception as e:
            logger.error(f"✗ {council_code} 크롤링 오류: {e}")
            failed_councils.append(council_code)
        finally:
            crawler.close()

        # 의회 간 딜레이 (서버 부하 방지)
        if idx < len(METRO_COUNCILS):
            time.sleep(3)

    end_time = datetime.now()
    duration = end_time - start_time

    # 결과 리포트 출력
    logger.info("\n" + "=" * 60)
    logger.info("수집 완료 리포트")
    logger.info("=" * 60)
    logger.info(f"수집 시간: {duration}")
    logger.info(f"성공: {len(results_summary)}개 의회")
    logger.info(f"실패: {len(failed_councils)}개 의회")

    if results_summary:
        logger.info("\n[ 수집 현황 ]")
        total_items = 0
        for r in results_summary:
            logger.info(f"  {r['name']}: {r['count']}건")
            total_items += r['count']
        logger.info(f"\n총 수집 건수: {total_items}건")

    if failed_councils:
        logger.info(f"\n[ 실패 의회 ]\n  {', '.join(failed_councils)}")

    # 요약 리포트 파일 저장
    report_file = output_path / f"crawl_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("16개 광역의회 회의록 수집 리포트\n")
        f.write("=" * 50 + "\n")
        f.write(f"수집일시: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"소요시간: {duration}\n")
        f.write(f"성공: {len(results_summary)}개, 실패: {len(failed_councils)}개\n\n")

        for r in results_summary:
            f.write(f"{r['name']}: {r['count']}건 -> {r['md_file']}\n")

        if failed_councils:
            f.write(f"\n실패 의회: {', '.join(failed_councils)}\n")

    logger.info(f"\n리포트 저장: {report_file}")
    logger.info("=" * 60)

    return results_summary, failed_councils


if __name__ == "__main__":
    # 기본 5페이지 (약 50-100건, 1개월 분량)
    max_pages = 5
    if len(sys.argv) > 1:
        try:
            max_pages = int(sys.argv[1])
        except ValueError:
            pass

    crawl_all_metro(max_pages=max_pages)
