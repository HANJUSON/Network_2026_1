# HFT 프로토콜 지연시간 벤치마크 - TCP vs UDP

컴퓨터 네트워크 Module 5 프로젝트 | Group 07

---

## 개요

이 프로젝트는 **고빈도 거래(HFT, High-Frequency Trading) 시뮬레이션 시스템**을 구현하여, 거래 환경에서 **TCP**와 **UDP** 프로토콜의 지연시간(latency) 성능을 측정하고 비교합니다. 제어된 조건에서 주문 처리의 왕복 지연시간(RTT)을 측정하여, 시간 기반 금융 애플리케이션에서 네트워크 프로토콜 선택을 위한 실증적 데이터를 제공합니다.

> **핵심 연구 질문**: 고빈도 거래 시스템에서 TCP와 UDP 중 어떤 프로토콜을 선택하는 것이 지연시간 성능에 더 큰 영향을 미치는가?

---

## 빠른 시작

### 방법 A — Docker (권장, 네트워크 분리 환경)

```bash
# 1. 이미지 빌드
docker compose build

# 2. 서버 시작
docker compose up server -d

# 3. 벤치마크 실행 (TCP + UDP 자동 비교)
docker compose run --rm client

# 4. 종료
docker compose down
```

결과 JSON은 `hft_client/results/`에 자동 저장됩니다.

### 방법 B — 로컬 직접 실행 (터미널 2개)

**터미널 1 — 서버:**
```bash
cd hft_server
python main_server.py
```

**터미널 2 — 클라이언트:**
```bash
cd hft_client
pip install -r requirements.txt
python main.py
```

---

## 웹 대시보드 (실시간 모니터링)

브라우저에서 TCP/UDP 지연시간, 처리량, 손실률을 실시간으로 확인할 수 있는 대시보드입니다.

### 1단계 — 이미지 빌드

```bash
docker compose build
```

### 2단계 — 서버 + 대시보드 시작

```bash
docker compose up server web -d
```

- `hft-server` 컨테이너: 10.10.0.2 에서 TCP/UDP 주문 수신
- `hft-web` 컨테이너: http://localhost:5000 에서 대시보드 제공

시작 확인:

```bash
docker logs hft-server    # "Listening on 0.0.0.0:8888" 확인
docker logs hft-web       # "Running on http://0.0.0.0:5000" 확인
```

### 3단계 — 브라우저 접속

http://localhost:5000

### 4단계 — 대시보드 설정 및 거래 시작

| 필드 | Docker 사용 시 | 로컬 직접 실행 시 |
|------|---------------|-----------------|
| Server Host | `10.10.0.2` | `127.0.0.1` |
| Port | `8888` | `8888` |
| Protocol | TCP 또는 UDP | TCP 또는 UDP |
| Orders / sec | 원하는 값 (예: 50) | 원하는 값 |
| Network Condition | tc netem 조건 메모 (예: `loss 1%`) | 비워두기 |

**▶ Start** 버튼을 클릭하면 거래가 시작되고 실시간 업데이트가 시작됩니다.

### 5단계 — 네트워크 조건 변경 (선택)

대시보드를 실행하는 동안 별도 터미널에서 서버 컨테이너에 tc netem 조건을 적용할 수 있습니다:

```bash
# 패킷 손실 1% 적용
docker exec hft-server tc qdisc add dev eth0 root netem loss 1%

# 고정 지연 1ms 적용
docker exec hft-server tc qdisc add dev eth0 root netem delay 1ms

# 조건 초기화
docker exec hft-server tc qdisc del dev eth0 root 2>/dev/null; true
```

Network Condition 입력란에 현재 적용한 조건을 입력하면 대시보드 헤더에 태그로 표시됩니다.

### 종료

```bash
docker compose down
```

### 대시보드 UI 설명

| 항목 | 설명 |
|------|------|
| Total Orders | 전송된 전체 주문 수 (Success / Lost 분리 표시) |
| Loss Rate | 타임아웃 주문 비율 (%) — 1% 초과 시 빨간색으로 강조 |
| Throughput | 현재 초당 처리 주문 수 (ops/sec) |
| P99 Latency | 99번째 백분위수 지연시간 — 1ms 초과 시 빨간색으로 강조 |
| Min / Mean / Median / P95 | 지연시간 분포 지표 |
| Latency Over Time | Mean(평균) vs P99 실시간 꺾은선 그래프 |
| Latency Distribution | 구간별 주문 수 막대 히스토그램 |
| Trade Log | 최근 100건 개별 주문 결과 (최대 20건/초 샘플링) |

### 색상 가이드

