#!/bin/bash
# TCP vs UDP 시나리오별 자동 벤치마크 실행 스크립트
# 사용법: bash scripts/run_scenarios.sh

set -e

RESULTS_DIR="hft_client/results"
mkdir -p "$RESULTS_DIR"

echo "========================================"
echo " HFT Benchmark - 시나리오 자동 실행"
echo "========================================"

echo ""
echo "[1/6] 컨테이너 빌드..."
docker compose build

echo ""
echo "[2/6] 서버 시작..."
docker compose up server -d
echo "서버 준비 대기 (3초)..."
sleep 3

run_scenario() {
    local name=$1
    local tc_cmd=$2

    echo ""
    echo "========================================"
    echo " 시나리오: $name"
    echo "========================================"

    # 이전 tc 조건 초기화
    docker exec hft-server tc qdisc del dev eth0 root 2>/dev/null || true

    if [ -n "$tc_cmd" ]; then
        docker exec hft-server sh -c "$tc_cmd"
        echo "네트워크 조건 적용: $tc_cmd"
    else
        echo "네트워크 조건: 없음 (baseline)"
    fi

    # 시나리오 이름을 파일명에 반영하기 위해 결과 디렉토리에 마커 파일 생성
    echo "$name" > "$RESULTS_DIR/.current_scenario"

    docker compose run --rm client python main.py \
        --config config/settings.docker.json \
        --orders 5000

    echo "시나리오 '$name' 완료."
}

# ── 시나리오 목록 ────────────────────────────────────────────
run_scenario "1_baseline"        ""
run_scenario "2_delay_1ms"       "tc qdisc add dev eth0 root netem delay 1ms"
run_scenario "3_delay_jitter"    "tc qdisc add dev eth0 root netem delay 1ms 500us distribution normal"
run_scenario "4_loss_1pct"       "tc qdisc add dev eth0 root netem loss 1%"
run_scenario "5_loss_5pct"       "tc qdisc add dev eth0 root netem loss 5%"
run_scenario "6_combined"        "tc qdisc add dev eth0 root netem delay 1ms loss 0.5%"
# ─────────────────────────────────────────────────────────────

echo ""
echo "========================================"
echo " 전체 시나리오 완료"
echo " 결과 파일: $RESULTS_DIR/"
echo "========================================"

docker compose down
