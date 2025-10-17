# `slava_talk/pages/2_❓_Quiz.py` 디버깅 및 개선 계획

## 개요
본 문서는 `2_❓_Quiz.py` 파일에 존재하는 여러 UI 및 기능 오류를 해결하기 위한 전수 검사 기반의 디버깅 및 개선 계획을 기술한다.

---

## 1. JavaScript 단축키 및 TTS 기능 오류

### 문제
- **브라우저 내장 TTS**: [발음 듣기] 버튼이 작동하지 않음.
- **키보드 단축키**: 숫자(1~n), Space, P 키 등 모든 단축키가 먹통임.

### 원인 분석
Streamlit은 보안을 위해 `st.markdown` 내의 `onclick` 같은 인라인 이벤트 핸들러를 제거한다. 이 때문에 버튼 클릭이 작동하지 않는다. 또한, 현재 `setTimeout`을 사용한 스크립트 실행 지연 방식은 Streamlit의 동적 DOM 렌더링 환경에서 불안정하여, 스크립트가 실행되는 시점에 버튼, 라디오 버튼 등의 DOM 요소가 존재하지 않을 수 있다. 이 타이밍 문제가 모든 JavaScript 기능 실패의 근본 원인이다.

### 해결 방안
안정적인 이벤트 처리를 위해 JavaScript 로직을 전면 재설계한다.

1.  **이벤트 위임 (Event Delegation) 패턴 적용**:
    -   `document` 최상위 레벨에 `click`과 `keydown` 이벤트 리스너를 단 한 번만 등록한다.
    -   이벤트 발생 시, `event.target`을 확인하여 클릭된 요소가 `.tts-button` 클래스를 가졌는지, 또는 특정 키가 눌렸는지 등을 판별하여 적절한 함수를 호출한다. 이 방식은 DOM 요소가 동적으로 추가/삭제되어도 안정적으로 작동한다.

2.  **데이터 직접 주입**:
    -   JavaScript가 DOM에서 읽어야 할 데이터(예: 발음할 우크라이나어 단어)를 `getElementById`로 찾는 대신, Python에서 스크립트를 생성할 때 데이터 자체를 JavaScript 변수나 `data-*` 속성에 직접 주입한다.
    -   **예시**: `tts-button`에 `data-word-to-speak="{ukrainian_word}"` 속성을 추가하고, JS에서는 `event.target.dataset.wordToSpeak`으로 단어를 가져온다.

3.  **통합 스크립트 재구성**:
    -   모든 JS 함수(TTS, 단축키)를 하나의 `<script>` 태그 안에 정의하고, 페이지 최하단에 한 번만 주입하여 실행 순서 문제를 해결한다.

---

## 2. 단축키 재설정

### 문제
- Pass & 복습 단축키가 `Enter`로 작동해야 하지만, 현재 `Submit`의 단축키(`Space` 또는 `Enter`)에 포함되어 있다.

### 해결 방안
`keydown` 이벤트 리스너의 로직을 다음과 같이 수정한다.

1.  **Submit 로직**: `event.key === ' ' || event.key === 'Enter'` 조건을 `event.key === ' '`만 감지하도록 변경한다.
2.  **Pass & 복습 로직**: `event.key === 'p' || event.key === 'P'` 조건을 `event.key === 'Enter' || event.key === 'p' || event.key === 'P'`로 변경하여 `Enter` 키에도 반응하도록 한다.
3.  **권장 사항**: 사용자 혼동을 막기 위해, 변경된 단축키에 맞춰 버튼의 레이블도 `st.form_submit_button("✅ Submit (Space)")` 및 `st.button("📖 Pass & 복습 (Enter/P)", ...)`와 같이 수정한다.

---

## 3. 중복 정답 정보 제거

### 문제
- 정답/오답 판정 후, 이미 아는 정보를 담은 `answer_card` (우크라이나어, 발음, 한국어, 영어 뜻)가 중복으로 표시된다.

### 해결 방안
- `if submitted:` 블록 내에서 `answer_card`를 생성하고 `st.markdown(answer_card, unsafe_allow_html=True)`를 호출하는 부분을 찾아 삭제하거나 주석 처리한다.

---

## 4. AI 피드백 UI 개선

### 문제
- AI 피드백이 페이지의 다른 부분에 작게 표시되어 가독성이 떨어진다.
- 피드백의 위치가 직관적이지 않다.

### 해결 방안
1.  **위치 변경**:
    -   현재 `st.session_state.quiz_feedback`을 `st.caption`으로 표시하는 로직을 찾는다.
    -   이 로직을 두 번째 "퀴즈 컨트롤" 버튼 그룹(`st.button(..., key="next_bottom")` 등) 바로 아래로 이동시킨다.

2.  **스타일 변경**:
    -   `st.caption()` 대신 `st.markdown()`을 사용한다.
    -   인라인 CSS를 적용하여 폰트 크기를 11pt로 설정한다.
    -   **예시 코드**:
        ```python
        if st.session_state.quiz_feedback:
            feedback_html = f'<div style="font-size: 11pt; margin-top: 1rem;">{st.session_state.quiz_feedback}</div>'
            st.markdown(feedback_html, unsafe_allow_html=True)
        ```
