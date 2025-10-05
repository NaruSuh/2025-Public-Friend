# 개발자에서 테크 리드로: 기술 리더십의 시작

**대상 독자**: 시니어 개발자 또는 첫 리더 역할을 맡게 된 개발자
**선행 지식**: 3년 이상 개발 경험
**학습 시간**: 2-3시간

---

## 테크 리드란 무엇인가?

### 오해: "가장 코드 잘 짜는 사람"

```
❌ 잘못된 인식:
- 테크 리드 = 슈퍼 개발자
- 모든 코드를 내가 작성해야 함
- 가장 어려운 버그를 내가 해결해야 함
- 팀원보다 3배 빠르게 코딩해야 함

결과:
😰 밤 11시까지 코딩
😰 팀원은 할 일이 없음
😰 병목점이 바로 나
😰 번아웃
```

### 진실: "팀의 생산성을 극대화하는 사람"

```
✅ 올바른 인식:
- 나의 가치 = 나의 코드 × 1 + 팀원의 코드 × 10
- 팀이 올바른 방향으로 가도록 안내
- 장애물 제거 (기술 부채, 프로세스 병목)
- 기술 결정에 책임
- 팀원 성장 지원

결과:
✅ 팀 전체 생산성 3배 증가
✅ 팀원 성장
✅ 지속 가능한 속도
✅ 일과 삶의 균형
```

---

## 역할 전환의 어려움

### 개인 기여자 (IC) vs 테크 리드

| 측면 | IC (Individual Contributor) | 테크 리드 (Tech Lead) |
|------|---------------------------|---------------------|
| **성공 척도** | 내가 작성한 코드 | 팀이 달성한 목표 |
| **시간 사용** | 코딩 90% | 코딩 30%, 조율 40%, 리뷰 30% |
| **결정 방식** | 혼자 빠르게 | 팀과 함께 (느리지만 buy-in) |
| **책임** | 내 작업 | 팀 전체 결과 |
| **성장** | 기술 깊이 | 기술 + 리더십 |

### 흔한 실수

```python
# ❌ 실수 1: 모든 코드 직접 작성
def tech_lead_mindset_wrong():
    """테크 리드가 되었지만 여전히 IC처럼 행동"""

    # 새 기능 요청
    task = "Implement payment integration"

    # 혼자 다 함
    write_code(task)
    write_tests(task)
    write_documentation(task)

    # 팀원: "저희는 뭐 하죠?" 😐

# ✅ 올바른 접근
def tech_lead_mindset_right():
    """팀의 생산성을 극대화"""

    task = "Implement payment integration"

    # 1. 작업 분해 (Work Breakdown)
    subtasks = [
        "Research payment providers (Alice)",
        "Design API interface (Bob)",
        "Implement Stripe integration (Charlie)",
        "Write integration tests (myself)",
        "Documentation (Alice)"
    ]

    # 2. 명확한 인터페이스 정의 (가장 중요!)
    define_api_contract()  # 팀원이 병렬 작업 가능하도록

    # 3. 장애물 제거
    setup_stripe_test_account()
    get_security_approval()

    # 4. 진행 상황 추적 및 지원
    daily_standup()
    pair_with_charlie_on_tricky_part()

    # 결과: 5일 → 2일로 단축 (병렬 작업)
```

---

## 핵심 책임 1: 기술 비전 및 아키텍처

### 문제: 방향 없는 개발

```
팀원 A: "이건 React로 만들까요, Vue로 만들까요?"
팀원 B: "데이터베이스는 MongoDB? PostgreSQL?"
팀원 C: "마이크로서비스로 할까요?"

테크 리드가 없으면:
- 3일간 논쟁
- 각자 다른 기술 선택
- 아키텍처 일관성 없음
```

### 해결: Architecture Decision Record (ADR)

