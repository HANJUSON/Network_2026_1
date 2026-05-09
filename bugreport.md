# Bug Report — HFT Protocol Latency Benchmark

> 분석 일자: 2026-05-08  
> 대상: `hft_server/`, `hft_client/`, `docker-compose.yml`, `scripts/`

---

## 🔴 Critical

### C1. 이중 체결 (Double-fill) — `hft_server/src/handler.py:164-181`

`_execute_order()`가 `OrderMatcher`의 `match_market_order()` / `match_limit_order()`를 호출한 후, 이미 `fill()`이 완료된 주문들에 대해 **한 번 더 `fill()`을 호출**합니다. 결과적으로 `filled_qty`가 실제 체결량의 2배로 기록됩니다.

**경로:**
1. `matcher.py:59-60` (또는 `match_market_order`/`match_limit_order` 내부)에서 `best_bid.fill()`, `best_ask.fill()`, `order.fill()` 실행
2. `handler.py:175-181`에서 동일한 `buy_order`/`sell_order`에 대해 `fill()` 재호출

```python
# handler.py:175-181 (제거되어야 할 코드)
for trade in trades:
    buy_order = self.exchange.get_order(trade.buy_order_id)
    sell_order = self.exchange.get_order(trade.sell_order_id)
    if buy_order:
        buy_order.fill(trade.quantity, trade.price)   # 이미 fill 완료
    if sell_order:
        sell_order.fill(trade.quantity, trade.price)  # 이미 fill 완료
```

**영향:** 모든 체결의 `filled_qty`가 2배로 기록됨. `is_fully_filled()`가 조기에 true를 반환하여 미체결 주문이 예상보다 빨리 제거됨.

---

### C2. TCP 응답 부분 읽기 — `hft_client/src/client.py:52`

`HFTClientTCP.send_order()`가 `self.sock.recv(1024)`로 응답을 읽습니다. TCP는 스트림 프로토콜이므로:
- 서버 응답이 1024바이트를 초과하면 잘림 (`handler.py`의 `buffer_size`는 65536)
- 단일 `recv()`로 메시지 경계를 보장할 수 없음 (TCP 조각화 시 여러 번 읽어야 함)

```python
# client.py:52
response_data = self.sock.recv(1024)  # 65536바이트 응답이면 손실 발생
```

**영향:** 지연시간 측정 자체는 RTT 측정이므로 데이터 내용에는 영향이 없으나, 응답 파싱이 추가될 경우 심각한 오류 발생 가능. 큰 `message` 필드가 포함된 응답에서도 잘림 가능.

---

### C3. Async 모드에서 UDP 미구현 — `hft_server/main_server.py:268-281`

`AsyncHFTPServer`는 `asyncio.start_server()`로 **TCP만 처리**합니다. UDP 수신 로직이 아예 구현되어 있지 않습니다.

```python
class AsyncHFTPServer:
    def __init__(self, config: dict):
        # ...
        self.udp_port = config["server"].get("udp_port", config["server"]["port"])  # 저장만 하고 사용 안 함

    async def start(self):
        self.server = await asyncio.start_server(
            self.handle_tcp_client, self.host, self.tcp_port  # TCP만 처리
        )
```

**영향:** `--mode async` 실행 시 UDP로 전송된 모든 주문이 유실됩니다.

---

### C4. `asyncio.run()` 중복 호출 — `hft_server/main_server.py:344-345`

이미 실행 중인 이벤트 루프가 있을 때 `asyncio.run()`을 다시 호출하면 `RuntimeError`가 발생합니다.

```python
# main_server.py:342-345
try:
    asyncio.run(server.start())
except KeyboardInterrupt:
    asyncio.run(server.stop())  # RuntimeError!
```

**수정 방안:** `server.start()` 내부에서 `try/except KeyboardInterrupt`로 `stop()`을 호출하거나, `asyncio.run()`에서 반환된 후 별도 처리.

---

## 🟠 Moderate

### M1. TCP 클라이언트 타임아웃 미처리 — `hft_client/src/client.py:47-55`

`HFTClientUDP.send_order()`는 `socket.timeout`을 잡아 `-1`을 반환하지만, `HFTClientTCP.send_order()`는 예외를 그대로 전파합니다.

```python
# UDP (정상 처리)
except socket.timeout:
    return -1

# TCP (미처리 — 예외 전파)
response_data = self.sock.recv(1024)  # timeout 발생 시 예외
```

**영향:** TCP 벤치마크에서 타임아웃 발생 시 `benchmark.py`의 `except Exception as e: latencies.append(-1)`로 잡히긴 하나, 불필요한 스택 트레이스 출력과 일관성 없는 동작.

---

### M2. `AsyncHFTPServer`에 `TCP_NODELAY` 누락 — `hft_server/main_server.py:236-266`

동기 `HFTPServer`는 각 TCP 연결에 `TCP_NODELAY`를 설정하지만(`main_server.py:103-104`), `AsyncHFTPServer`는 설정하지 않습니다.

```python
# HFTPServer (설정함)
if self.tcp_nodelay:
    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

# AsyncHFTPServer (설정 안 함) — Nagle 알고리즘 활성화 상태
```

**영향:** async 모드에서 작은 주문 메시지들이 Nagle 알고리즘에 의해 버퍼링되어 지연시간 증가.

---

### M3. `ResultLogger.print_summary()` 통계 0 출력 — `hft_client/src/utils.py:157-158`

`__dict__.update(result['stats'])`로 복원 시 `latencies` 리스트가 복원되지 않아 모든 property(`min_ns`, `max_ns`, `mean_ns` 등)가 0을 반환합니다. (Python의 `property` descriptor가 instance dict보다 우선하기 때문)

