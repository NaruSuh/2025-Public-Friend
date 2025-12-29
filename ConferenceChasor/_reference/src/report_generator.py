"""
보고서 생성기 - 통계 분석과 LLM 텍스트를 결합하여 최종 보고서 생성
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

from data_processor import SurveyDataProcessor
from llm_generator import ReportTextGenerator
from docx_processor import DocxReportWriter


class SurveyReportGenerator:
    """설문조사 보고서 통합 생성기"""

    def __init__(self, data_path: str, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            data_path: 설문조사 데이터 파일 경로
            config: 보고서 설정 (학회명, 날짜, 항목 매핑 등)
        """
        self.data_processor = SurveyDataProcessor(data_path)
        self.text_generator = ReportTextGenerator()
        self.config = config or {}

        # 기본 설정
        self.conference_name = self.config.get('conference_name', '학회')
        self.survey_date = self.config.get('survey_date', datetime.now().strftime('%Y년 %m월'))
        self.respondents = self.config.get('estimated_attendees', '수백명')

    def generate_full_report(self, output_format: str = 'markdown') -> str:
        """전체 보고서 생성"""

        # 1. 데이터 로드
        self.data_processor.load_data()

        # 2. 설정에서 항목 매핑 가져오기
        score_columns = self.config.get('score_columns', [])
        text_columns = self.config.get('text_columns', {})

        # 3. 통계 분석
        basic_stats = self.data_processor.get_basic_stats()
        satisfaction_analysis = {}
        satisfaction_index = 0

        if score_columns:
            satisfaction_analysis = self.data_processor.analyze_satisfaction_scores(score_columns)
            satisfaction_index = self.data_processor.calculate_satisfaction_index(score_columns)

        # 4. LLM 텍스트 생성
        overall_stats = {
            'basic_stats': basic_stats,
            'satisfaction_analysis': satisfaction_analysis,
            'satisfaction_index': satisfaction_index,
        }

        executive_summary = self.text_generator.generate_executive_summary(
            overall_stats, self.conference_name
        )

        # 5. 보고서 작성
        if output_format == 'markdown':
            report = self._generate_markdown_report(
                basic_stats, satisfaction_analysis, satisfaction_index,
                executive_summary, score_columns, text_columns
            )
        elif output_format == 'html':
            report = self._generate_html_report(
                basic_stats, satisfaction_analysis, satisfaction_index,
                executive_summary, score_columns, text_columns
            )
        elif output_format == 'docx':
            # docx는 파일로 직접 저장해야 하므로 None 반환
            return None
        else:
            raise ValueError(f"지원하지 않는 출력 형식: {output_format}")

        return report

    def _generate_markdown_report(self, basic_stats, satisfaction_analysis,
                                  satisfaction_index, executive_summary,
                                  score_columns, text_columns) -> str:
        """마크다운 형식 보고서 생성"""

        report_sections = []

        # 제목 및 개요
        report_sections.append(f"# {self.conference_name} 참석자 만족도 조사 보고서\n")
        report_sections.append(f"**조사 기간**: {self.survey_date}")
        report_sections.append(f"**응답자 수**: {basic_stats['total_responses']}명")
        report_sections.append(f"**보고서 생성일**: {datetime.now().strftime('%Y년 %m월 %d일')}\n")
        report_sections.append("---\n")

        # 경영진 요약
        report_sections.append("## 경영진 요약 (Executive Summary)\n")
        report_sections.append(executive_summary + "\n")
        report_sections.append("---\n")

        # 주요 지표
        report_sections.append("## 주요 지표\n")
        if satisfaction_index > 0:
            report_sections.append(f"### 전체 만족도 지수: **{satisfaction_index}/100**\n")

            # 만족도 등급
            grade = self._get_satisfaction_grade(satisfaction_index)
            report_sections.append(f"**평가**: {grade}\n")

        # 세부 항목 분석
        if satisfaction_analysis:
            report_sections.append("## 세부 항목별 분석\n")

            for col_name, stats in satisfaction_analysis.items():
                if col_name == 'overall':
                    continue

                # 사용자 정의 항목명 사용
                display_name = self.config.get('column_labels', {}).get(col_name, col_name)

                report_sections.append(f"### {display_name}\n")
                report_sections.append(f"- **평균 점수**: {stats['mean']:.2f}/5.0")
                report_sections.append(f"- **중앙값**: {stats['median']:.2f}")
                report_sections.append(f"- **표준편차**: {stats['std']:.2f}")
                report_sections.append(f"- **응답 수**: {stats['count']}명\n")

                # 분포 시각화 (텍스트 기반)
                if 'distribution_percent' in stats:
                    report_sections.append("**응답 분포**:")
                    for score, percent in sorted(stats['distribution_percent'].items()):
                        bar = '█' * int(percent / 5)  # 5%당 1개 블록
                        report_sections.append(f"- {score}점: {percent:.1f}% {bar}")

                # LLM 생성 분석
                analysis_text = self.text_generator.generate_detailed_analysis(
                    stats, display_name
                )
                report_sections.append(f"\n**분석**: {analysis_text}\n")

        # 주관식 응답 분석
        if text_columns:
            report_sections.append("## 주관식 응답 분석\n")

            for col_name, category in text_columns.items():
                responses = self.data_processor.get_text_responses(col_name)

                if responses:
                    report_sections.append(f"### {category}\n")
                    report_sections.append(f"**응답 수**: {len(responses)}개\n")

                    # LLM 인사이트 생성
                    insights = self.text_generator.generate_insights_from_text_responses(
                        responses, category
                    )
                    report_sections.append(f"{insights}\n")

                    # 샘플 응답 (최대 5개)
                    report_sections.append("**주요 응답 샘플**:")
                    for i, resp in enumerate(responses[:5], 1):
                        report_sections.append(f"{i}. \"{resp}\"")
                    report_sections.append("")

        # 권장사항
        report_sections.append("## 개선 권장사항\n")
        recommendations = self.text_generator.generate_recommendations({
            'satisfaction_index': satisfaction_index,
            'satisfaction_analysis': satisfaction_analysis,
        })
        report_sections.append(recommendations + "\n")

        # 결론
        report_sections.append("## 결론\n")
        conclusion = self.text_generator.generate_conclusion(
            {'satisfaction_index': satisfaction_index}, self.conference_name
        )
        report_sections.append(conclusion + "\n")

        # 부록
        report_sections.append("---\n")
        report_sections.append("## 부록: 상세 통계 데이터\n")
        report_sections.append("```json")
        report_sections.append(json.dumps({
            'basic_stats': basic_stats,
            'satisfaction_analysis': satisfaction_analysis,
        }, ensure_ascii=False, indent=2))
        report_sections.append("```\n")

        return "\n".join(report_sections)

    def _generate_html_report(self, basic_stats, satisfaction_analysis,
                             satisfaction_index, executive_summary,
                             score_columns, text_columns) -> str:
        """HTML 형식 보고서 생성"""

        html_sections = []

        # HTML 헤더
        html_sections.append("""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{} 참석자 만족도 조사 보고서</title>
    <style>
        body {{
            font-family: 'Malgun Gothic', sans-serif;
            line-height: 1.6;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }}
        h3 {{
            color: #555;
        }}
        .summary-box {{
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .metric {{
            font-size: 2em;
            color: #3498db;
            font-weight: bold;
        }}
        .stats {{
            background-color: #f9f9f9;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }}
        .progress-bar {{
            background-color: #ecf0f1;
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
            margin: 5px 0;
        }}
        .progress-fill {{
            background-color: #3498db;
            height: 100%;
            transition: width 0.3s;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
""".format(self.conference_name))

        # 제목
        html_sections.append(f"<h1>{self.conference_name} 참석자 만족도 조사 보고서</h1>")
        html_sections.append(f"<p><strong>조사 기간</strong>: {self.survey_date}</p>")
        html_sections.append(f"<p><strong>응답자 수</strong>: {basic_stats['total_responses']}명</p>")
        html_sections.append(f"<p><strong>보고서 생성일</strong>: {datetime.now().strftime('%Y년 %m월 %d일')}</p>")

        # 경영진 요약
        html_sections.append("<h2>경영진 요약</h2>")
        html_sections.append(f"<div class='summary-box'>{executive_summary}</div>")

        # 주요 지표
        if satisfaction_index > 0:
            html_sections.append("<h2>주요 지표</h2>")
            html_sections.append(f"<div class='summary-box'>")
            html_sections.append(f"<p>전체 만족도 지수</p>")
            html_sections.append(f"<p class='metric'>{satisfaction_index}/100</p>")
            grade = self._get_satisfaction_grade(satisfaction_index)
            html_sections.append(f"<p><strong>평가</strong>: {grade}</p>")
            html_sections.append("</div>")

        # 세부 항목 분석
        if satisfaction_analysis:
            html_sections.append("<h2>세부 항목별 분석</h2>")

            for col_name, stats in satisfaction_analysis.items():
                if col_name == 'overall':
                    continue

                display_name = self.config.get('column_labels', {}).get(col_name, col_name)

                html_sections.append(f"<h3>{display_name}</h3>")
                html_sections.append("<div class='stats'>")
                html_sections.append(f"<p><strong>평균 점수</strong>: {stats['mean']:.2f}/5.0</p>")
                html_sections.append(f"<p><strong>응답 수</strong>: {stats['count']}명</p>")

                # 진행 바
                score_percent = (stats['mean'] / 5.0) * 100
                html_sections.append(f"""
                <div class='progress-bar'>
                    <div class='progress-fill' style='width: {score_percent}%'></div>
                </div>
                """)

                html_sections.append("</div>")

        # HTML 푸터
        html_sections.append("""
        <div class='footer'>
            <p>본 보고서는 AI 기반 자동 생성 시스템으로 작성되었습니다.</p>
        </div>
    </div>
</body>
</html>
""")

        return "\n".join(html_sections)

    def _get_satisfaction_grade(self, index: float) -> str:
        """만족도 지수 기반 등급 산정"""
        if index >= 90:
            return "매우 우수"
        elif index >= 80:
            return "우수"
        elif index >= 70:
            return "양호"
        elif index >= 60:
            return "보통"
        else:
            return "개선 필요"

    def _generate_docx_report(self, basic_stats, satisfaction_analysis,
                             satisfaction_index, executive_summary,
                             score_columns, text_columns, output_path: str):
        """워드 형식 보고서 생성"""
        writer = DocxReportWriter()

        # 제목
        writer.add_title(
            f"{self.conference_name} 참석자 만족도 조사 보고서",
            f"조사 기간: {self.survey_date}"
        )

        # 메타데이터
        metadata = {
            '조사 기간': self.survey_date,
            '응답자 수': f"{basic_stats['total_responses']}명",
            '보고서 생성일': datetime.now().strftime('%Y년 %m월 %d일')
        }
        writer.add_metadata(metadata)

        # 경영진 요약
        writer.add_section('경영진 요약 (Executive Summary)', '', level=1)
        writer.add_highlighted_box(executive_summary)

        # 주요 지표
        if satisfaction_index > 0:
            writer.add_section('주요 지표', '', level=1)
            grade = self._get_satisfaction_grade(satisfaction_index)
            writer.add_stats_table('전체 만족도', {
                '만족도 지수': f'{satisfaction_index}/100',
                '평가 등급': grade
            })

        # 세부 항목별 분석
        if satisfaction_analysis:
            writer.add_section('세부 항목별 분석', '', level=1)

            for col_name, stats in satisfaction_analysis.items():
                if col_name == 'overall':
                    continue

                display_name = self.config.get('column_labels', {}).get(col_name, col_name)

                # LLM 분석 텍스트 생성
                analysis_text = self.text_generator.generate_detailed_analysis(
                    stats, display_name
                )

                writer.add_satisfaction_item(display_name, stats, analysis_text)

        # 주관식 응답 분석
        text_columns = self.config.get('text_columns', {})
        if text_columns:
            writer.add_section('주관식 응답 분석', '', level=1)

            for col_name, category in text_columns.items():
                responses = self.data_processor.get_text_responses(col_name)

                if responses:
                    # LLM 인사이트 생성
                    insights = self.text_generator.generate_insights_from_text_responses(
                        responses, category
                    )
                    writer.add_text_responses(category, responses, insights, max_display=5)

        # 개선 권장사항
        recommendations = self.text_generator.generate_recommendations({
            'satisfaction_index': satisfaction_index,
            'satisfaction_analysis': satisfaction_analysis,
        })
        writer.add_recommendations(recommendations)

        # 결론
        conclusion = self.text_generator.generate_conclusion(
            {'satisfaction_index': satisfaction_index}, self.conference_name
        )
        writer.add_section('결론', conclusion, level=1)

        # 저장
        writer.save(output_path)

    def save_report(self, output_path: str, output_format: str = 'markdown'):
        """보고서 생성 및 저장"""
        if output_format == 'docx':
            # 워드는 별도 처리
            self.data_processor.load_data()

            score_columns = self.config.get('score_columns', [])
            text_columns = self.config.get('text_columns', {})

            basic_stats = self.data_processor.get_basic_stats()
            satisfaction_analysis = {}
            satisfaction_index = 0

            if score_columns:
                satisfaction_analysis = self.data_processor.analyze_satisfaction_scores(score_columns)
                satisfaction_index = self.data_processor.calculate_satisfaction_index(score_columns)

            overall_stats = {
                'basic_stats': basic_stats,
                'satisfaction_analysis': satisfaction_analysis,
                'satisfaction_index': satisfaction_index,
            }

            executive_summary = self.text_generator.generate_executive_summary(
                overall_stats, self.conference_name
            )

            self._generate_docx_report(
                basic_stats, satisfaction_analysis, satisfaction_index,
                executive_summary, score_columns, text_columns, output_path
            )
        else:
            # 마크다운, HTML은 기존 방식
            report = self.generate_full_report(output_format)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)

        print(f"보고서가 생성되었습니다: {output_path}")
        return output_path