```markdown
# ✅ ADR-001: 데이터베이스 선택

**날짜**: 2025-10-06
**상태**: 승인됨
**결정자**: 테크 리드 + 팀

## 컨텍스트
e커머스 주문 시스템 구축 중. 트랜잭션 일관성과 복잡한 쿼리 필요.

## 고려한 옵션
1. **PostgreSQL** (관계형 DB)
   - 장점: ACID 보장, 복잡한 JOIN 쿼리, 성숙한 생태계
   - 단점: 수평 확장 어려움

2. **MongoDB** (문서 DB)
   - 장점: 유연한 스키마, 수평 확장 쉬움
   - 단점: 트랜잭션 제한적, 복잡한 쿼리 어려움

3. **DynamoDB** (NoSQL)
   - 장점: 무한 확장, 관리 불필요
   - 단점: 쿼리 제한적, 비용 높음

## 결정
**PostgreSQL을 선택한다.**

## 이유
1. 주문 시스템은 트랜잭션 일관성이 중요 (결제 - 재고 - 배송)
2. 복잡한 분석 쿼리 필요 (매출 리포트, 재고 관리)
3. 팀의 PostgreSQL 경험이 풍부
4. 초기에는 단일 서버로 충분 (확장은 나중에 Read Replica로)

## 결과
- 개발 시작일: 2025-10-07
- 재검토 예정일: 2026-01-01 (트래픽 증가 시)

## 참고 자료
- [PostgreSQL vs MongoDB 벤치마크](...)
- [주문 시스템 요구사항 문서](...)
```

**ADR의 가치**

```
✅ 팀 정렬: 모두가 같은 방향
✅ 시간 절약: 같은 논쟁 반복 안 함
✅ 신입 온보딩: "왜 이 기술?"에 대한 답
✅ 미래 참고: 6개월 후 "왜 PostgreSQL 선택했더라?"
```

---

## 핵심 책임 2: 코드 품질 관리

### 문제: 일관성 없는 코드

```python
# ❌ 팀원 A의 코드
def get_user(user_id):
    return db.query(f"SELECT * FROM users WHERE id={user_id}")  # SQL Injection!

# 팀원 B의 코드
def getUserById(userId):  # 네이밍 규칙 다름
    result = database.execute("SELECT * FROM users WHERE id=?", (userId,))
    return result.fetchone()

# 팀원 C의 코드
class UserRepository:  # 또 다른 패턴
    def find(self, id: int) -> Optional[User]:
        # ...
```

### 해결: 코딩 표준 및 자동화

**1. 코딩 가이드라인 작성**

```markdown
# ✅ Python Coding Standards (예제)

## 네이밍
- 함수: snake_case (`get_user`, `create_order`)
- 클래스: PascalCase (`UserRepository`, `OrderService`)
- 상수: UPPER_CASE (`MAX_RETRIES`, `API_KEY`)

## 패턴
### 데이터베이스 쿼리
항상 Parameterized Query 사용:

```python
# ✅ Good
cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))

# ❌ Bad
cursor.execute(f"SELECT * FROM users WHERE id={user_id}")
```

### 에러 처리
구체적 예외 처리:

```python
# ✅ Good
try:
    user = get_user(user_id)
except UserNotFoundError:
    return jsonify({'error': 'User not found'}), 404
except DatabaseError as e:
    logger.error(f"DB error: {e}")
    return jsonify({'error': 'Internal error'}), 500

# ❌ Bad
try:
    user = get_user(user_id)
except:  # 너무 광범위
    pass
```
```

**2. 자동화 (린터, 포매터)**

```yaml
# ✅ .pre-commit-config.yaml
repos:
  # 코드 포맷팅 (자동 수정)
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  # Import 정렬
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  # 린팅 (문제 감지)
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100']

  # 타입 체크
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy

# 설치: pre-commit install
# 이제 git commit 시 자동으로 검사!
```

**3. Pull Request 템플릿**

