# 10 - Product and Leadership
# 10 - 제품과 리더십

You've mastered the technical skills to build almost anything. The final level of Vibe Coding is about deciding *what* to build and leading the effort to make it successful. This involves moving beyond code to understand product, strategy, and people.
거의 모든 것을 만들 수 있는 기술을 익혔다면, Vibe Coding의 마지막 단계는 *무엇을* 만들지 결정하고 그것을 성공으로 이끄는 것입니다. 이는 코드를 넘어 제품, 전략, 사람을 이해하는 영역입니다.

## Before You Begin
## 시작하기 전에
-   Re-read Level 1’s product notes so personas, JTBD, and basic analytics are fresh in your mind.
-   레벨 1의 제품 노트를 다시 읽어 페르소나, JTBD, 기본 분석 개념을 떠올리세요.
-   Collect recent user feedback or interview notes—you’ll need real voices to ground the exercises below.
-   최근 사용자 피드백이나 인터뷰 노트를 모아 실제 목소리를 기반으로 연습을 진행하세요.
-   Set aside a dedicated “strategy journal” where you log hypotheses, experiments, and leadership reflections.
-   가설, 실험, 리더십에 대한 생각을 기록할 “전략 저널”을 준비하세요.

## Level 2 Upgrade Goals
## 레벨 2 업그레이드 목표
1.  **Make product decisions data-informed** by pairing intuition with structured experiments.
1.  **데이터 기반 제품 의사결정**: 직관과 구조화된 실험을 결합합니다.
2.  **Prioritize ruthlessly** using frameworks that balance impact, confidence, and effort.
2.  **가차 없는 우선순위 결정**: 영향, 확신, 노력의 균형을 맞추는 프레임워크를 사용합니다.
3.  **Lead intentionally** by documenting decisions, communicating vision, and investing in others.
3.  **의도적인 리더십 발휘**: 의사결정을 문서화하고, 비전을 공유하며, 동료에 투자합니다.

## Core Concepts
## 핵심 개념

1.  **Product Management Mindset**: Understanding user needs, defining a product vision, and prioritizing what to build next.
1.  **제품 관리자 사고방식**: 사용자 니즈를 이해하고, 제품 비전을 정의하며, 다음에 만들 것을 우선순위화합니다.
2.  **Lean Startup Methodology**: A framework for building products under conditions of extreme uncertainty, emphasizing rapid iteration and validated learning.
2.  **린 스타트업 방법론**: 극도의 불확실성 속에서 빠른 반복과 검증된 학습을 강조하는 제품 개발 프레임워크입니다.
3.  **Data-Driven Decision Making**: Using metrics and experiments (A/B testing) to make objective decisions about the product.
3.  **데이터 기반 의사결정**: 지표와 실험(A/B 테스트)을 활용해 객관적인 제품 결정을 내립니다.
4.  **Technical Leadership**: The ability to influence, mentor, and guide a team to achieve technical excellence.
4.  **기술 리더십**: 팀의 기술적 탁월함을 이끌고 멘토링하며 영향력을 발휘하는 능력입니다.

---

## 1. The Product Management Mindset
## 1. 제품 관리자 사고방식

As a solo Vibe Coder, you are your own product manager.
솔로 Vibe Coder라면 스스로 제품 관리자 역할을 수행해야 합니다.

### "Jobs to be Done" (JTBD) Framework
### “Jobs to be Done”(JTBD) 프레임워크
-   **The Idea**: Customers don't "buy" products; they "hire" them to do a "job."
-   **개념**: 고객은 제품을 “구매”하는 것이 아니라 어떤 “일”을 하기 위해 “고용”합니다.
-   **Example**: You don't buy a drill because you want a drill. You buy it because you want a hole in your wall. The drill is hired for the job of "making a hole."
-   **예시**: 드릴을 사고 싶은 것이 아니라 벽에 구멍을 뚫고 싶어서 드릴을 “고용”하는 것입니다.
-   **Application**: Instead of thinking about features, think about the user's underlying need or goal. What "job" is your `druid_donum` crawler being hired for? Is it "save me time from manually checking websites," or is it "ensure I don't miss a critical business opportunity"? The framing changes how you think about the product.
-   **적용**: 기능보다 사용자 근본적 니즈와 목표를 생각하세요. `druid_donum` 크롤러는 “웹사이트 수동 확인 시간을 줄여줘”라는 일에 고용되나요, 아니면 “중요한 비즈니스 기회를 놓치지 않도록 해줘”라는 일에 고용되나요? 이런 관점이 제품에 대한 사고를 바꿉니다.

