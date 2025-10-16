# Critical Bug Review (2025-10-06 – 재평가)

**검토 일시**: 2025-10-06  
**검토자**: Codex CLI (재검증)

---

## 1. Executive Summary
- 🔴 **Critical (P0)**: 0건
- 🟠 **High (P1)**: 0건
- 🟡 **Medium (P2)**: 0건
- 🟢 **Low (P3)**: 0건

이전 감사(Claude)가 보고한 Race Condition·데이터 손실·Streamlit 세션 충돌 등 치명적 이슈는 모두 코드에 반영되어 해결되었습니다. 현재 코드베이스에서는 프로덕션 차단급 버그가 확인되지 않았습니다.

---

## 2. 재검증 요약

| 이전 이슈 | 재검증 결과 | 근거 |
|-----------|-------------|------|
| 캐시 `_json_cache` Race Condition | ✅ 해결 | `app_utils.py:34-109`에서 `threading.Lock`으로 모든 캐시 read/write 보호 |
| `save_vocabulary` 타임아웃 데이터 손실 | ✅ 해결 | 타임아웃 시 캐시 보존 및 `TimeoutError` 발생 (`app_utils.py:117-134`) |
| Streamlit 세션 상태 경쟁 | ✅ 해결 | `app.py:27-101`에서 `_session_lock` 기반 헬퍼 도입, 모든 state mutate가 락으로 감싸짐 |
| 용어장 read-modify-write 충돌 | ✅ 해결 | 락 보유 중 `_load_json_unlocked`로 최신 데이터 재로딩 (`app_utils.py:298-322`) |
| `highlight_terms` 과도한 정규식 호출 | ✅ 해결 | `pattern.sub`만 호출하도록 정리 (`app_utils.py:259-265`) |
| `BeautifulSoup.replace_with` Fragment 삽입 | ✅ 해결 | 파싱된 fragment의 children만 삽입 (`app_utils.py:267-272`) |
| `st.experimental_rerun` deprecated | ✅ 해결 | `streamlit_app.py:219`, `:335`에서 `st.rerun()` 사용 |

---

## 3. 권장 모니터링 항목 (참고)
- **Lock 타임아웃 로그**: `save_vocabulary`가 `TimeoutError`를 던지면 사용자 알림 UX가 필요할 수 있음.
- **캐시 메모리 사용량**: 장기 실행 시 `_json_cache` 범위 확인 (현재는 glossary/vocabulary 두 파일만 관리).
- **Streamlit 세션 컨텐션**: 동시에 많은 세션에서 용어장을 수정할 경우 추가 대기 시간이 발생할 수 있으므로 운영 환경에서 모니터링 권장.

---

## 4. 결론
현 시점에서 프로덕션 차단급 버그는 존재하지 않습니다. 상기 모니터링 포인트를 주기적으로 점검하면서 차후 요구사항(예: DB 백엔드 도입, LRU 캐시 등)을 계획적으로 진행하면 됩니다.