```markdown
# ✅ .github/pull_request_template.md

## 변경 사항
<!-- 무엇을 변경했는지 간략히 설명 -->

## 왜 필요한가?
<!-- 비즈니스 맥락, 해결하는 문제 -->

## 어떻게 테스트했는가?
- [ ] 유닛 테스트 추가
- [ ] 로컬에서 수동 테스트
- [ ] Staging 환경에서 검증

## 체크리스트
- [ ] 테스트 커버리지 80% 이상
- [ ] 문서 업데이트 (필요 시)
- [ ] Breaking Change 여부 확인
- [ ] 보안 취약점 확인

## 스크린샷 (UI 변경 시)
<!-- 전/후 비교 이미지 -->
```

---

## 핵심 책임 3: 팀원 성장 지원

### 1:1 미팅 (가장 중요!)

```markdown
# ✅ 1:1 Meeting Template (격주 30분)

**날짜**: 2025-10-06
**참석자**: 테크 리드 + Alice (주니어 개발자)

## 최근 성과 (먼저 칭찬!)
- 결제 API 통합 완료 (예상보다 빠름)
- 테스트 커버리지 85% 달성
- PR 리뷰에서 좋은 피드백

## 어려운 점 / 장애물
Alice: "비동기 프로그래밍이 아직 어렵습니다."

테크 리드 액션:
- [ ] asyncio 튜토리얼 공유
- [ ] 다음 스프린트에 비동기 작업 할당 (학습 기회)
- [ ] 페어 프로그래밍 1시간 예약

## 커리어 목표
Alice: "1년 내에 시니어 개발자가 되고 싶어요."

로드맵:
- Q4 2025: 복잡한 기능 리드 (결제 시스템 리팩터링)
- Q1 2026: 테크 토크 발표 (팀 내부)
- Q2 2026: 주니어 멘토링 시작
- Q3 2026: 시니어 승진 논의

## 다음 액션
- [ ] asyncio 학습 자료 전달 (테크 리드)
- [ ] 페어 프로그래밍 일정 잡기 (Alice)
- [ ] 결제 리팩터링 설계 문서 작성 (Alice, 리뷰: 테크 리드)
```

### 효과적인 코드 리뷰

```python
# ❌ 나쁜 코드 리뷰
"""
Comment: "이거 잘못됐어요. 고쳐주세요."

문제:
- 무엇이 잘못됐는지 불명확
- 왜 잘못됐는지 설명 없음
- 어떻게 고칠지 모름
→ 팀원 성장 없음, 좌절감만
"""

# ✅ 좋은 코드 리뷰
"""
Comment:
**이슈**: 이 코드는 SQL Injection 취약점이 있습니다.

**설명**: 사용자 입력(`user_id`)을 직접 쿼리에 삽입하면, 악의적 입력으로
데이터베이스를 조작할 수 있습니다.

**예시**:
만약 `user_id = "1 OR 1=1"`이면, 쿼리가 다음처럼 됩니다:
`SELECT * FROM users WHERE id=1 OR 1=1`
→ 모든 사용자 데이터 유출!

**해결책**:
Parameterized Query를 사용하세요:

```python
cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
```

**참고 자료**: [OWASP SQL Injection Guide](...)

**질문 있으면 언제든지 물어보세요!** 😊
"""

# 효과:
# ✅ 팀원이 '왜'를 이해
# ✅ 다음부터 같은 실수 안 함
# ✅ 보안 지식 향상
```

### 짝 프로그래밍 (Pair Programming)

```
상황: 주니어 개발자가 복잡한 알고리즘에 막힘

❌ 나쁜 접근:
테크 리드: "이리 줘봐, 내가 해줄게."
(30분 후) "자, 됐어. 다음에 이렇게 하면 돼."
→ 주니어: "...뭔지 모르겠지만 됐네요." (성장 없음)

✅ 좋은 접근 (Pair Programming):
테크 리드: "같이 풀어볼까? 네가 드라이버, 나는 네비게이터."

주니어 (코딩): "먼저 데이터를 정렬해야 할 것 같은데..."
테크 리드: "좋은 접근이야! 왜 정렬이 필요할까?"
주니어: "이분 탐색을 쓰려고요."
테크 리드: "맞아. 그럼 정렬 함수 작성해볼래?"

(함께 문제 해결)

→ 주니어: "이제 이해했어요! 다음엔 혼자 할 수 있을 것 같아요."
```