### Prioritization Frameworks
### 우선순위 결정 프레임워크
You will always have more ideas than you have time to build them. You need a system for deciding what to work on next.
아이디어는 항상 시간보다 많기 때문에, 무엇을 다음으로 만들지 결정할 시스템이 필요합니다.
-   **RICE Framework**:
-   **RICE 프레임워크**:
    -   **Reach**: How many users will this feature affect?
    -   **Reach**: 이 기능이 영향을 줄 사용자 수
    -   **Impact**: How much will this feature impact those users (on a scale of 1-3)?
    -   **Impact**: 사용자에게 미칠 영향(1~3 점수)
    -   **Confidence**: How confident are you in your estimates for Reach and Impact (on a scale of 0-1)?
    -   **Confidence**: Reach와 Impact 추정에 대한 확신도(0~1)
    -   **Effort**: How much engineering time will this take?
    -   **Effort**: 필요한 엔지니어링 시간
    -   **Score = (Reach * Impact * Confidence) / Effort**
    -   **점수** = (Reach × Impact × Confidence) / Effort
    -   This provides a simple, quantitative way to compare the relative value of different features.
    -   다양한 기능의 상대적 가치를 정량적으로 비교하는 간단한 방법입니다.

**Practice:** draft three feature ideas for your crawler, score them with RICE, and commit the results to your strategy journal. Revisit the scores after a week to see if new data shifts your priorities.
**실습:** 크롤러를 위한 기능 아이디어 세 가지를 작성하고 RICE 점수를 매긴 뒤 전략 저널에 기록하세요. 일주일 후 새로운 데이터를 반영해 우선순위가 바뀌는지 확인해 보세요.

---

## 2. The Lean Startup: Build-Measure-Learn
## 2. 린 스타트업: 제작-측정-학습

The core of the Lean Startup is the **Build-Measure-Learn feedback loop**.
린 스타트업의 핵심은 **제작-측정-학습** 피드백 루프입니다.

1.  **Ideas**: Start with a core hypothesis about your product (e.g., "I believe users will pay for a service that automatically notifies them of new bids from the IT department").
1.  **아이디어**: 제품에 대한 핵심 가설부터 시작합니다(예: “사용자가 IT 부서 새 입찰을 자동으로 알려주는 서비스에 비용을 지불할 것이다”).
2.  **Build (Minimum Viable Product - MVP)**: Build the *smallest possible thing* you can to test your hypothesis. This isn't your final product; it's an experiment. For the hypothesis above, an MVP might not even have a UI. It could be a simple script that emails you and a few beta testers.
2.  **제작(MVP)**: 가설을 검증하기 위한 *가장 작은 것*을 만듭니다. 최종 제품이 아니라 실험용입니다. 위 가설의 경우 UI 없이 몇몇 베타 테스터에게 이메일을 보내는 간단한 스크립트일 수도 있습니다.
3.  **Measure**: Define key metrics to measure the outcome of your experiment. Did users open the email? Did they click the link? Did they reply asking for more?
3.  **측정**: 실험 결과를 평가할 핵심 지표를 정의합니다. 사용자가 이메일을 열었나요? 링크를 클릭했나요? 더 많은 정보를 요청했나요?
4.  **Learn**: Analyze the data. Was your hypothesis correct?
4.  **학습**: 데이터를 분석해 가설이 맞았는지 확인합니다.
    -   If yes, **persevere**. Build the next feature to enhance the validated learning.
    -   맞았다면 **유지**하고, 검증된 학습을 강화할 다음 기능을 만듭니다.
    -   If no, **pivot**. Your core idea was wrong. Change your strategy based on what you learned. Maybe users don't care about notifications, but they would pay for a detailed analysis of past bids.
    -   틀렸다면 **피벗**하고 배운 것을 바탕으로 전략을 바꾸세요. 알림보다 과거 입찰 분석에 가치가 있을지도 모릅니다.

This loop forces you to confront reality early and often, preventing you from spending months building something nobody wants.
이 루프는 현실을 빠르고 자주 확인하게 만들어, 아무도 원하지 않는 것을 몇 달씩 개발하는 일을 막아줍니다.

### A/B Testing
### A/B 테스트
A/B testing is a powerful tool for making data-driven product decisions.
A/B 테스트는 데이터 기반 제품 의사결정을 위한 강력한 도구입니다.
-   **How it works**: You show two different versions of your product to two different groups of users (e.g., Group A sees a green "Sign Up" button, Group B sees a blue one).
-   **동작 방식**: 두 개의 다른 제품 버전을 사용자 그룹 두 개에 각각 보여줍니다(예: A그룹은 초록 버튼, B그룹은 파란 버튼).
-   **Measure**: You measure which version leads to a better outcome (e.g., a higher sign-up rate).
-   **측정**: 어떤 버전이 더 나은 결과(예: 가입률 상승)를 가져오는지 측정합니다.
-   **Application**: You can A/B test anything from button colors to pricing models to different recommendation algorithms. It replaces "I think" with "I know."
-   **적용**: 버튼 색상부터 가격 정책, 추천 알고리즘까지 A/B 테스트할 수 있습니다. “그럴 것 같다”를 “확실하다”로 바꿔줍니다.

