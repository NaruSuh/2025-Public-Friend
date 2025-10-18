"""
CLI 툴: OpenAI Chat Completions API 호출 테스트 및 진단.

이 도구는 지정된 모델과 프롬프트를 사용하여 OpenAI Chat Completions API를 호출하고,
성공 여부와 함께 할당량(Quota) 부족, API 키 오류 등 일반적인 문제에 대한
진단 및 해결 가이드를 제공합니다.

사용법:
    python3 tools/openai_responses_diagnose.py \
        --model gpt-4o-mini \
        --prompt "ping" \
        --api-key sk-xxxx

또는 환경 변수로 OPENAI_API_KEY 설정 후 실행:
    export OPENAI_API_KEY=sk-xxxx
    python3 tools/openai_responses_diagnose.py
"""

import argparse
import os
import sys
import textwrap
from typing import Dict, Optional

from openai import OpenAI, RateLimitError, AuthenticationError, APIError

# --- 상수 정의 ---
DEFAULT_PROMPT = "Ping test from SlavaTalk diagnostics."
DEFAULT_MODEL = "gpt-4o-mini"

# 오류 메시지 키워드와 해결 가이드를 매핑 (확장성 용이)
ERROR_GUIDANCE_MAP: Dict[str, str] = {
    "insufficient_quota": textwrap.dedent(
        """
        ➤ 해결 가이드 (할당량 부족):
          1. https://platform.openai.com/account/billing/overview 에서 유효한 결제 수단 등록
          2. Usage limits (Soft/Hard limit) 값이 0이 아닌지 확인
          3. Free trial credit이 만료된 경우 Pay-as-you-go 전환 후 새 API 키 발급
        """).strip(),
    "invalid api key": "➤ 해결 가이드 (잘못된 API 키): API 키가 올바른지, 비활성화되지 않았는지 확인하고 새 키를 발급하여 다시 시도하세요.",
    "rate limit": "➤ 해결 가이드 (요청 한도 초과): 잠시 후 다시 시도하거나, 분당/일일 요청 한도를 확인하고 호출 빈도를 조절하세요.",
}


class OpenAIDiagnosticTool:
    """OpenAI API 호출과 진단 로직을 캡슐화한 클래스."""

    def __init__(self, api_key: str, model: str, prompt: str):
        """진단 도구를 초기화하고 OpenAI 클라이언트를 설정합니다."""
        self._api_key = api_key
        self.model = model
        self.prompt = prompt
        try:
            self.client = OpenAI(api_key=self._api_key)
        except Exception as e:
            raise SystemExit(f"❌ OpenAI 클라이언트 초기화 실패: {e}")

    def _get_error_guidance(self, error_message: str) -> Optional[str]:
        """오류 메시지를 분석하여 적절한 해결 가이드를 반환합니다."""
        lower_msg = error_message.lower()
        for keyword, guidance in ERROR_GUIDANCE_MAP.items():
            if keyword in lower_msg:
                return guidance
        return None

    def run_diagnostic(self) -> None:
        """Chat Completions API를 호출하고 결과를 진단하여 출력합니다."""
        print(f"- 모델: {self.model}, 프롬프트: {self.prompt!r}로 진단을 시작합니다...")
        try:
            # [BUG FIX] 존재하지 않는 `responses.create` -> `chat.completions.create`로 수정
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": self.prompt},
                ],
                max_tokens=64,
            )

            # [ENHANCEMENT] 더 상세한 성공 정보 출력
            print("\n✅ API 호출 성공")
            choice = response.choices[0]
            usage = response.usage
            print(textwrap.dedent(f"""
                  - ID: {response.id}
                  - Model: {response.model}
                  - Finish Reason: {choice.finish_reason}
                  - Token Usage: Prompt={usage.prompt_tokens}, Completion={usage.completion_tokens}, Total={usage.total_tokens}
            """))
            print("--- 응답 미리보기 ---")
            print(textwrap.indent(choice.message.content.strip(), '    '))

        except (RateLimitError, AuthenticationError, APIError) as exc:
            error_message = str(exc)
            guidance = self._get_error_guidance(error_message)

            print(f"\n❌ API 호출 실패: {type(exc).__name__}")
            print(f"   {error_message}")
            if guidance:
                print(guidance)
            sys.exit(1)
        except Exception as exc:
            print(f"\n❌ 예상치 못한 오류 발생: {exc}")
            sys.exit(1)

def main() -> None:
    """CLI 인자를 파싱하고 진단 도구를 실행합니다."""
    parser = argparse.ArgumentParser(
        description="OpenAI Chat Completions API 호출 테스트 도구",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--api-key", help="OpenAI API 키 (미지정 시 환경 변수 OPENAI_API_KEY 사용)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"모델명 (기본값: {DEFAULT_MODEL})")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="테스트에 사용할 프롬프트 문장")
    args = parser.parse_args()

    try:
        api_key = args.api_key or os.environ["OPENAI_API_KEY"]
    except KeyError:
        raise SystemExit(
            "❌ API 키를 찾을 수 없습니다. --api-key 옵션을 사용하거나 "
            "환경 변수 OPENAI_API_KEY 를 설정하세요."
        )

    tool = OpenAIDiagnosticTool(api_key=api_key, model=args.model, prompt=args.prompt)
    tool.run_diagnostic()


if __name__ == "__main__":
    main()