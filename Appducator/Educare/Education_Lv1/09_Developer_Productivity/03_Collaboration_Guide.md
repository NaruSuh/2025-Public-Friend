# 09.03 - Vibe Coding Collaboration Guide
# 09.03 - Vibe Coding 협업 가이드

Vibe Coding isn't just about individual productivity; it's about elevating the entire team. A high-vibe team communicates effectively, maintains high standards, and moves quickly and safely. This guide covers the "soft skills" and processes that make this possible.
Vibe Coding은 단순히 개인의 생산성에 관한 것이 아닙니다. 팀 전체를 향상시키는 것입니다. 높은 분위기의 팀은 효과적으로 소통하고, 높은 기준을 유지하며, 빠르고 안전하게 움직입니다. 이 가이드는 이를 가능하게 하는 "소프트 스킬"과 프로세스를 다룹니다.

## Core Principles
## 핵심 원칙

1.  **Psychological Safety**: Team members must feel safe to ask questions, admit mistakes, and propose new ideas without fear of blame. This is the bedrock of a high-performing team.
    **심리적 안정감**: 팀원들은 비난에 대한 두려움 없이 질문하고, 실수를 인정하고, 새로운 아이디어를 제안할 수 있어야 합니다. 이것이 고성과 팀의 기반입니다.
2.  **Clear Communication**: Be concise, clear, and asynchronous-first. Respect others' focus time.
    **명확한 의사소통**: 간결하고 명확하며 비동기 우선으로 소통하세요. 다른 사람의 집중 시간을 존중하세요.
3.  **Ownership and Accountability**: Take ownership of your work from start to finish. If you see a problem, you own it until it's resolved or delegated.
    **주인의식과 책임감**: 처음부터 끝까지 자신의 작업에 대한 주인의식을 가지세요. 문제를 발견하면 해결되거나 위임될 때까지 당신의 책임입니다.
4.  **High-Quality Code Reviews**: Treat code reviews as a learning opportunity, not a gatekeeping exercise. The goal is to improve the code, not to criticize the author.
    **고품질 코드 리뷰**: 코드 리뷰를 문지기 역할이 아닌 학습 기회로 여기세요. 목표는 저자를 비판하는 것이 아니라 코드를 개선하는 것입니다.
5.  **Continuous Improvement**: Regularly reflect on and improve your team's processes.
    **지속적인 개선**: 정기적으로 팀의 프로세스를 되돌아보고 개선하세요.

---

## 1. Asynchronous-First Communication
## 1. 비동기 우선 커뮤니케이션

Your most valuable resource is focused time. Constant interruptions from synchronous chat messages destroy productivity.
가장 귀중한 자원은 집중된 시간입니다. 동기식 채팅 메시지로 인한 지속적인 방해는 생산성을 파괴합니다.

-   **Use Tools Intentionally**:
    **의도적으로 도구 사용**:
    -   **Asynchronous (Default)**: Use tools like GitHub Issues, Pull Requests, and project management boards (e.g., Linear, Jira) for discussions that need thought and documentation.
        **비동기(기본값)**: 생각과 문서화가 필요한 토론에는 GitHub Issues, Pull Requests 및 프로젝트 관리 보드(예: Linear, Jira)와 같은 도구를 사용하세요.
    -   **Synchronous (For Urgency/High-Bandwidth)**: Use chat (Slack, Teams) for urgent issues blocking work, or a quick huddle/call for complex discussions that are faster in real-time. After a call, summarize the outcome in a written, asynchronous format.
        **동기(긴급/고대역폭용)**: 작업을 차단하는 긴급한 문제에는 채팅(Slack, Teams)을 사용하거나 실시간으로 더 빠른 복잡한 토론을 위해 빠른 허들/통화를 사용하세요. 통화 후에는 결과를 서면, 비동기 형식으로 요약하세요.
-   **Write Good Messages**:
    **좋은 메시지 작성**:
    -   Provide all necessary context upfront (links, code snippets, error messages).
        필요한 모든 컨텍스트(링크, 코드 스니펫, 오류 메시지)를 미리 제공하세요.
    -   Clearly state the problem or question.
        문제나 질문을 명확하게 기술하세요.
    -   State what you've already tried.
        이미 시도한 것을 명시하세요.
    -   **Bad**: "Hey, is the server down?"
        **나쁜 예**: "저기요, 서버 다운됐나요?"
    -   **Good**: "Hey @team, I'm getting a 502 error when trying to access the `/api/v1/users` endpoint on staging. I've already checked the server status page and my local connection seems fine. Can anyone else confirm?"
        **좋은 예**: "안녕하세요 @team, 스테이징에서 `/api/v1/users` 엔드포인트에 액세스하려고 할 때 502 오류가 발생합니다. 서버 상태 페이지를 이미 확인했고 제 로컬 연결은 괜찮아 보입니다. 다른 분도 확인할 수 있나요?"

---

## 2. The Art of the Code Review
## 2. 코드 리뷰의 기술

A Vibe Coder's code review is empathetic, constructive, and efficient.
Vibe 코더의 코드 리뷰는 공감적이고 건설적이며 효율적입니다.

### For the Author
### 작성자를 위해