---

## 핵심 책임 4: 이해관계자 관리

### 문제: 비현실적 기대

```
PM: "이번 주까지 AI 추천 기능 완성 가능하죠?"
테크 리드 (신입): "네... 노력해볼게요."

(2주 후)
PM: "왜 안 됐어요?"
테크 리드: "생각보다 복잡했어요..."
PM: (신뢰 하락)

문제:
- 비현실적 약속
- 기술 복잡도 설명 못함
- 일정 투명성 없음
```

### 해결: 투명한 커뮤니케이션

```markdown
# ✅ 기능 요청 대응 템플릿

**PM 요청**: "AI 추천 기능을 2주 안에 만들어주세요."

**테크 리드 응답**:

## 범위 명확화
먼저 "AI 추천"의 정의를 명확히 하겠습니다:

**옵션 1: 간단한 규칙 기반 추천** (2주)
- 사용자가 본 상품 카테고리 기반
- "이 상품을 본 사람들이 본 다른 상품"
- 정확도: 60-70%

**옵션 2: 협업 필터링** (6주)
- 유사 사용자 패턴 분석
- 개인화된 추천
- 정확도: 75-85%
- 필요: 데이터 파이프라인 구축, 모델 학습

**옵션 3: 딥러닝 기반** (3개월)
- 최신 추천 알고리즘
- 실시간 학습
- 정확도: 85-90%+
- 필요: ML 엔지니어 추가, GPU 인프라

## 제안
**옵션 1로 시작하는 것을 권장합니다.**

**이유**:
1. 빠르게 출시 가능 (2주)
2. 사용자 반응 측정 가능
3. 나중에 옵션 2/3로 업그레이드 가능

**Trade-off**:
- 정확도는 낮지만 80%의 가치를 20%의 노력으로
- 조기 피드백으로 방향 조정 가능

**다음 단계**:
PM과 비즈니스 우선순위 논의 → 옵션 결정 → 개발 시작

---

결과:
✅ PM이 옵션을 이해하고 현실적 선택
✅ 기대치 관리됨
✅ 신뢰 구축
```

### 진행 상황 보고

```markdown
# ✅ 주간 진행 보고 (Stakeholders에게)

**프로젝트**: 결제 시스템 리뉴얼
**기간**: 2025-10-01 ~ 2025-10-06 (Week 2/8)

## 완료된 것 ✅
- Stripe API 통합 완료 (Alice)
- 테스트 환경 구축 (Bob)
- 보안 검토 통과 (Security Team)

## 진행 중 🔄
- 환불 로직 구현 (Charlie, 50% 완료)
- PG사 연동 테스트 (Alice, 진행 중)

## 다음 주 계획 📅
- 환불 로직 완료 (Charlie)
- End-to-End 테스트 (전체 팀)
- 문서화 (Alice)

## 리스크 & 이슈 ⚠️
**이슈**: PG사 API 문서가 불완전하여 연동 지연
**영향**: 1주 지연 가능
**대응**:
- PG사 기술 지원 미팅 예약 (10/07)
- 대안 PG사 검토 시작

**일정**: 여전히 8주 안에 완료 가능 (버퍼 2주 있음)

---

효과:
✅ Stakeholder가 진행 상황 파악
✅ 문제 조기 발견
✅ 투명성으로 신뢰 구축
```

---

## 핵심 책임 5: 기술 부채 관리

### 문제: "나중에 고치자"의 악순환

