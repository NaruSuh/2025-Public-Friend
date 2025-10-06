# Appducator 코드 감사 보고서 (LLM 협업용)

**감사 일시**: 2025-10-06
**감사 대상**: `streamlit_app.py`, `app_utils.py`
**감사자**: Gemini

---

## 1. 개요

`Appducator` 애플리케이션의 핵심 로직(`streamlit_app.py`, `app_utils.py`)에 대한 코드 감사를 수행했습니다.

전반적으로, 코드는 명확하고 잘 구조화되어 있으며 Streamlit의 캐싱 및 세션 상태 기능을 효과적으로 활용하고 있습니다. 그러나 프로덕션 환경에서 운영될 경우를 대비하여 보안, 성능, 안정성 측면에서 몇 가지 개선이 필요한 영역이 발견되었습니다.

본 보고서는 다른 LLM 에이전트(Claude, Codex 등)가 후속 디버깅 및 개선 작업을 수행할 수 있도록 구체적인 문제점과 해결 방안을 제시합니다.

---

## 2. 감사 요약

| 영역 | 심각도 | 요약 |
|---|---|---|
| **보안 (Security)** | **High** | `unsafe_allow_html=True` 사용으로 인한 잠재적 XSS(Cross-Site Scripting) 취약점 |
| **성능 (Performance)** | **Medium** | 대규모 문서/용어집 처리 시 `highlight_terms` 함수의 성능 저하 가능성 |
| **안정성 (Reliability)** | **Medium** | JSON 파일 동시 접근 시 Race Condition 및 파싱 오류 처리 부재 |
| **코드 품질 (Quality)** | **Low** | 일부 경로 하드코딩 및 개선 가능한 로직 존재 |

---

## 3. 상세 분석 및 개선 제안

### High-1: 잠재적 XSS(Cross-Site Scripting) 취약점

-   **파일**: `streamlit_app.py`
-   **문제점**: `st.markdown(..., unsafe_allow_html=True)`를 사용하여 HTML을 렌더링하는 부분이 다수 존재합니다. `markdown_to_html` 함수를 거친 결과물(`highlighted_html`)과 사용자가 관리하는 `vocabulary.json`의 내용이 필터링 없이 렌더링됩니다. 만약 교육 자료(.md 파일)나 용어집(vocabulary.json)에 악의적인 `<script>` 태그가 포함될 경우, 사용자의 브라우저에서 그대로 실행되어 쿠키 탈취 등의 공격에 노출될 수 있습니다.
-   **영향**: 신뢰할 수 없는 마크다운 파일이나 용어집 데이터가 시스템에 포함될 경우, 애플리케이션을 사용하는 모든 사용자가 XSS 공격에 취약해집니다.
-   **개선 제안**:
    1.  HTML 렌더링 전, `bleach`와 같은 라이브러리를 사용하여 허용된 태그와 속성만 남기고 모두 제거(Sanitization)해야 합니다.
    2.  `app_utils.py`에 HTML 정화 함수를 추가하고, `st.markdown`으로 출력하기 전에 모든 HTML 콘텐츠가 이 함수를 통과하도록 파이프라인을 수정하는 것을 권장합니다.

    ```python
    # app_utils.py에 추가할 예시
    import bleach

    ALLOWED_TAGS = ['p', 'h1', 'h2', 'h3', 'h4', 'strong', 'em', 'ul', 'ol', 'li', 'code', 'pre', 'span', 'br', 'a', 'table', 'thead', 'tbody', 'tr', 'th', 'td']
    ALLOWED_ATTRS = {
        '*': ['class'],
        'a': ['href', 'title'],
        'span': ['class', 'data-term', 'data-tooltip'],
    }

    def sanitize_html(html_content: str) -> str:
        """HTML 콘텐츠에서 잠재적으로 위험한 태그와 속성을 제거합니다."""
        return bleach.clean(html_content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)

    # streamlit_app.py 에서 사용
    # ...
    # safe_html = sanitize_html(highlighted_html)
    # st.markdown(f"<div class='md-viewer'>{safe_html}</div>", unsafe_allow_html=True)
    ```

### Medium-1: 어휘집 하이라이팅 성능 저하 가능성