| 색상 | 의미 |
|------|------|
| 초록 (`#00ff88`) | 지연시간 300μs 미만 / BUY 주문 / 정상 |
| 노란색 (`#ffaa00`) | 지연시간 300μs–1ms 경고 구간 |
| 빨간색 (`#ff4757`) | 지연시간 1ms 초과 위험 / SELL / 손실(LOST) |
| 청록 (`#00d4ff`) | TCP 프로토콜 뱃지 / 일반 수치 |
| 주황 (`#ffaa00`) | UDP 프로토콜 뱃지 |

---

## 실측 결과

Docker 환경(컨테이너 간 bridge 네트워크)에서 1,000개 주문 기준으로 측정한 실제 결과입니다.

### Baseline (패킷 손실 없음)

| 지표 | TCP | UDP |
|------|-----|-----|
| Min | 109.9 μs | 110.3 μs |
| Mean | 188.6 μs | 178.0 μs |
| Median | 179.2 μs | 169.2 μs |
| P95 | 263.9 μs | 253.1 μs |
| P99 | 375.7 μs | 386.1 μs |
| Max | 795.0 μs | 830.7 μs |
| 수신 성공 | 1,000 / 1,000 | 1,000 / 1,000 |

→ 손실이 없는 환경에서는 TCP와 UDP의 차이가 미미합니다. (평균 차이 약 10μs)

### 패킷 손실 1% (tc netem `loss 1%` 적용)

| 지표 | TCP | UDP |
|------|-----|-----|
| Min | 117.8 μs | 102.9 μs |
| Mean | **2,306 μs** | **177.9 μs** |
| Median | 194.0 μs | 172.9 μs |
| P95 | 402.4 μs | 253.4 μs |
| P99 | **204,812 μs** | **374.5 μs** |
| Max | 212,968 μs | 559.9 μs |
| 수신 성공 | **1,000 / 1,000** (재전송) | **992 / 1,000** (8개 손실) |

→ 패킷 손실 1%만으로 TCP P99가 375μs → **204ms로 545배** 급등합니다.
  Linux 기본 TCP 재전송 타이머(RTO minimum 200ms)가 원인입니다.
  UDP는 손실된 8개를 포기하는 대신 나머지 992개의 지연시간은 손실 전과 동일하게 유지됩니다.

**이것이 HFT 시스템에서 프로토콜 선택이 중요한 이유입니다.**

---

## 프로젝트 구조

```
.
├── hft_server/
│   ├── main_server.py              # 서버 진입점
│   ├── Dockerfile                  # Docker 이미지 정의
│   ├── config/
│   │   └── server_settings.json    # 서버 설정
│   ├── src/
│   │   ├── __init__.py
│   │   ├── order_book.py           # 주문서 및 거래소 상태
│   │   ├── matcher.py              # 주문 체결 로직
│   │   └── handler.py              # 요청 처리 및 유효성 검사
│   └── requirements.txt
│
├── hft_client/
│   ├── main.py                     # 벤치마크 클라이언트 진입점
│   ├── web_server.py               # 웹 대시보드 서버
│   ├── Dockerfile                  # Docker 이미지 정의
│   ├── config/
│   │   ├── settings.json           # 클라이언트 설정 (로컬용)
│   │   └── settings.docker.json    # 클라이언트 설정 (Docker용)
│   ├── src/
│   │   ├── __init__.py
│   │   ├── protocol.py             # 주문 메시지 프로토콜
│   │   ├── client.py               # TCP/UDP 클라이언트 구현
│   │   ├── benchmark.py            # 지연시간 벤치마킹
│   │   └── utils.py                # 유틸리티 및 통계
│   ├── static/
│   │   ├── css/style.css           # 대시보드 스타일
│   │   └── js/app.js               # 대시보드 프론트엔드
│   ├── templates/
│   │   ├── trading.html            # 거래 대시보드
│   │   └── trading_dashboard.html
│   ├── results/                    # 벤치마크 결과 (JSON)
│   └── requirements.txt
│
├── scripts/
│   └── run_scenarios.sh            # 시나리오 자동 실행 스크립트
│
├── docker-compose.yml              # 컨테이너 구성
└── CN_Module5_MidpointReport_Group07.md  # 프로젝트 보고서
```

---

## 로컬 실행 상세

### 사전 요구사항

- Python 3.8 이상

### 서버 실행 옵션

```bash
cd hft_server

# 기본 모드 (TCP 8888 + UDP 8888 동시 수신)
python main_server.py

# 비동기 모드 (asyncio 기반, 고동시성)
python main_server.py --mode async

# 더미 모드 (인위적 지연 100~500μs 추가)
python main_server.py --dummy

# 포트 분리
python main_server.py --port 9999 --udp-port 9998
```

### 클라이언트 실행 옵션