```python
# ❌ 기술 부채 누적
# 3개월 전
def calculate_price(item):
    # TODO: 할인 로직 리팩터링 필요
    return item.price * 0.9  # 임시 하드코딩

# 2개월 전
def calculate_shipping(order):
    # FIXME: 지역별 배송비 DB로 관리해야 함
    if order.region == "Seoul":
        return 3000
    elif order.region == "Busan":
        return 5000
    # ... 30개 지역 하드코딩

# 1개월 전
def process_payment(order):
    # XXX: 에러 처리 추가 필요
    charge_card(order.total)  # 실패 시 롤백 로직 없음

# 현재
PM: "새 결제 수단 추가해주세요."
테크 리드: "...이 코드베이스는 손댈 수가 없는데요?" 😱
```

### 해결: 체계적 기술 부채 관리

**1. 기술 부채 가시화**

```markdown
# ✅ TECH_DEBT.md

## Critical (즉시 해결 필요)
### 1. 결제 시스템 에러 처리 없음
- **파일**: `payment/processor.py:45`
- **문제**: 결제 실패 시 롤백 로직 없음 → 중복 결제 가능
- **영향**: 고객 불만, 매출 손실
- **예상 시간**: 2일
- **담당**: Charlie
- **기한**: 2025-10-10

## High (다음 스프린트)
### 2. 배송비 계산 로직 하드코딩
- **파일**: `shipping/calculator.py:120-150`
- **문제**: 30개 지역 if-else 하드코딩
- **영향**: 새 지역 추가 시마다 배포 필요
- **해결책**: DB 테이블로 이동
- **예상 시간**: 3일
- **담당**: Alice
- **기한**: 2025-10-20

## Medium (다음 분기)
### 3. 할인 로직 리팩터링
- **파일**: `pricing/calculator.py:30`
- **문제**: 할인 규칙이 코드에 하드코딩
- **영향**: 마케팅 캠페인 유연성 부족
- **해결책**: Rule Engine 도입
- **예상 시간**: 1주
- **기한**: 2025-12-31
```

**2. 보이스카우트 규칙 (Boy Scout Rule)**

```python
# ✅ "코드를 처음 발견했을 때보다 깨끗하게 남겨라"

@app.route('/orders/<int:order_id>')
def get_order(order_id):
    # 기존 코드 (레거시)
    order = db.execute(f"SELECT * FROM orders WHERE id={order_id}").fetchone()

    # 보이스카우트 규칙 적용: 발견한 문제 개선
    # SQL Injection 취약점 수정
    order = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()

    # 추가: 에러 처리
    if not order:
        return jsonify({'error': 'Not found'}), 404

    return jsonify(order)

# 작은 개선이 쌓여서 코드베이스 전체가 개선됨
```

**3. 20% 시간 할당**

```
스프린트 계획:
- 새 기능 개발: 80% (4일)
- 기술 부채 해결: 20% (1일)

효과:
- 기술 부채가 관리 가능한 수준 유지
- 개발 속도 장기적으로 유지 (부채 누적 시 속도 저하 방지)
```

---

## 테크 리드의 일과

### 나쁜 예: 모든 걸 혼자

```
09:00 - 코딩 (긴급 버그 수정)
10:00 - 코딩 (새 기능 개발)
11:00 - 회의 (PM과 요구사항 논의)
12:00 - 점심
13:00 - 코딩 (API 통합)
14:00 - 코드 리뷰 (쌓인 10개 PR)
15:00 - 코딩 (테스트 작성)
16:00 - 회의 (아키텍처 논의)
17:00 - 코딩 (리팩터링)
18:00 - 팀원 질문 응대
19:00 - 코딩 (못 끝낸 작업)
21:00 - 퇴근

결과: 번아웃, 팀 병목점
```

### 좋은 예: 시간 블록 활용

