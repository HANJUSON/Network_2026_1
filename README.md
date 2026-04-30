# HFT 프로토콜 지연시간 벤치마크 - TCP vs UDP

컴퓨터 네트워크 Module 5 프로젝트 | Group 07

## 개요

이 프로젝트는 **고빈도 거래(HFT, High-Frequency Trading) 시뮬레이션 시스템**을 구현하여, 거래 환경에서 **TCP**와 **UDP** 프로토콜의 지연시간(latency) 성능을 측정하고 비교합니다. 제어된 조건에서 주문 처리의 종단간 지연시간을 측정하여, 시간 기반 금융 애플리케이션에서 네트워크 프로토콜 선택을 위한 실증적 데이터를 제공합니다.

## 주요 연구 질문

> **고빈도 거래 시스템에서 TCP와 UDP 중 어떤 프로토콜을 선택하는 것이 지연시간 성능에 더 큰 영향을 미치는가?**

## 주요 기능

### 서버 (hft_server)
- 멀티스레드 TCP/UDP 서버 구현
- 가격-시간 우선순위 기반 주문서(Order Book) 관리
- 주문 체결 엔진 (시장가/지정가 주문)
- 인위적 지연시간 설정 가능한 시뮬레이션 모드
- 다중 거래 심볼 지원 (BTC-USD, ETH-USD, AAPL, GOOGL, MSFT)
- 실시간 처리 통계 (평균, p99, 최소/최대 지연시간)
- Python asyncio를 활용한 비동기 모드 지원

### 클라이언트 (hft_client)
- 자동화된 지연시간 벤치마킹
- TCP 및 UDP 프로토콜 테스트
- 웜업 및 테스트 주문 수 설정 가능
- 통계 분석 (평균, 중앙값, p95, p99, 표준편차)
- JSON 결과 로깅
- **실시간 시각화를 제공하는 웹 기반 거래 대시보드**
- Flask-SocketIO를 통한 WebSocket 지원

## 프로젝트 구조

```
.
├── hft_server/
│   ├── main_server.py              # 서버 진입점
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
│   ├── config/
│   │   └── settings.json           # 클라이언트 설정
│   ├── src/
│   │   ├── __init__.py
│   │   ├── protocol.py             # 주문 메시지 프로토콜
│   │   ├── client.py               # TCP/UDP 클라이언트 구현
│   │   ├── benchmark.py            # 지연시간 벤치마킹
│   │   └── utils.py                # 유틸리티 및 통계
│   ├── static/
│   │   ├── css/style.css          # 대시보드 스타일
│   │   └── js/app.js              # 대시보드 프론트엔드
│   ├── templates/
│   │   ├── trading.html           # 거래 대시보드
│   │   └── trading_dashboard.html
│   ├── results/                    # 벤치마크 결과 (JSON)
│   └── requirements.txt
│
└── CN_Module5_MidpointReport_Group07.md  # 프로젝트 보고서
```

## 설치 방법

### 사전 요구사항
- Python 3.8 이상

### 서버 설정
```bash
cd hft_server
# 외부 의존성 없음 (표준 라이브러리만 사용)
python main_server.py
```

### 클라이언트 설정
```bash
cd hft_client
pip install -r requirements.txt
```

## 사용법

### 1. 서버 실행

**기본 모드 (TCP + UDP):**
```bash
cd hft_server
python main_server.py
```

**비동기 모드 (고동시성 환경):**
```bash
python main_server.py --mode async
```

**더미/시뮬레이션 모드 (인위적 지연시간 추가):**
```bash
python main_server.py --dummy
```

**커스텀 포트 설정:**
```bash
python main_server.py --port 9999 --udp-port 9998
```

### 2. 지연시간 벤치마크 실행

**두 프로토콜 비교:**
```bash
cd hft_client
python main.py
```

**특정 프로토콜 테스트:**
```bash
python main.py --protocol tcp
python main.py --protocol udp
```

**벤치마크 매개변수 커스텀:**
```bash
python main.py --orders 5000 --interval 50 --warmup 50
```

### 3. 웹 대시보드 실행

```bash
cd hft_client
python web_server.py
```

브라우저에서 접속: http://127.0.0.1:5000

대시보드 기능:
- 실시간 주문 전송
- 실시간 지연시간 시각화
- 프로토콜 비교 (TCP vs UDP)
- 주문 통계 확인

## 설정

### 서버 설정 (`hft_server/config/server_settings.json`)

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

### 클라이언트 설정 (`hft_client/config/settings.json`)

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

## 프로토콜 비교 방법론

| 기능 | TCP | UDP |
|------|-----|-----|
| 신뢰성 | 보장됨 | 최선 노력 |
| 순서 보장 | 보장됨 | 없음 |
| 혼잡 제어 | 있음 | 없음 |
| 연결 상태 | 필요 | 불필요 |
| 헤더 오버헤드 | 20+ 바이트 | 8 바이트 |
| 지연시간 잠재력 | 더 높음 | 더 낮음 |
| 구현 복잡도 | 단순함 | 복잡함 |

### 벤치마크 프로세스
1. **웜업 단계**: 시스템 상태 안정을 위해 100개 주문 전송
2. **테스트 단계**: 마이크로초 단위 간격으로 10,000개 주문 전송
3. **분석 단계**: 통계 계산 (평균, 중앙값, p95, p99)

### 수집 지표
- 평균, 중앙값, p95, p99 지연시간
- 최소 및 최대 지연시간
- 표준편차
- 성공/실패율

## 예상 결과

프로토콜 특성에 따른 예상 결과:
- **UDP**는 일반적으로 더 낮은 평균 지연시간을 보임 (연결 오버헤드 없음, 작은 헤더)
- **TCP**는 더 일관된 지연시간을 제공 (내장된 혼잡 제어)
- 고부하 상황에서는 성능이 수렴될 수 있음

## 사용 기술

- **Python 3** (서버 표준 라이브러리)
- **Flask** + **Flask-SocketIO** (웹 대시보드)
- **소켓 프로그래밍** (TCP/UDP)
- **스레딩** & **Asyncio** (동시성 처리)
- **JSON** (설정 및 결과 저장)

## 교과목 정보

- **교과목**: 컴퓨터 네트워크 (Computer Networks)
- **모듈**: Module 5 - 전송 계층 프로토콜
- **프로젝트**: 중간 보고서
- **팀**: Group 07
- **연도**: 2026

## 결과

벤치마크 결과는 `hft_client/results/` 디렉토리에 타임스탬프와 함께 JSON 파일로 저장됩니다:
```
benchmark_20260410_223722.json
benchmark_20260407_150628.json
...
```

## 라이선스

이 프로젝트는 컴퓨터 네트워크 교과목의 교육 목적으로 제작되었습니다.

## 참고 문헌

1. RFC 793 - Transmission Control Protocol
2. RFC 768 - User Datagram Protocol
3. 고빈도 거래 관련 학술 문헌
4. 저지연 거래 시스템의 업계 모범 사례