```bash
cd hft_client
pip install -r requirements.txt

# TCP + UDP 비교 (기본)
python main.py

# 특정 프로토콜만
python main.py --protocol tcp
python main.py --protocol udp

# 파라미터 커스텀 (주문 5,000개, 50μs 간격, 워밍업 50개)
python main.py --orders 5000 --interval 50 --warmup 50
```

### 웹 대시보드 (로컬 직접 실행)

```bash
cd hft_client
pip install -r requirements.txt
python web_server.py
# 브라우저에서 http://127.0.0.1:5000 접속
# Server Host: 127.0.0.1, Port: 8888 로 설정 후 ▶ Start
```

Docker 환경에서 대시보드를 사용하는 방법은 위의 **웹 대시보드** 섹션을 참고하세요.

---

## Docker 분리 환경 벤치마크 상세

### 왜 Docker인가

로컬 loopback(`127.0.0.1`)은 OS 커널이 NIC와 네트워크 스택을 우회하므로, 측정값이 "프로토콜 차이"가 아닌 "파이썬 소켓 API 오버헤드"에 가깝습니다. Docker bridge 네트워크는 두 컨테이너가 별도의 가상 이더넷 인터페이스를 통해 통신하고, **tc netem**으로 지연·손실·지터를 수치로 제어할 수 있습니다.

### 아키텍처

```
[hft-client]  10.10.0.3
      │
      │  Docker bridge (10.10.0.0/24)
      │  ← tc netem이 서버 eth0 egress에 적용됨
      │
[hft-server]  10.10.0.2
```

### 사전 준비

- Docker Desktop (Windows 11: WSL2 백엔드 필요)
  https://www.docker.com/products/docker-desktop/

```bash
docker --version   # 설치 확인
```

### 이미지 빌드

```bash
docker compose build
```

### 서버 시작

```bash
docker compose up server -d
docker logs hft-server          # 서버 기동 확인
```

### 네트워크 조건 설정 (tc netem)

```bash
# 이전 조건 초기화 (새 조건 적용 전 항상 먼저 실행)
docker exec hft-server tc qdisc del dev eth0 root 2>/dev/null; true

# ── 시나리오 A: Baseline ───────────────────────────────────────
# (초기화 후 아무것도 적용하지 않음)

# ── 시나리오 B: 고정 지연 1ms ─────────────────────────────────
docker exec hft-server tc qdisc add dev eth0 root netem delay 1ms

# ── 시나리오 C: 지연 1ms + 지터 ±500μs ────────────────────────
docker exec hft-server tc qdisc add dev eth0 root netem delay 1ms 500us distribution normal

# ── 시나리오 D: 패킷 손실 1% ──────────────────────────────────
docker exec hft-server tc qdisc add dev eth0 root netem loss 1%

# ── 시나리오 E: 패킷 손실 5% ──────────────────────────────────
docker exec hft-server tc qdisc add dev eth0 root netem loss 5%

# ── 시나리오 F: 복합 (1ms 지연 + 0.5% 손실) ────────────────────
docker exec hft-server tc qdisc add dev eth0 root netem delay 1ms loss 0.5%

# 현재 적용 조건 확인
docker exec hft-server tc qdisc show dev eth0
```

### 벤치마크 실행

```bash
# TCP + UDP 비교 (기본, 10,000 주문)
docker compose run --rm client

# 주문 수 조정
docker compose run --rm client python main.py --config config/settings.docker.json --orders 5000

# 특정 프로토콜만
docker compose run --rm client python main.py --config config/settings.docker.json --protocol tcp
docker compose run --rm client python main.py --config config/settings.docker.json --protocol udp
```

결과 JSON은 호스트의 `hft_client/results/`에 자동 저장됩니다 (볼륨 마운트).

### 전체 시나리오 자동 실행

6개 시나리오(Baseline → 복합)를 순서대로 자동 실행합니다.

```bash
bash scripts/run_scenarios.sh
```

### 종료

```bash
docker compose down
```

### 시나리오별 예상 vs 실측 결과

| 시나리오 | 조건 | TCP 동작 | UDP 동작 |
|---------|------|---------|---------|
| Baseline | 없음 | ≈ UDP (평균 차이 ~10μs) | ≈ TCP |
| 고정 지연 | delay 1ms | RTT +1ms | RTT +1ms |
| 지터 | delay 1ms 500us | P99 상승, head-of-line blocking | P99 낮음, 주문별 독립 처리 |
| 손실 1% | loss 1% | **P99 204ms** (재전송 타이머), 손실 0% | P99 374μs, **손실 ~1%** |
| 손실 5% | loss 5% | P99 폭증 | 손실률 ~5% |
| 복합 | delay+loss | 누적 악화 | 손실률 증가, 지연은 낮음 |