```python
stats = LatencyStats([])                 # self.latencies = []
stats.__dict__.update(result['stats'])   # latencies는 dict에 없음 → 그대로 []
print(stats.summary())                   # 모두 0 출력
```

**영향:** `print_summary()` 호출 시 무의미한 출력. 디버깅/결과 확인 불가.

---

### M4. `accept()` 블로킹으로 종료 불가 — `hft_server/main_server.py:89`

TCP listening socket에 timeout이 설정되지 않아 `accept()`가 영원히 블로킹됩니다. Windows에서는 `KeyboardInterrupt`가 `accept()`를 중단시키지 못할 수 있습니다.

```python
self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# settimeout() 미설정 — accept() 블로킹
self.tcp_socket.bind(...)
self.tcp_socket.listen(self.backlog)  # ← backlog가 100으로 낮음

# UDP는 timeout 있음
self.udp_socket.settimeout(0.1)
```

**영향:** Ctrl+C로 서버 종료가 안 될 수 있음. `docker stop` 등 외부 수단 필요.

---

### M5. `processing_times` 스레드 경합 — `hft_server/handler.py:141`, `main_server.py:107-111`

여러 TCP 핸들러 스레드가 동기화 없이 하나의 `self.handler.processing_times` 리스트에 `append()`합니다.

```python
# handler.py:141
self.processing_times.append(processing_time)  # 여러 스레드가 동시 접근

# handler.py:194-207 — get_stats()에서 sort() 중 append() 시 비정합
sorted_times = sorted(self.processing_times)
```

**영향:** `get_stats()` 호출 시 리스트가 정렬되는 도중 append되면 `IndexError` 또는 잘못된 통계 출력 가능.

---

## 🟢 Minor

| # | 파일 | 라인 | 문제 | 설명 |
|---|------|------|------|------|
| m1 | `order_book.py` | 82, 87 | Side-effect mutation | `add_bid()`/`add_ask()`가 인자로 받은 `order.side`를 강제로 변경 (`order.side = OrderSide.BUY`). 호출자에 의도치 않은 영향. |
| m2 | `handler.py` | 65-77 | 구분자 미이스케이프 | `serialize()`가 `|`로 필드를 연결. `message`에 `|` 포함 시 `deserialize()`의 `split('|')`이 잘못 파싱함. |
| m3 | `utils.py` | 157 | 취약한 복원 패턴 | `__dict__.update()`로 인스턴스 복원하는 방식은 클래스 필드와 충돌 가능. `@classmethod` 팩토리 메서드 권장. |
| m4 | `matcher.py` | 10-20 | 데드 코드 | `match_orders()` 메서드가 어디서도 호출되지 않음. `match_market_order()`와 `match_limit_order()`만 사용됨. |
| m5 | `trading_dashboard.html` | 전체 | 미사용 템플릿 | `web_server.py`는 `trading.html`만 사용. `trading_dashboard.html`의 JS는 `price_update`, `signal_update`, `status_update` 이벤트를 구독하지만 서버에서 절대 emit하지 않음. 완전한 데드 코드. |
| m6 | `client.py` | 1 | 비관용적 import | `socket = __import__('socket')`는 `import socket`보다 가독성이 낮고 일반적이지 않음. |
| m7 | `server_settings.json` | 15, 27, 20-21 | 미사용 설정 | `order_book.price_precision`, `simulation.drop_rate`, `logging.*` 필드가 코드에서 전혀 참조되지 않음. |
| m8 | `web_server.py` | 21 | 하드코딩된 secret key | `app.config['SECRET_KEY'] = 'hft-trading-secret'`. 로컬 데모이나 보안 관행상 환경변수 권장. |
| m9 | `benchmark.py` | 134-155 | Logger 누적 | `run_comparison()`이 두 프로토콜을 순차 실행할 때 `self.logger`를 초기화하지 않아 결과가 누적됨. JSON에 두 결과가 모두 저장되는 것은 설계 의도일 수 있으나 명시적이지 않음. |
| m10 | `main.py` | 83 | Logger 경로 설정 방식 | `benchmark.logger.results_dir`을 생성 후 직접 변경. logger가 이미 기본 `results_dir="results"`로 초기화되어 있어 생성자 인자로 전달하는 것이 일관적. |
| m11 | `web_server.py` | 141 | 고정 심볼 목록 | `_run()`에서 5개 심볼 하드코딩. 설정 파일과 불일치 시 서버에서 Reject 가능. |
| m12 | `Dockerfile` (server) | 3-4 | 비효율적 레이어 | `apt-get update`와 `install`이 분리되지 않아 캐시 무효화 발생 시 불필요한 재다운로드. |
| m13 | `docker-compose.yml` | 2-41 | 웹 컨테이너 cap_add 누락 | (의도적일 수 있으나) 웹 컨테이너도 네트워크 진단이 필요하면 `NET_ADMIN`이 필요할 수 있음. |

---

## 📋 요약

| 심각도 | 개수 |
|--------|------|
| 🔴 Critical | 4 |
| 🟠 Moderate | 5 |
| 🟢 Minor | 13 |
| **합계** | **22** |

### 최우선 수정 권장 사항

1. **C1 (이중 체결)**: `handler.py:175-181`의 두 번째 `fill()` 루프를 제거 — matcher가 이미 fill을 수행함
2. **C3 (async UDP)**: `AsyncHFTPServer`에 UDP 핸들러 추가, 또는 async 모드 진입 시 경고 출력
3. **C4 (asyncio.run)**: `server.start()` 내에서 KeyboardInterrupt 처리
4. **M2 (TCP_NODELAY)**: `AsyncHFTPServer.handle_tcp_client()`에 `TCP_NODELAY` 설정 추가

---

*Report generated by code analysis.*
