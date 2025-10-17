# SlavaTalk 앱 코드 감사 및 고도화 계획 (BATON_TOUCH v2)

**작성일:** 2025년 10월 17일
**작성자:** Gemini (Code Auditor)

## 1. 개요

이전 감사(`BATON_TOUCH v1`)에서 지적된 치명적 오류(핵심 모듈 부재)는 해결되었으며, 현재 애플리케이션은 정상적으로 작동 가능한 상태입니다. 본 문서는 현재 코드를 기반으로, 앱의 **성능, 지능, 사용자 경험**을 최고 수준으로 끌어올리기 위한 구체적인 고도화 지침을 'Vibe Coding' 명령 형식으로 기술합니다.

---

## 2. 고도화 지침 (Actionable Directives)

### **Directive 1: 데이터 로딩 성능 최적화**

- **대상 파일:** `modules/data_loader.py`
- **명령:**
```vibe
REFECTOR `modules/data_loader.py`.
APPLY Streamlit's `@st.cache_data` decorator to the `load_vocab` function.
REASON: This will cache the vocabulary data in memory, drastically improving performance by eliminating redundant file I/O on every user interaction.
```

### **Directive 2: PDF 처리기 지능 강화 (NLP 도입)**

- **대상 파일:** `modules/pdf_processor.py`
- **명령:**
```vibe
OVERHAUL `modules/pdf_processor.py`.
REMOVE the hardcoded `KEYWORDS` list.
INTEGRATE the `spaCy` library (add to requirements.txt).
IMPLEMENT a new keyword extraction mechanism that performs Part-of-Speech (POS) tagging on the PDF text and automatically identifies key nouns (NOUN), proper nouns (PROPN), and verbs (VERB) as vocabulary candidates.
REASON: This transitions the processor from a static, manual system to a dynamic, intelligent one that can learn from any document.
```

### **Directive 3: 예문 번역 자동화 (AI 연동)**

- **대상 파일:** `modules/pdf_processor.py`
- **명령:**
```vibe
ENHANCE the overhauled `pdf_processor.py`.
INTEGRATE the `openai` library.
FOR each extracted example sentence (`example_sentence_ukr`):
  CALL the GPT-4 API with a prompt to translate the Ukrainian sentence to high-quality English.
  UPDATE the `example_sentence_eng` field, replacing the `(Translation not available...)` placeholder with the AI-generated translation.
ENSURE API key is accessed securely via `st.secrets`.
REASON: This provides immediate contextual understanding for users and fulfills the app's promise of AI enrichment.
```

### **Directive 4: 학습 페이지 UI/UX 개선**

- **대상 파일:** `pages/1_📚_Document_Study.py`
- **명령:**
```vibe
REFECTOR `pages/1_📚_Document_Study.py`.
INSIDE the `st.expander` for each vocabulary item:
  REPLACE the `st.markdown` for 'Topics' with interactive `st.button` elements for each topic tag, using `use_container_width=True`.
  WHEN a topic button is clicked, it should trigger a callback function that updates the `st.session_state` for the sidebar's multiselect filter, effectively filtering the entire view for that topic.
REASON: This creates a more dynamic and intuitive user experience, allowing seamless exploration of related terms.
```

### **Directive 5: 퀴즈 페이지 상태 관리 리팩토링**

- **대상 파일:** `pages/2_❓_Quiz.py`
- **명령:**
```vibe
REFECTOR the state management in `pages/2_❓_Quiz.py`.
REMOVE all `st.rerun()` calls.
ATTACH the `generate_new_question` function as an `on_click` callback directly to the 'Next ▶️' and 'Skip ❌' buttons.
PASS necessary arguments (question_mode, n_options) to the callback using `args` or `kwargs`.
REASON: This aligns with modern Streamlit best practices, making state transitions more predictable and eliminating potential side-effects of forced reruns.
```

### **Directive 6: 사용자 대시보드 기능 신설**

- **대상 파일:** (신규) `pages/3_📊_Progress_Dashboard.py`
- **명령:**
```vibe
CREATE a new page `pages/3_📊_Progress_Dashboard.py`.
ON this page, ACCESS the `st.session_state.quiz_history` list.
CALCULATE and DISPLAY key performance metrics using `st.metric`: 'Overall Accuracy (%)', 'Total Quizzed Words', and 'Current Streak'.
ANALYZE the history to identify the user's most frequently missed words.
DISPLAY a list or table of these 'Words to Revisit' to guide future study.
REASON: This provides users with valuable feedback on their learning progress and helps them focus on areas of weakness, increasing learning efficiency.
```

---

## 3. 결론

상기 지침들은 `SlavaTalk` 앱을 단순한 '작동하는' 프로토타입에서, 사용자가 실질적인 가치를 느끼는 '효과적인' 학습 도구로 전환시키는 핵심적인 다음 단계입니다. 후속 개발자는 이 지침에 따라 각 모듈을 체계적으로 고도화할 수 있습니다.