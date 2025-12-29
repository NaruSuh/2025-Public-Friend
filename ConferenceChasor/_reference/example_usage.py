#!/usr/bin/env python3
"""
보고서 생성기 사용 예시
Python 코드로 직접 제어하는 방법을 보여줍니다
"""

import sys
from pathlib import Path

# src 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from data_processor import SurveyDataProcessor, quick_analysis
from llm_generator import ReportTextGenerator
from report_generator import SurveyReportGenerator


def example1_quick_analysis():
    """예시 1: 빠른 통계 분석"""
    print("=" * 60)
    print("예시 1: 빠른 통계 분석")
    print("=" * 60)

    result = quick_analysis(
        'data/sample_survey.csv',
        score_columns=['overall_satisfaction', 'content_quality']
    )

    print(f"응답자 수: {result['basic_stats']['total_responses']}명")
    print(f"만족도 지수: {result['satisfaction_index']}/100")
    print()


def example2_detailed_processing():
    """예시 2: 상세 데이터 처리"""
    print("=" * 60)
    print("예시 2: 상세 데이터 처리")
    print("=" * 60)

    processor = SurveyDataProcessor('data/sample_survey.csv')
    processor.load_data()

    # 특정 컬럼 분석
    stats = processor.analyze_numeric_column('overall_satisfaction')
    print(f"전체 만족도 평균: {stats['mean']:.2f}/5.0")
    print(f"응답 수: {stats['count']}명")

    # 주관식 응답 가져오기
    feedback = processor.get_text_responses('positive_feedback')
    print(f"긍정 피드백 수: {len(feedback)}개")
    print(f"샘플: {feedback[0]}")
    print()


def example3_llm_text_generation():
    """예시 3: LLM 텍스트 생성 (API 키 필요)"""
    print("=" * 60)
    print("예시 3: LLM 텍스트 생성")
    print("=" * 60)

    try:
        generator = ReportTextGenerator()

        # 샘플 통계로 요약 생성
        sample_stats = {
            'total_responses': 20,
            'satisfaction_index': 85.5,
        }

        summary = generator.generate_executive_summary(sample_stats, "AI 학회")
        print("생성된 경영진 요약:")
        print(summary)
        print()

    except ValueError as e:
        print(f"LLM 생성 스킵: {e}")
        print("ANTHROPIC_API_KEY 환경변수를 설정하면 사용 가능합니다.")
        print()


def example4_full_report():
    """예시 4: 전체 보고서 생성"""
    print("=" * 60)
    print("예시 4: 전체 보고서 생성")
    print("=" * 60)

    config = {
        'conference_name': '2024 AI 테스트 학회',
        'survey_date': '2024년 11월',
        'score_columns': ['overall_satisfaction', 'content_quality'],
        'column_labels': {
            'overall_satisfaction': '전체 만족도',
            'content_quality': '내용 품질'
        },
        'text_columns': {
            'positive_feedback': '좋았던 점'
        }
    }

    try:
        generator = SurveyReportGenerator('data/sample_survey.csv', config)

        # 보고서 생성 및 저장
        output_path = 'output/example_report.md'
        generator.save_report(output_path, output_format='markdown')

        print(f"보고서가 생성되었습니다: {output_path}")

    except Exception as e:
        print(f"보고서 생성 중 오류: {e}")
        print("API 키가 설정되어 있는지 확인하세요.")

    print()


def main():
    """모든 예시 실행"""
    print("\n")
    print("#" * 60)
    print("# 학회 만족도 조사 보고서 생성기 - 사용 예시")
    print("#" * 60)
    print("\n")

    # 예시 1, 2는 API 키 없이 실행 가능
    example1_quick_analysis()
    example2_detailed_processing()

    # 예시 3, 4는 API 키 필요
    example3_llm_text_generation()
    example4_full_report()

    print("=" * 60)
    print("모든 예시 완료!")
    print("=" * 60)


if __name__ == '__main__':
    main()
