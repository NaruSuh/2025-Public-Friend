"""
LLM 기반 텍스트 생성 모듈
통계 데이터를 기반으로 자연스러운 보고서 텍스트 생성
"""

import anthropic
import os
from typing import Dict, List, Any, Optional


class ReportTextGenerator:
    """LLM을 활용한 보고서 텍스트 생성 클래스"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Anthropic API 키 (없으면 환경변수에서 가져옴)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다")

        self.client = anthropic.Anthropic(api_key=self.api_key)

    def generate_executive_summary(self, stats: Dict[str, Any],
                                   conference_name: str = "학회") -> str:
        """경영진 요약 생성"""

        prompt = f"""
다음 설문조사 통계 데이터를 바탕으로 {conference_name} 참석자 만족도 조사의 경영진 요약(Executive Summary)를 작성해주세요.

통계 데이터:
{self._format_stats(stats)}

요구사항:
1. 200-300자 분량의 간결한 요약
2. 핵심 수치와 인사이트 포함
3. 전문적이고 객관적인 톤
4. 주요 강점과 개선점 언급
5. 한국어로 작성

경영진 요약:
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    def generate_detailed_analysis(self, column_stats: Dict[str, Any],
                                   item_name: str) -> str:
        """세부 항목 분석 텍스트 생성"""

        prompt = f"""
다음 설문조사 항목 "{item_name}"의 통계 데이터를 바탕으로 상세한 분석 텍스트를 작성해주세요.

통계 데이터:
{self._format_stats(column_stats)}

요구사항:
1. 100-150자 분량
2. 평균, 분포, 특이사항 언급
3. 데이터 기반의 객관적 분석
4. 전문적인 보고서 스타일
5. 한국어로 작성

분석:
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    def generate_insights_from_text_responses(self, responses: List[str],
                                              category: str = "주관식 응답") -> str:
        """주관식 응답 분석 및 인사이트 도출"""

        # 너무 많으면 샘플링
        sample_responses = responses[:50] if len(responses) > 50 else responses

        prompt = f"""
다음은 설문조사의 "{category}" 항목에 대한 응답들입니다.

응답 목록:
{self._format_text_responses(sample_responses)}

총 응답 수: {len(responses)}개

요구사항:
1. 주요 테마와 패턴 파악
2. 긍정적 피드백과 개선 요청사항 분류
3. 빈도가 높은 키워드 추출
4. 200-300자 분량으로 요약
5. 한국어로 작성

인사이트:
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    def generate_recommendations(self, overall_stats: Dict[str, Any]) -> str:
        """개선 권장사항 생성"""

        prompt = f"""
다음 설문조사 통계 데이터를 바탕으로 향후 학회 개선을 위한 권장사항을 작성해주세요.

통계 데이터:
{self._format_stats(overall_stats)}

요구사항:
1. 3-5개의 구체적인 권장사항
2. 데이터 기반의 근거 제시
3. 실행 가능한 제안
4. 우선순위 고려
5. 한국어로 작성
6. 불릿 포인트 형식

권장사항:
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    def generate_conclusion(self, stats: Dict[str, Any],
                           conference_name: str = "학회") -> str:
        """결론 생성"""

        prompt = f"""
다음 설문조사 통계 데이터를 바탕으로 {conference_name} 참석자 만족도 조사의 결론을 작성해주세요.

통계 데이터:
{self._format_stats(stats)}

요구사항:
1. 150-200자 분량
2. 전체적인 성과 평가
3. 긍정적인 마무리
4. 향후 전망 언급
5. 한국어로 작성

결론:
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    def _format_stats(self, stats: Dict[str, Any]) -> str:
        """통계 데이터를 읽기 쉬운 형식으로 변환"""
        import json
        return json.dumps(stats, ensure_ascii=False, indent=2)

    def _format_text_responses(self, responses: List[str]) -> str:
        """텍스트 응답을 읽기 쉬운 형식으로 변환"""
        formatted = []
        for i, resp in enumerate(responses[:30], 1):  # 최대 30개만
            formatted.append(f"{i}. {resp}")
        return "\n".join(formatted)

    def generate_custom_section(self, prompt_text: str, context: Dict[str, Any]) -> str:
        """사용자 정의 섹션 생성"""

        full_prompt = f"""
{prompt_text}

참고 데이터:
{self._format_stats(context)}

한국어로 작성해주세요.
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": full_prompt}]
        )

        return response.content[0].text.strip()
