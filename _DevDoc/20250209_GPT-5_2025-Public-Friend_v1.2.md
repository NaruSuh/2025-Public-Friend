# 2025-Public-Friend 코드 감사 보고서 (2025-02-09, GPT-5, v1.2)

## 범위·방법·한계
- 리포지토리: `2025-Public-Friend`
- 포함: `Appducator`, `ConferenceChasor`, `druid_donum/druid_full_auto`, `naPO`, `slava_talk`, `tools` 스크립트.
- 방법: 주요 엔트리포인트와 보안/설정 파일을 정적 스팟 점검. 전체 테스트 실행이나 모든 파일의 동적 검증은 포함하지 않음. 서술은 “관찰 기준”이며, 발견되지 않은 위험이 남아있을 수 있음.
- 심각도 표기: [H]=High, [M]=Medium, [L]=Low

## 프로젝트별 상세 진단 및 실천 항목

### Appducator
- [M] 감사/버그 문서 분산(`CRITICAL_BUGS_FOUND.md`, `Appducator_Code_Audit.md` 등) → 최신 상태 파악 어려움.
  - 조치: 단일 `STATUS.md`/`CHANGELOG.md`로 이관하고, 원본 문서에는 이관 일자·링크 명시.
- [M] CI/테스트 가시성 부족(루트에 CI 워크플로 확인되지 않음). 테스트 폴더는 존재하나 자동 실행 여부 불명.
  - 조치: CI에서 `pytest` + 커버리지 실행 후 배지로 README 노출. `requirements-dev.txt` 사용하도록 워크플로 추가.

### ConferenceChasor
- [H] 업로드 인증/제한 없음 (`ConferenceChasor/app.py`): 누구나 파일 업로드·ZIP 생성 가능, 크기/확장자 제한 없음.
  - 조치: 최소 토큰/베이직 인증, `MAX_CONTENT_LENGTH` 설정, 허용 확장자/용량(예: 5MB) 화이트리스트, CSRF 보호 적용. 업로드 파일 MIME 검사 후만 처리.
- [M] 사용자에게 예외 메시지 노출 (`error = f"...{exc}"`). 운영 시 내부 정보 누출 가능.
  - 조치: 사용자 메시지 일반화, 상세 스택은 서버 로그로만 남기기. `DEBUG=False` 확인.
- [M] 임시 디렉터리 ZIP 포함 범위 무제한.
  - 조치: 생성된 PDF만 포함하도록 경로 화이트리스트.

### druid_donum / druid_full_auto
- [M] 감사/개선 문서가 다수(`AUDIT_REPORT.md`, `IMPROVEMENTS_v1.1.0.md`, `VIBE_GROWTH_PLAN.md`)로 분산.
  - 조치: `CURRENT_STATUS.md` 또는 `CHANGELOG.md`에 최신·미해결 항목 통합. 과거 문서는 보관용으로만 유지.
- [M] CI/테스트 불명확(`tests`, `requirements-dev.txt`는 있으나 워크플로 미확인).
  - 조치: CI에 `pytest`와 린터(ruff/flake8) 추가, 실패 시 머지 차단.

### naPO
- [H] Dev 로그인 허용: `apps/backend/src/api/routes/auth.routes.ts`에서 dev/test 모드에 임의 자격 증명 허용, prod는 501 응답.
  - 조치: 운영 빌드에서 dev 로그인 비활성화(환경 분기 강제) 또는 OAuth/OIDC로 대체, 관리자 엔드포인트에 인증 미들웨어 추가.
- [H] 암호화 키 기본값: `apps/backend/src/lib/encryption.ts`에서 `ENCRYPTION_KEY` 미설정 시 개발용 키 사용.
  - 조치: 키 미설정 시 부팅 실패하도록 변경, 키 회전 절차·재암호화 스크립트 제공.
- [M] API 키 메타 노출 가능: `/sources/apis`에 인증 미적용 상태(코드상 별도 미들웨어 없음). 실제 키는 마스킹되지만 메타(라벨/만료) 노출 우려.
  - 조치: 인증/권한 미들웨어 추가(admin 전용), 필요 시 응답 필드 축소.
- [M] 미구현 인텐트: `query.routes.ts`에서 `parse_pdf` 미구현, R-ONE NLP TODO.
  - 조치: API에서 400/501 명시 및 UI/문서에 제한 표시. 백로그 일정 확정.
- [M] 기능 플래그 기본 ON: `.env.example`에서 NL_QUERY/OCR/CRAWLING 모두 true, 소스별 세분 rate-limit 없음(전역 `/api` 제한 외).
  - 조치: 운영 샘플 기본 OFF 후 필요 기능만 활성화. 소스/사용자별 rate-limit 추가 검토.

### slava_talk
- [H] 인증·접근통제 근거 미확인(Streamlit 앱, 관련 설정/문서 없음).
  - 조치: 비밀번호/토큰 보호 또는 SSO 프록시 적용. 파일/텍스트 입력 길이·타입 제한.
- [L] `slava_talk_debugging_plan.md`와 실제 조치 간 연결 부재.
  - 조치: 이슈 트래커와 연동, 완료 시 체크리스트 업데이트.

### tools 스크립트
- [M] 비밀 처리 불명확(`tools/batch_update_examples.py`, `openai_responses_diagnose.py` 등): 키 로딩·로깅 방식 명시 안 됨.
  - 조치: 환경변수만 사용하도록 표준화, 로그에 키 마스킹. 실행 예시(.env 샘플) 문서화.

## 공통 권고(우선순위)
1) 인증/권한: 외부 노출 가능 앱(ConferenceChasor, naPO, slava_talk)에 인증·업로드 제한·CSRF 방어 적용.
2) 비밀 관리: `ENCRYPTION_KEY` 필수화, API 키 메타/로그 마스킹, 툴은 환경변수만 사용. 키 회전 가이드 작성.
3) CI/테스트: 모든 프로젝트에 테스트·린트 CI 추가, 커버리지/품질 배지로 가시화.
4) 문서 통합: 분산된 감사/개선 문서를 STATUS/CHANGELOG로 단일화해 최신 상태만 유지.
5) 기능 제한 명시: naPO 미구현 인텐트, ConferenceChasor 업로드 정책, slava_talk 접근 정책을 README/FAQ에 명확히 표기.

## 부록: 실행 및 운영 리스크
- naPO Auto Debug Collector: 기본 3~4 prompts/min(라이브러리/스크립트), Gemini 10/min 내 동작. `--cleanup`는 `test_temp` 전체 삭제이므로 경로 주의, 외부 API 비용·키 유출 주의.
- ConferenceChasor: 배포 전 `MAX_CONTENT_LENGTH`, 확장자 화이트리스트, CSRF 보호, 인증 없이는 서비스 불가.
- 전 프로젝트 공통: 운영에서 DEBUG/개발 모드 비활성화 확인, 로그에 비밀값 필터 적용.
