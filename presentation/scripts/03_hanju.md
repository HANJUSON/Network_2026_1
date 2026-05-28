# 손한주 — Part 3: Empirical Validation (TCP vs UDP Benchmark)

> **담당 슬라이드:** 14 – 19
> **목표 시간:** 약 4분 00초
> **약 560 단어** · 분당 약 140 wpm 기준
>
> **차별 포인트:** 이 파트는 우리 팀의 **유일한 1차 데이터**.
> 다른 파트(문헌 조사)와 톤이 달라야 한다 — "We measured this ourselves."
> 가이드: PLAN.md §5.2 — 짧은 문장 우선, 슬라이드를 그대로 읽지 말 것, **강조 단어는 굵게**.

---

## ▶ SLIDE 14 — Our Setup (Docker + tc netem) (08:10 – 08:55, 약 45초)

**화면:** ASCII 아키텍처 박스 (hft-client ↔ Docker bridge ↔ hft-server)

> Thank you, Jungha. *(짧은 인사 — 1초)*
>
> To measure the actual TCP-versus-UDP gap, we built our own HFT simulator.
> The diagram on the left shows our setup.
> A client and a server running in two Docker containers,
> connected through a Docker bridge — a **real network interface**, not loopback.
> We use `tc netem` on the server's egress to inject **reproducible** packet loss, delay, and jitter.
> Ten thousand orders per run, one hundred microseconds apart.
> Python three, raw sockets, pipe-delimited order protocol.
> We built every piece of this end-to-end.
> **This is our team's primary data.**

`▶ NEXT  →  SLIDE 15`

---

## ▶ SLIDE 15 — Baseline: TCP ≈ UDP (no loss) (08:55 – 09:35, 약 40초)

**화면:** Baseline 표 (TCP 188.6 / UDP 178.0) + "≈ 0 μs P99 difference" big-stat

> First — the baseline. **No packet loss, no delay injection.**
> TCP mean round-trip is one hundred eighty-eight microseconds.
> UDP mean is one hundred seventy-eight.
> P99 for both is around three hundred eighty microseconds.
> The gap is about **ten microseconds** — almost nothing.
>
> A naive reading of this table would conclude —
> *protocol choice doesn't matter for HFT.*
> Now let's see what happens when we add **just one percent packet loss**.

`▶ NEXT  →  SLIDE 16`

---

## ▶ SLIDE 16 — The Bombshell: 1% loss (09:35 – 10:20, 약 45초)

**화면:** TCP vs UDP P99 표 + 거대한 막대 그래프 (TCP 막대가 UDP의 ~545배)

> This is the bombshell.
> Under one percent packet loss, **UDP barely changes**.
> Mean is still one hundred seventy-eight microseconds. P99 around three hundred seventy-five.
>
> But TCP — *(말을 끊는다)* — **TCP mean jumps to two thousand three hundred microseconds.**
> **And P99 explodes to two hundred and five milliseconds.**
>
> Look at the bar chart on the right. The TCP bar is about **five hundred and forty-five times** taller than the UDP bar.
> Five hundred forty-five times. From a one percent loss rate.

`▶ NEXT  →  SLIDE 17`

---

## ▶ SLIDE 17 — Why? Linux RTO_min = 200 ms (10:20 – 11:00, 약 40초)

**화면:** Linux kernel `TCP_RTO_MIN = 200 ms` 코드 + 6단계 재전송 메커니즘

> The cause is one line in the Linux kernel source.
> TCP cannot detect a lost packet faster than its **retransmission timeout**.
> And on Linux, the floor of that timeout is hardcoded — `TCP_RTO_MIN` equals **two hundred milliseconds**.
>
> On a clean network, our RTT is around one hundred eighty microseconds.
> But the moment a packet is lost, TCP **waits at least two hundred milliseconds** before even retrying.
> The order arrives — eventually. But it arrives **a thousand times too late**.
> TCP guarantees delivery — but **its guarantee mechanism is the latency**.
>
> This is exactly Boseok's queueing-delay blow-up — measured on our own machine.

`▶ NEXT  →  SLIDE 18`

---

## ▶ SLIDE 18 — UDP Trade-off: 8/1000 lost, tail stays flat (11:00 – 11:40, 약 40초)

**화면:** UDP trade-off 카드 + 시장 데이터 vs 주문 entry 표

> What about UDP under the same one percent loss?
> UDP **loses eight out of one thousand orders**. That is the one percent.
> But the other nine hundred ninety-two arrive with the **same latency as the baseline**.
> UDP refuses to wait. **That refusal is its speed.**
>
> For HFT, this trade-off is exactly the right shape.
> Missing one market data tick is **recoverable** — the next update fixes it in microseconds.
> But a two-hundred-millisecond TCP stall is **permanent**.
> During those two hundred milliseconds, the price has moved a thousand times. The opportunity is gone.

`▶ NEXT  →  SLIDE 19`

---

## ▶ SLIDE 19 — What our data proves + handoff (11:40 – 12:10, 약 30초)

**화면:** 4 takeaway grid (Boseok 이론 검증 · Jungha 수치 정합 · TCP 한계 · UDP 트레이드오프)

> So — what does our data actually prove? **Four things.**
> One — Boseok's theory of non-linear queueing delay. **Confirmed.** Five hundred forty-five times blowup.
> Two — Jungha's kernel-overhead numbers. **Consistent** with our Python baseline.
> Three — TCP's guarantee mechanism is fundamentally **incompatible** with sub-millisecond markets.
> Four — UDP's refusal to retransmit is **exactly** the property HFT needs.
>
> Our numbers explain *why* real exchanges split their protocols.
> **Junseo** will show you who, where, and how.

`▶ HANDOFF → JUNSEO (Part 4 시작)`

---

## 발표 팁

- **속도:** 분당 약 140 단어 — 다른 파트보다 약간 빠르게. 데이터가 충격적이라 호흡이 자연스럽게 짧아진다.
- **결정적 멈춤:** Slide 16 "But TCP —" 다음 **1초 침묵**. 청중이 숨을 멈출 만큼.
- **숫자 발음:** "545 times", "200 milliseconds", "188 microseconds" 는 모두 또박또박. 자료가 이 숫자들에 걸려 있다.
- **시선:** Slide 16 막대 그래프를 한 번 가리킨 뒤 청중을 본다. 직접 측정한 자료라는 자부심이 톤에 드러나야 한다.
- **인계:** Slide 19 마지막 문장 끝나면 1초 침묵 → 자리 이동.
