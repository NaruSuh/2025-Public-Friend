#!/bin/bash
# CLIK API 회의록 수집 실행 스크립트
# 백그라운드 실행 및 로그 관리

cd "$(dirname "$0")"

# 로그 디렉토리 확인
mkdir -p logs

# 현재 시간
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=============================================="
echo "CLIK API 회의록 수집 시작"
echo "시작 시간: $(date)"
echo "=============================================="

# 수집 실행 (nohup으로 백그라운드 실행)
if [ "$1" == "background" ]; then
    echo "백그라운드 실행..."
    nohup python3 fetch_all_minutes.py > logs/output_$TIMESTAMP.log 2>&1 &
    echo "PID: $!"
    echo "로그: logs/output_$TIMESTAMP.log"
    echo ""
    echo "진행 상황 확인: tail -f logs/output_$TIMESTAMP.log"
else
    # 포그라운드 실행
    python3 fetch_all_minutes.py "$@"
fi
