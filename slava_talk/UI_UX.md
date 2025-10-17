# SlavaTalk 앱 UI/UX 개선 계획서

**작성일:** 2025년 10월 17일
**작성자:** Gemini (UI/UX Auditor)

## 1. 문제 진단

- **현상:** `Document_Study` 페이지의 단어 카드 UI가 의도대로 표시되지 않고, 레이아웃이 깨지거나 스타일이 잘못 적용되는 문제가 발생하고 있음.
- **추정 원인:** 파이썬 코드 내에 복잡한 HTML/CSS를 직접 주입(`st.markdown(unsafe_allow_html=True)`)하는 방식이 Streamlit의 기본 렌더링 방식과 충돌하여 발생. 이 방식은 불안정하고 유지보수가 매우 어려움.

---

## 2. 해결 원칙

1.  **구조와 스타일의 분리:** 파이썬 코드에서는 데이터와 레이아웃 구조만 담당하고, 모든 시각적 스타일은 별도의 CSS 파일에서 관리한다.
2.  **Streamlit 친화적 설계:** `st.container`와 `st.columns`를 적극 활용하여 안정적이고 반응형인 레이아웃을 구성한다.
3.  **컴포넌트화:** 반복되는 UI 요소(단어 카드)는 재사용 가능한 함수로 만들어 코드 중복을 없애고 유지보수를 용이하게 한다.

---

## 3. 실행 계획 (Actionable Directives)

아래 4단계 지침에 따라 UI/UX를 전면적으로 리팩토링하여, 전문가 수준의 안정적이고 미려한 디자인을 구현한다.

### **Directive 1: 중앙 CSS 파일 생성 및 스타일 정의**

- **목표:** 앱의 모든 시각적 스타일을 한 곳에서 관리하는 중앙 CSS 파일을 생성한다.
- **명령:**
```vibe
CREATE a new directory `assets` in the project root.
CREATE a new file `assets/style.css` inside it.
POPULATE `style.css` with CSS classes for a modern, clean vocabulary card design.
DEFINE a professional color palette (e.g., dark text for readability, a light-gray background for comfort, and Ukrainian flag colors #0057B7 (blue) and #FFD700 (gold) as accent colors).

/* Example CSS for style.css */
.vocab-card {
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 15px;
    margin-bottom: 10px;
    background-color: #f9f9f9;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.ukrainian-text {
    font-size: 24px;
    font-weight: 600;
    color: #0057B7;
}
.pronunciation {
    font-style: italic;
    color: #555;
    margin-bottom: 10px;
}
.topic-tag {
    display: inline-block;
    padding: 3px 8px;
    background-color: #FFD700;
    color: #333;
    border-radius: 5px;
    font-size: 12px;
    margin-right: 5px;
}
```

### **Directive 2: CSS 로더 유틸리티 함수 생성**

- **목표:** `style.css` 파일을 읽어 모든 Streamlit 페이지에 일괄적으로 적용하는 함수를 만든다.
- **명령:**
```vibe
CREATE a new file `modules/ui_components.py` if it doesn't exist.
ADD a function `apply_custom_css()` to this module.
IMPLEMENT this function to open `assets/style.css`, read its content, and inject it into the Streamlit app using `st.markdown(f"<style>{{css}}</style>", unsafe_allow_html=True)`.
REASON: This allows a single point of control for the entire app's styling.
```

### **Directive 3: 단어 카드 렌더링 로직 리팩토링**

- **목표:** 깨진 HTML 주입 방식 대신, Streamlit 네이티브 레이아웃과 CSS 클래스를 사용하는 안정적인 카드 렌더링 함수를 구현한다.
- **명령:**
```vibe
REFACTOR the vocabulary display loop in `pages/1_📚_Document_Study.py`.
IN `modules/ui_components.py`, CREATE a new function `render_vocab_card(item: dict)`.
INSIDE this function, use `st.container()` as the main card body and assign it the `vocab-card` CSS class.
USE `st.columns()` to structure the internal layout (e.g., word on the left, buttons on the right).
USE `st.markdown()` with the new CSS class names (e.g., `<p class='ukrainian-text'>...</p>`) to style the text elements.
REPLACE the old, broken loop in the page file with a simple loop that calls `render_vocab_card(item)` for each vocabulary item.
REASON: This separates logic from presentation, making the UI stable, responsive, and easy to modify.
```

### **Directive 4: CSS 로더 전역 적용**

- **목표:** 앱의 모든 페이지에 일관된 디자인을 적용한다.
- **명령:**
```vibe
IMPORT the `apply_custom_css` function in `streamlit_app.py` and in every file inside the `pages/` directory.
CALL `apply_custom_css()` at the beginning of each of these files.
REASON: This ensures a consistent, professional look and feel across the entire application.
```

---

## 4. 결론

상기 지침들은 현재 발생한 UI 깨짐 문제를 해결할 뿐만 아니라, 향후 앱의 유지보수성과 확장성을 극대화하는 전문가 수준의 리팩토링 계획입니다. 이 계획을 따르면 `SlavaTalk` 앱은 훨씬 더 안정적이고 시각적으로 뛰어난 학습 도구로 거듭날 것입니다.
