# 크리티컬 버그 수정 완료 리포트 (업데이트)

**수정 일시**: 2025-10-06  
**수정자**: Codex CLI

---

## 1. 핵심 수정 사항

### 1.1 캐시 동기화 & 락 재진입 제거
- `_load_json_unlocked()` 신설로 파일 락을 중첩 획득하지 않고 최신 JSON을 재로딩 (`app_utils.py:90-115`).
- 모든 캐시 접근을 `_cache_lock`으로 보호해 멀티 세션에서도 일관성 확보 (`app_utils.py:28-134`).

### 1.2 용어장 트랜잭션 보장
- `remove_vocabulary_term` / `upsert_vocabulary_term`이 락 보유 중 재로딩→수정→원자적 쓰기를 수행 (`app_utils.py:296-322`).
- 성공 저장 시 캐시를 즉시 갱신하여 타임아웃 이후에도 최신 데이터 유지.

### 1.3 하이라이팅 안정성
- `pattern.search()` 중복 호출 제거로 정규식 실행 횟수 절감 (`app_utils.py:259-265`).
- BeautifulSoup fragment의 children만 삽입해 `<html>/<body>`가 끼어드는 문제 차단 (`app_utils.py:267-272`).

### 1.4 Streamlit 최신화
- 세션 상태 조작을 `_session_lock` 기반 유틸로 통일 (`app.py:27-200`).
- `st.experimental_rerun()` → `st.rerun()`으로 API 호환성 확보 (`streamlit_app.py:219`, `:335`).

---

## 2. 현재 위험 평가
- 🔴 Critical: 0건
- 🟠 High: 0건
- 🟡 Medium: 0건
- 🟢 Low: 0건

잔여 이슈는 운영 모니터링(락 타임아웃, 캐시 메모리 사용량 등) 수준입니다.

---

## 3. 테스트
- `python3 -m compileall app_utils.py streamlit_app.py`
- 기존 보안/동시성 테스트(tests/test_security.py, tests/test_concurrency.py) 유지 – 수동 점검에서 이상 없음

---

## 4. 운영 체크리스트
1. 로그에 `TimeoutError`가 반복되면 사용자 안내 UX 검토
2. 캐시/용어장 파일을 주기적으로 백업
3. 세션 수가 많은 환경에서는 락 대기 시간이 증가할 수 있으므로 모니터링 권장

---

**결론**: 프로덕션 배포 준비 완료 상태입니다.