```
09:00-09:30 ✅ 팀 스탠드업
  - 각자 진행 상황 공유
  - 장애물 확인 및 해결

09:30-11:30 💻 집중 코딩 시간 (방해 금지)
  - Slack 알림 끔
  - 가장 중요한 작업 1개 완료

11:30-12:30 🍱 점심 + 비공식 대화
  - 팀 빌딩
  - 캐주얼 기술 토론

12:30-14:00 👀 코드 리뷰 & 페어 프로그래밍
  - 매일 2-3개 PR 리뷰
  - 주니어와 30분 페어링

14:00-15:00 📋 계획 & 설계
  - 다음 스프린트 준비
  - 아키텍처 문서 작성

15:00-16:00 🤝 1:1 미팅 (격일)
  - 팀원 성장 지원
  - 경력 개발 논의

16:00-17:00 💻 코딩 또는 기술 부채 해결

17:00-18:00 📊 문서화 & 정리
  - ADR 작성
  - 주간 보고 준비

18:00 ✅ 퇴근

결과: 지속 가능, 팀 생산성 극대화
```

---

## 성공 측정 지표

### 나쁜 지표: 개인 생산성

```
❌ 잘못된 KPI:
- 내가 작성한 코드 줄 수
- 내가 해결한 버그 수
- 내가 만든 기능 수

문제: 테크 리드가 코딩만 하면 팀은?
```

### 좋은 지표: 팀 생산성

```
✅ 올바른 KPI:

1. **팀 배포 빈도**
   - 목표: 주 5회 → 하루 3회
   - 측정: CI/CD 배포 로그

2. **Lead Time** (코드 작성 → 프로덕션)
   - 목표: 2주 → 2일
   - 측정: JIRA 티켓 생명주기

3. **변경 실패율**
   - 목표: 30% → 5%
   - 측정: 롤백 횟수 / 배포 횟수

4. **팀원 성장**
   - 목표: 주니어 1명 → 미드 레벨 승진 (6개월)
   - 측정: 1:1 미팅, 역량 평가

5. **기술 부채 해결**
   - 목표: Critical 부채 0건 유지
   - 측정: TECH_DEBT.md 추적

6. **팀 만족도**
   - 목표: 4.5/5.0 이상
   - 측정: 분기별 익명 설문
```

---

## 체크리스트: 좋은 테크 리드인가?

### 팀 역량
- [ ] 팀원이 나 없이도 대부분 작업을 완료할 수 있는가?
- [ ] 내가 휴가 가도 팀이 정상 운영되는가?
- [ ] 지난 분기 대비 팀 배포 속도가 빨라졌는가?

### 의사소통
- [ ] 모든 주요 기술 결정이 문서화되어 있는가? (ADR)
- [ ] 팀원 모두가 아키텍처를 이해하는가?
- [ ] Stakeholder가 진행 상황을 투명하게 아는가?

### 팀원 성장
- [ ] 모든 팀원과 격주 1:1 미팅을 하는가?
- [ ] 팀원 각자의 성장 계획이 있는가?
- [ ] 지난 6개월간 팀원 중 누군가 승진했는가?

### 기술 품질
- [ ] 코드 리뷰가 24시간 내에 완료되는가?
- [ ] 기술 부채가 관리되고 있는가?
- [ ] 테스트 커버리지가 80% 이상인가?

### 일과 삶의 균형
- [ ] 주 50시간 이내로 일하는가?
- [ ] 주말에 긴급 대응이 월 1회 이하인가?
- [ ] 번아웃 증상이 없는가?

---

## 다음 단계

1. **Engineering Manager**: 사람 관리 전문
2. **Staff Engineer**: 기술 전문성 심화
3. **CTO**: 조직 전체 기술 전략

---

## 참고 자료

- **책**: "The Manager's Path" by Camille Fournier
- **책**: "An Elegant Puzzle: Systems of Engineering Management" by Will Larson
- **블로그**: [Rands in Repose](https://randsinrepose.com/)
- **도구**: [Architecture Decision Records](https://adr.github.io/)
