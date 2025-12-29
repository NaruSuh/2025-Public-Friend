#!/usr/bin/env python3
"""
학회 참석자 만족도 조사 보고서 자동 생성 스크립트

사용법:
    python generate_report.py --data data/survey.csv --config config.json
    python generate_report.py --data data/survey.xlsx --output output/report.md
"""

import argparse
import json
import sys
from pathlib import Path

# 현재 디렉토리를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from report_generator import SurveyReportGenerator


def load_config(config_path: str) -> dict:
    """설정 파일 로드"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description='학회 참석자 만족도 조사 보고서 자동 생성',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 기본 사용
  python generate_report.py --data data/survey.csv

  # 설정 파일 사용
  python generate_report.py --data data/survey.csv --config config.json

  # HTML 형식으로 출력
  python generate_report.py --data data/survey.csv --format html

  # 워드 형식으로 출력
  python generate_report.py --data data/survey.csv --format docx

  # 출력 경로 지정
  python generate_report.py --data data/survey.csv --output output/my_report.md
        """
    )

    parser.add_argument(
        '--data',
        required=True,
        help='설문조사 데이터 파일 (CSV, Excel 등)'
    )

    parser.add_argument(
        '--config',
        default=None,
        help='보고서 설정 파일 (JSON)'
    )

    parser.add_argument(
        '--format',
        choices=['markdown', 'html', 'docx'],
        default='markdown',
        help='출력 형식 (기본값: markdown)'
    )

    parser.add_argument(
        '--output',
        default=None,
        help='출력 파일 경로 (지정하지 않으면 자동 생성)'
    )

    args = parser.parse_args()

    # 데이터 파일 확인
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"오류: 데이터 파일을 찾을 수 없습니다: {args.data}")
        sys.exit(1)

    # 설정 로드
    config = {}
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"오류: 설정 파일을 찾을 수 없습니다: {args.config}")
            sys.exit(1)
        config = load_config(args.config)

    # 출력 파일 경로 결정
    if args.output:
        output_path = Path(args.output)
    else:
        # 자동 생성
        ext_map = {'markdown': 'md', 'html': 'html', 'docx': 'docx'}
        ext = ext_map.get(args.format, 'md')
        output_dir = Path(__file__).parent / 'output'
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f'survey_report_{Path(args.data).stem}.{ext}'

    print("=" * 60)
    print("학회 참석자 만족도 조사 보고서 생성 시작")
    print("=" * 60)
    print(f"데이터 파일: {args.data}")
    print(f"출력 형식: {args.format}")
    print(f"출력 파일: {output_path}")
    print("=" * 60)

    try:
        # 보고서 생성기 초기화
        generator = SurveyReportGenerator(str(data_path), config)

        # 보고서 생성 및 저장
        print("\n[1/3] 데이터 로드 및 통계 분석 중...")
        print("[2/3] LLM 기반 텍스트 생성 중...")
        print("[3/3] 보고서 작성 중...")

        generator.save_report(str(output_path), args.format)

        print("\n" + "=" * 60)
        print("보고서 생성 완료!")
        print("=" * 60)
        print(f"보고서 위치: {output_path.absolute()}")
        print("=" * 60)

    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