-   **파일**: `app_utils.py`의 `highlight_terms` 함수
-   **문제점**: 현재 로직은 용어집(`glossary`)에 있는 모든 용어에 대해 개별 정규식을 생성하고, 문서의 모든 텍스트 노드를 순회하며 정규식을 실행합니다. 용어집에 수천 개의 용어가 있거나, 문서가 매우 길 경우 이 과정은 심각한 성능 병목을 유발할 수 있습니다.
-   **영향**: 문서 로딩 시간이 길어져 사용자 경험을 저해합니다.
-   **개선 제안**:
    1.  모든 용어를 `|`로 연결하여 하나의 거대한 정규식으로 컴파일하면, 텍스트 노드 순회를 한 번만 수행할 수 있어 성능이 크게 향상됩니다.
    2.  용어 길이를 기준으로 정렬하여 더 긴 용어가 먼저 매치되도록 한 것은 매우 좋은 접근입니다. 이 로직은 유지하면서 정규식을 하나로 합치는 것을 권장합니다.

    ```python
    # highlight_terms 함수 개선 예시
    def highlight_terms(html_text: str, glossary: Dict[str, Dict[str, str]]) -> Tuple[str, List[str]]:
        # ...
        sorted_terms = sorted(glossary.keys(), key=len, reverse=True)
        
        # 모든 용어를 하나의 정규식으로 결합
        combined_pattern = re.compile(
            rf"(?<![\w-])({ '|'.join(re.escape(term) for term in sorted_terms) })(?![\w-])",
            re.IGNORECASE
        )
        
        # ... (이하 로직은 이 combined_pattern을 사용하여 텍스트 노드 순회)
    ```

### Medium-2: 상태 관리 및 동시성 문제

-   **파일**: `app_utils.py`의 `load_vocabulary`, `save_vocabulary`
-   **문제점**: `vocabulary.json` 파일을 직접 읽고 쓰는 방식은 상태 관리의 출처가 로컬 파일 시스템에 의존하게 됩니다. Streamlit Cloud와 같은 다중 인스턴스 환경이나 여러 사용자가 동시에 접속하는 환경에서는 파일 잠금(File Lock) 없이는 Race Condition이 발생하여 데이터가 손상될 수 있습니다.
-   **영향**: 사용자 데이터가 유실되거나 깨질 수 있습니다.
-   **개선 제안**:
    *   **단기**: 파일 저장 시 `fcntl` (Unix) 또는 `msvcrt` (Windows)를 사용한 파일 잠금을 구현하여 동시 쓰기를 방지합니다.
    *   **장기**: 사용자별 데이터를 관리하기 위해 `st.session_state`를 넘어, 서버 측 세션 관리나 사용자별 데이터베이스(예: SQLite, 또는 클라우드 DB)를 도입하는 것을 고려해야 합니다. 이는 앱의 확장성을 크게 향상시킬 것입니다.

### Low-1: 안정성을 위한 예외 처리 부재

-   **파일**: `app_utils.py`의 `load_glossary`, `load_vocabulary`
-   **문제점**: `json.load(f)` 실행 중 `glossary.json` 또는 `vocabulary.json` 파일의 내용이 손상되어 유효한 JSON 형식이 아닐 경우, `json.JSONDecodeError`가 발생하여 애플리케이션 전체가 중단됩니다.
-   **영향**: 설정 파일 하나가 손상되면 앱 전체를 사용할 수 없게 됩니다.
-   **개선 제안**: `try...except json.JSONDecodeError` 블록으로 감싸고, 파싱 실패 시 빈 데이터(`{}` 또는 `[]`)를 반환하고 `st.error`나 로그를 통해 관리자에게 파일 손상 사실을 알리도록 수정합니다.

    ```python
    # load_glossary 개선 예시
    def load_glossary() -> Dict[str, Dict[str, str]]:
        # ...
        try:
            with GLOSSARY_PATH.open(encoding="utf-8") as f:
                raw = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # 파일이 없거나 손상된 경우 빈 용어집 반환
            return {}
        # ...
    ```

---

## 4. 결론

`Appducator`는 교육 콘텐츠를 효과적으로 전달하기 위한 훌륭한 아이디어를 기반으로 잘 구현된 애플리케이션입니다. 위에 제시된 개선안, 특히 **보안 정화(Sanitization) 로직 추가**를 최우선으로 적용한다면, 더욱 안정적이고 안전하며 확장 가능한 서비스로 발전할 수 있을 것입니다.