---

## 설정 파일

### 서버 (`hft_server/config/server_settings.json`)

```json
{
    "server": {
        "host": "0.0.0.0",
        "port": 8888,
        "backlog": 100,
        "max_connections": 1000
    },
    "performance": {
        "tcp_nodelay": true,
        "so_reuseaddr": true,
        "buffer_size": 65536
    },
    "order_book": {
        "symbols": ["BTC-USD", "ETH-USD", "AAPL"],
        "max_order_size": 10000,
        "min_order_size": 1
    },
    "simulation": {
        "enabled": false,
        "min_latency_us": 100,
        "max_latency_us": 500
    }
}
```

### 클라이언트 로컬 (`hft_client/config/settings.json`)

```json
{
    "server": {
        "host": "127.0.0.1",
        "port": 8888,
        "protocol": "tcp"
    },
    "benchmark": {
        "warmup_orders": 100,
        "test_orders": 10000,
        "interval_us": 100,
        "save_results": true
    }
}
```

### 클라이언트 Docker (`hft_client/config/settings.docker.json`)

```json
{
    "server": {
        "host": "10.10.0.2",
        "port": 8888,
        "protocol": "tcp"
    },
    "client": {
        "tcp_nodelay": true,
        "socket_timeout_ms": 5000
    },
    "benchmark": {
        "warmup_orders": 100,
        "test_orders": 10000,
        "interval_us": 100,
        "save_results": true,
        "results_dir": "results"
    },
    "symbols": ["BTC-USD", "ETH-USD", "AAPL"]
}
```

---

## 프로토콜 비교 방법론

| 기능 | TCP | UDP |
|------|-----|-----|
| 신뢰성 | 보장됨 (재전송) | 최선 노력 |
| 순서 보장 | 보장됨 | 없음 |
| 혼잡 제어 | 있음 | 없음 |
| 연결 상태 | 필요 | 불필요 |
| 헤더 오버헤드 | 20+ 바이트 | 8 바이트 |
| 재전송 타이머 | 최소 200ms (Linux RTO) | 없음 |
| 구현 복잡도 | 낮음 | 높음 |

### 벤치마크 프로세스

1. **웜업 단계**: 100개 주문으로 캐시 및 커넥션 상태 안정화
2. **테스트 단계**: 100μs 간격으로 10,000개 주문 전송, 각 주문의 RTT를 `time.perf_counter_ns()`로 측정
3. **분석 단계**: 통계 계산 (평균, 중앙값, P95, P99, 표준편차)

### 수집 지표

- 평균(Mean), 중앙값(Median), P95, P99, P99.9
- 최소/최대 지연시간
- 표준편차
- 수신 성공률 (UDP 손실 감지)

---

## 주요 기능

### 서버 (hft_server)

- 멀티스레드 TCP / 단일스레드 UDP 동시 처리
- 가격-시간 우선순위 기반 주문서(Order Book) 관리
- 주문 체결 엔진 (시장가/지정가)
- 인위적 지연 설정 가능한 더미 모드 (`--dummy`)
- 다중 거래 심볼 지원 (BTC-USD, ETH-USD, AAPL)
- Python asyncio 기반 비동기 모드 (`--mode async`)

### 클라이언트 (hft_client)

- 자동화된 지연시간 벤치마킹 (TCP/UDP 비교)
- 웜업 및 테스트 주문 수 설정 가능
- 통계 분석 (평균, 중앙값, P95, P99, 표준편차)
- JSON 결과 로깅 (`hft_client/results/`)
- Flask-SocketIO 기반 실시간 웹 대시보드

---

## 사용 기술

- **Python 3** (서버: 표준 라이브러리만 사용)
- **Flask** + **Flask-SocketIO** (웹 대시보드)
- **소켓 프로그래밍** (TCP/UDP)
- **스레딩** & **asyncio** (동시성 처리)
- **Docker** + **tc netem** (네트워크 조건 제어)
- **JSON** (설정 및 결과 저장)

---

## 교과목 정보

- **교과목**: 컴퓨터 네트워크 (Computer Networks)
- **모듈**: Module 5 — 전송 계층 프로토콜
- **프로젝트**: 중간 보고서
- **팀**: Group 07
- **연도**: 2026

## 라이선스

이 프로젝트는 컴퓨터 네트워크 교과목의 교육 목적으로 제작되었습니다.

## 참고 문헌

1. RFC 793 — Transmission Control Protocol
2. RFC 768 — User Datagram Protocol
3. 고빈도 거래 관련 학술 문헌
4. 저지연 거래 시스템의 업계 모범 사례
