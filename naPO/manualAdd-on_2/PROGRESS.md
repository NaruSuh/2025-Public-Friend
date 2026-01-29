# CLIK API 회의록 수집 진행 기록

## 프로젝트 개요
- **목적**: 전국 지방의회 회의록 전체 수집
- **데이터 소스**: CLIK Open API (국회지방의회의정포털)
- **API 키**: `REDACTED_CLIK_API_KEY`

## 수집 대상
| API | 항목 | 건수 | 상태 |
|-----|------|------|------|
| minutes.do | 회의록 | 827,210건 | 수집중 |
| bill.do | 의안정보 | 435,978건 | 미시작 |
| assemblyinfo.do | 의원정보 | 2,160건 | 미시작 |
| policyinfoList.do | 정책정보 | 85,954건 | 미시작 |

## 진행 상황

### 2024-12-29 (시작일)
- 14:31 - 수집 시작 (백그라운드)
- 15:32 - 965건 수집 완료, 108개 의회
- 예상 소요: 약 27-31일
- 2025-12-29 15:44 - 965건 수집 (0.1%), 108개 의회, 266.5MB
- 2025-12-29 15:45 - 965건 수집 (0.1%), 108개 의회, 266.5MB
- 2025-12-29 16:42 - 965건 수집 (0.1%), 108개 의회, 266.5MB
- 2025-12-29 17:40 - 965건 수집 (0.1%), 108개 의회, 266.5MB
- 2025-12-29 18:37 - 965건 수집 (0.1%), 108개 의회, 266.5MB

## 주요 파일
```
manualAdd-on_2/
├── config.py           # API 설정
├── api_client.py       # API 클라이언트
├── fetch_all_minutes.py # 수집 메인 스크립트
├── check_status.py     # 진행 확인
├── run_collector.sh    # 실행 스크립트
├── data/
│   ├── progress.json       # 진행 상황 (자동 저장)
│   └── collected_docids.txt # 수집된 DOCID 목록
├── output/minutes/     # 수집 결과 (의회별 .jsonl)
├── docs/
│   └── clik_api_spec.yaml  # 4대 API 명세서
└── logs/               # 로그 파일
```

## 명령어

### 진행 상황 확인
```bash
cd /home/naru/dev/Labgod/apps/naPO/manualAdd-on_2
python3 check_status.py
```

### 프로세스 확인
```bash
ps aux | grep fetch_all_minutes
```

### 실시간 로그
```bash
tail -f logs/output_*.log
```

### 중단 후 재시작
```bash
# 자동으로 마지막 위치에서 재시작
python3 fetch_all_minutes.py

# 또는 백그라운드로
./run_collector.sh background
```

### 처음부터 다시
```bash
python3 fetch_all_minutes.py --reset
```

## 예상 용량
- 전체: ~212GB (827,210건 × 270KB 평균)
- 일일 수집량: ~7GB (27,000건)

## 특이사항
- searchKeyword 필수: 빈값 불가, "회의" 사용시 전체 조회
- 중단해도 progress.json에서 이어서 재시작 가능
- RASMBLY_ID 체계: XXX(지역코드) + YYY(의회번호)

## TODO (추후)
- [ ] 회의록 수집 완료
- [ ] 누락 필드 재수집 (RASMBLY_NUMPR, ORGINL_FILE_URL)
- [ ] 의안정보 수집
- [ ] 의원정보 수집
- [ ] 정책정보 수집

---
*마지막 업데이트: 2025-12-29 18:37*
