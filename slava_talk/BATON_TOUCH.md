# SlavaTalk 앱 코드 감사 및 고도화 계획 (BATON_TOUCH v3)

**작성일:** 2025년 10월 17일
**작성자:** Gemini (Code Auditor)

## 1. 개요

이전 감사(v1, v2) 이후, `slava_talk` 앱은 누락된 모듈이 복구되고 UI/UX가 대폭 개선되어, 현재 **정상적으로 작동하는 고기능 프로토타입(High-Fidelity Prototype)** 상태입니다. 본 문서는 현재의 높은 코드 품질을 전제로, 앱의 **정확성, 효율성, 유지보수성**을 전문가 수준으로 끌어올리기 위한 최종 리팩토링 및 최적화 지침을 'Vibe Coding' 명령 형식으로 기술합니다.

---

## 2. 고도화 지침 (Actionable Directives)

### **Directive 1: PDF 처리기의 NLP 정확도 최적화**

- **대상 파일:** `modules/pdf_processor.py`
- **배경:** 현재 PDF 처리기는 범용 다국어 모델(`xx_sent_ud_sm`)을 사용하고 있어, 우크라이나어의 미묘한 문법적 특성을 완벽하게 처리하지 못할 수 있습니다.
- **명령:**
```vibe
REFECTOR the `_get_nlp` function in `modules/pdf_processor.py`.
REPLACE the generic `xx_sent_ud_sm` spaCy model with the language-specific `uk_core_news_sm` model.
ADD robust error handling for the model download and loading process to guide the user if the model is not present.
REASON: This will significantly improve the accuracy of Part-of-Speech (POS) tagging and lemmatization for Ukrainian, leading to higher quality keyword extraction.
```

### **Directive 2: 데이터 처리 파이프라인 통합 및 효율화**

- **대상 파일:** `tools/pdf_processor.py`, `tools/batch_update_examples.py`
- **배경:** 현재 단어 추출과 예문 생성이 별개의 스크립트로 분리되어 있어 워크플로우가 비효율적입니다.
- **명령:**
```vibe
CONSOLIDATE data processing logic into a single, powerful tool.
RENAME `tools/pdf_processor.py` to `tools/data_pipeline.py`.
INTEGRATE the functionality of `tools/batch_update_examples.py` into the new `data_pipeline.py`.
ADD a new CLI flag `--generate-examples` to the pipeline script.
IF this flag is present, after harvesting and saving new vocabulary, CHAIN the AI example generation process for the newly added terms.
DEPRECATE the now-redundant `batch_update_examples.py` script.
REASON: This creates a single, unified, and more powerful data pipeline, reduces script redundancy, and streamlines the entire vocabulary enrichment workflow.
```

### **Directive 3: 퀴즈 페이지 통계 로직 가독성 및 성능 개선**

- **대상 파일:** `pages/2_❓_Quiz.py`
- **배경:** 현재 최고 스트릭(max streak)을 계산하는 코드가 한 줄의 복잡한 리스트 컴프리헨션으로 작성되어 가독성이 떨어지고, 데이터가 많아질 경우 성능 저하의 원인이 될 수 있습니다.
- **명령:**
```vibe
REFACTOR the max streak calculation logic in `pages/2_❓_Quiz.py`.
CREATE a new helper function `calculate_max_streak(history: list) -> int` within the script.
IMPLEMENT an efficient, readable algorithm inside this function to iterate through the history and find the longest sequence of correct answers.
REPLACE the complex one-liner in the main UI with a simple call to this new, well-documented helper function.
REASON: This improves code readability, maintainability, and performance, making the logic easier to debug and understand for other developers.
```

### **Directive 4: UI 렌더링 로직 컴포넌트화**

- **대상 파일:** `pages/1_📚_Document_Study.py` 및 `modules/ui_components.py`
- **배경:** AI 레슨 결과를 출력하는 UI 로직이 `Document_Study.py` 페이지 파일 내에 길게 작성되어 있어, 페이지의 복잡도를 높이고 코드 재사용을 어렵게 합니다.
- **명령:**
```vibe
DECOUPLE rendering logic from page logic in `pages/1_📚_Document_Study.py`.
CREATE a new function `render_ai_lesson(lesson: dict)` in `modules/ui_components.py`.
MOVE the entire `if/else` block responsible for rendering flashcards, drills, and mission briefs from the page file into this new function.
CALL the new `render_ai_lesson(lesson)` function from the main page to display the results.
REASON: This follows the principle of Separation of Concerns, making the page logic cleaner and the rendering logic reusable and easier to test independently.
```

---

## 3. 결론

상기 지침들은 `SlavaTalk` 앱의 내부 코드 품질을 전문가 수준으로 끌어올리는 데 초점을 맞춥니다. 이 리팩토링 작업들은 앱의 안정성을 높이고, 향후 새로운 기능을 추가하거나 유지보수할 때의 효율성을 극대화할 것입니다. 후속 개발자는 이 지침에 따라 각 모듈을 체계적으로 고도화할 수 있습니다.