**Practice:** run a tiny experiment—even if it’s manual. For example, send two versions of an update email to different friends and track responses. Record the hypothesis, metric, and outcome.
**실습:** 수동이라도 작은 실험을 해보세요. 업데이트 이메일 두 버전을 다른 친구에게 보내고 반응을 추적합니다. 가설, 지표, 결과를 기록하세요.

---

## 3. Technical Leadership
## 3. 기술 리더십

Even as a solo coder, you are leading yourself. As you grow, you may lead a team.
혼자 작업할 때도 스스로를 이끌어야 하며, 성장하면 팀을 이끌게 될지도 모릅니다.

### The Engineering Manager vs. The Tech Lead
### 엔지니어링 매니저 vs. 테크 리드
These are the two primary leadership tracks in many tech companies.
많은 기술 회사에서 두 가지 주요 리더십 트랙이 존재합니다.
-   **Engineering Manager**: Focuses on people and process. Responsible for hiring, career growth, team health, and project management. They ask "who" and "when."
-   **엔지니어링 매니저**: 사람과 프로세스에 집중하며 채용, 성장, 팀 건강, 프로젝트 관리를 책임지고 “누가”, “언제”를 묻습니다.
-   **Tech Lead (or Staff/Principal Engineer)**: Focuses on the technical aspects. Responsible for architecture, code quality, technical strategy, and mentoring other engineers. They ask "what" and "how."
-   **테크 리드(또는 스태프/프린시펄 엔지니어)**: 기술 측면에 집중하며 아키텍처, 코드 품질, 기술 전략, 멘토링을 담당하고 “무엇을”, “어떻게”를 묻습니다.
-   A Vibe Coder, especially when starting, must wear both hats.
-   Vibe Coder는 특히 초기에는 두 역할을 모두 수행해야 합니다.

### Qualities of a Tech Lead
### 테크 리드의 자질
-   **Technical Excellence**: You must be a strong technical contributor, but you don't have to be the "best" coder on the team.
-   **기술적 탁월성**: 팀에서 가장 뛰어난 코더일 필요는 없지만 강력한 기술 기여자여야 합니다.
-   **Vision**: You can see the long-term technical roadmap and guide the team toward it, making sure short-term decisions don't compromise long-term goals.
-   **비전**: 장기 기술 로드맵을 바라보고 단기 결정이 장기 목표를 해치지 않도록 팀을 이끕니다.
-   **Mentorship**: You find more satisfaction in helping others on your team succeed than in writing code yourself. You level up the entire team through code reviews, design discussions, and pairing.
-   **멘토링**: 직접 코드 작성보다 팀원을 성장시키는 데 더 큰 만족을 느끼며, 코드 리뷰, 설계 토론, 페어 작업으로 팀 전체를 성장시킵니다.
-   **Communication and Influence**: You can clearly articulate complex technical ideas to both technical and non-technical audiences. You build consensus and influence without relying on authority.
-   **커뮤니케이션과 영향력**: 복잡한 기술 아이디어를 기술자와 비기술자 모두에게 명확히 전달하고 권위가 아닌 설득으로 합의를 이끌어냅니다.
-   **Pragmatism**: You know when to pursue technical perfection and when to accept "good enough" to ship a feature. You balance technical debt against product velocity.
-   **실용주의**: 기술적 완벽을 추구해야 할 때와 “충분히 좋음”으로 기능을 출시해야 할 때를 구분해 기술 부채와 제품 속도를 균형 있게 맞춥니다.

Mastering this final level means you have the skills not just to build a great piece of software, but to build a great product and, eventually, a great team and a great business. It's the ultimate expression of the Vibe Coding philosophy: using technology as a lever to create meaningful impact in the world.
이 마지막 단계를 마스터한다는 것은 훌륭한 소프트웨어뿐 아니라 뛰어난 제품, 나아가 훌륭한 팀과 비즈니스를 만들 수 있는 역량을 갖췄다는 뜻입니다. 이것이 바로 기술을 레버로 삼아 세상에 의미 있는 임팩트를 만드는 Vibe Coding 철학의 정수입니다.

## Going Further
## 더 나아가기
-   Schedule a recurring “founder reflection” session where you review metrics, customer feedback, and team health.
-   지표, 고객 피드백, 팀 건강을 돌아보는 “창업자 회고” 세션을 정기적으로 마련하세요.
-   Shadow or interview a product manager/tech lead to compare how they prioritize and communicate.
-   제품 관리자나 테크 리드를 따라다니며 그들이 어떻게 우선순위를 정하고 소통하는지 비교해 보세요.
-   Read "Inspired" (Marty Cagan) or "The Manager’s Path" (Camille Fournier) and extract three ideas to test in your next sprint.
-   Marty Cagan의 『Inspired』나 Camille Fournier의 『The Manager’s Path』를 읽고 다음 스프린트에 시험해 볼 아이디어 세 가지를 뽑아보세요.