1.  **Prepare Your PR**:
    **PR 준비**:
    -   Your PR is not a draft. It should be work you consider complete and ready to merge.
        PR은 초안이 아닙니다. 완료되어 병합할 준비가 되었다고 생각하는 작업이어야 합니다.
    -   Write a clear description explaining the "why" and "what." Include screenshots or GIFs for UI changes.
        "왜"와 "무엇을"을 설명하는 명확한 설명을 작성하세요. UI 변경 사항에 대한 스크린샷이나 GIF를 포함하세요.
    -   Link to the relevant issue or ticket.
        관련 이슈나 티켓에 링크하세요.
    -   **Self-Review First**: Read through your own code one last time. You'll often catch your own mistakes.
        **먼저 자체 검토**: 자신의 코드를 마지막으로 한 번 더 읽어보세요. 종종 자신의 실수를 발견하게 될 것입니다.
2.  **Respond to Comments Gracefully**:
    **댓글에 우아하게 응답하기**:
    -   Assume good intent. The reviewer is trying to help you and the project.
        좋은 의도를 가정하세요. 리뷰어는 당신과 프로젝트를 돕기 위해 노력하고 있습니다.
    -   Don't be defensive. If something is unclear, it's an opportunity to improve your code's clarity.
        방어적으로 행동하지 마세요. 불분명한 것이 있다면 코드의 명확성을 향상시킬 수 있는 기회입니다.
    -   If you disagree, explain your reasoning calmly. A quick call can resolve lengthy back-and-forth debates.
        동의하지 않으면 차분하게 이유를 설명하세요. 빠른 통화로 길고 긴 논쟁을 해결할 수 있습니다.

### For the Reviewer
### 리뷰어를 위해

1.  **Understand the Goal**: Read the PR description and understand the purpose of the change before diving into the code.
    **목표 이해**: 코드를 살펴보기 전에 PR 설명을 읽고 변경 목적을 이해하세요.
2.  **Be Kind and Constructive**:
    **친절하고 건설적으로**:
    -   Frame feedback as suggestions or questions, not commands.
        피드백을 명령이 아닌 제안이나 질문으로 구성하세요.
    -   **Bad**: "Fix this. This is wrong."
        **나쁜 예**: "이거 고쳐요. 틀렸어요."
    -   **Good**: "What do you think about extracting this logic into a helper function? It seems like it might be reusable here."
        **좋은 예**: "이 로직을 헬퍼 함수로 추출하는 것에 대해 어떻게 생각하세요? 여기서 재사용할 수 있을 것 같습니다."
    -   Use emojis to convey tone. A simple `👍` or `😊` can make feedback feel more positive.
        이모티콘을 사용하여 톤을 전달하세요. 간단한 `👍` 또는 `😊`는 피드백을 더 긍정적으로 느끼게 할 수 있습니다.
3.  **Balance High-Level and Low-Level Feedback**:
    **높은 수준과 낮은 수준의 피드백 균형**:
    -   **High-Level**: Does this change make sense? Is the overall approach correct? Are there architectural concerns?
        **높은 수준**: 이 변경이 타당한가요? 전반적인 접근 방식이 올바른가요? 아키텍처 문제가 있나요?
    -   **Low-Level**: Nitpicks about style (should be automated by a linter/formatter), variable names, or small logic errors.
        **낮은 수준**: 스타일에 대한 잔소리(린터/포맷터로 자동화되어야 함), 변수 이름 또는 작은 논리 오류.
    -   Prefix comments with `nit:` for minor, non-blocking suggestions.
        사소하고 차단되지 않는 제안에 대해서는 주석 앞에 `nit:`를 붙이세요.
4.  **Be Timely**: Unblocking your teammates is a high priority. Aim to review PRs within a few hours. If you can't, let the author know when you'll be able to.
    **시기 적절하게**: 팀원의 막힌 작업을 풀어주는 것은 높은 우선순위입니다. 몇 시간 내에 PR을 검토하는 것을 목표로 하세요. 할 수 없다면 저자에게 언제 할 수 있는지 알려주세요.
5.  **Approve or Request Changes**: Be clear about the outcome. If changes are needed, state clearly what is required to get to an approval. If it's good to go, approve it! Don't leave the author in limbo.
    **승인 또는 변경 요청**: 결과에 대해 명확하게 하세요. 변경이 필요한 경우 승인을 받기 위해 무엇이 필요한지 명확하게 명시하세요. 괜찮다면 승인하세요! 저자를 불확실한 상태로 두지 마세요.

---

## 3. Running Effective Meetings (When You Must)
## 3. 효과적인 회의 진행 (필요할 때)

-   **Have a Clear Agenda and Goal**: Every meeting invitation must have a stated purpose and a list of topics. If there's no agenda, decline the meeting.
    **명확한 의제와 목표 설정**: 모든 회의 초대장에는 명시된 목적과 주제 목록이 있어야 합니다. 의제가 없으면 회의를 거절하세요.
-   **Invite Only the Necessary People**: Respect people's time.
    **필요한 사람만 초대**: 사람들의 시간을 존중하세요.
-   **Timebox Everything**: Stick to the schedule.
    **모든 것에 시간 제한 설정**: 일정을 지키세요.
-   **End with Clear Action Items**: Every meeting should end with a summary of who is responsible for what, and by when. Document this and share it.
    **명확한 실행 항목으로 마무리**: 모든 회의는 누가 무엇을 언제까지 책임지는지에 대한 요약으로 끝나야 합니다. 이를 문서화하고 공유하세요.

By adopting these collaborative practices, your team can build a "vibe" of trust, efficiency, and mutual respect. This creates a positive feedback loop where high-quality work happens naturally, and developers feel motivated and empowered.
이러한 협업 관행을 채택함으로써 팀은 신뢰, 효율성 및 상호 존중의 "분위기"를 구축할 수 있습니다. 이것은 고품질 작업이 자연스럽게 이루어지고 개발자가 동기를 부여받고 권한을 부여받는 긍정적인 피드백 루프를 만듭니다.