# 이준서 — Part 4: Industry Applications + Conclusion + Q&A

> **담당 슬라이드:** 20 – 26 (Part 4 전체 + 마무리 + Q&A)
> **목표 시간:** 약 4분 20초 (Part 4 4분 + 마무리 20초)
> **약 620 단어** · 분당 약 140 wpm 기준
>
> **역할:** 발표 전체를 **현실 세계에 착륙시키는** 마지막 주자.
> 이론(김보석) + 솔루션(김정하) + 실측(손한주) 을 NASDAQ / CME / NYSE / Citadel 사례로 통합.
> 가이드: PLAN.md §5.2 — 짧은 문장 우선, 슬라이드를 그대로 읽지 말 것, **강조 단어는 굵게**.

---

## ▶ SLIDE 20 — Industry's answer: split the protocol (12:10 – 12:55, 약 45초)

**화면:** Matching Engine → UDP MD / TCP OE 분할 도식

> Thank you, Hanju. *(짧은 인사 — 1초)*
>
> Hanju showed us why a **single** protocol can't win on both reliability and speed.
> The industry's answer is — **don't pick one. Pick both, by purpose.**
>
> Real exchanges split their network into two separate channels.
> The first — **UDP multicast** — broadcasts market data to every subscriber simultaneously.
> Speed matters here. One lost tick is replaceable by the next update.
> The second — **TCP, or FIX, or OUCH** — handles order entry. One client at a time.
> Reliability matters here. An order must arrive, exactly once, in order.
>
> Real exchanges don't pick TCP **or** UDP. They use **both**, by purpose.

`▶ NEXT  →  SLIDE 21`

---

## ▶ SLIDE 21 — Three exchanges, same pattern (12:55 – 13:35, 약 40초)

**화면:** NASDAQ · CME · NYSE 비교 표

> The same pattern appears at **every major exchange**.
>
> **NASDAQ** — market data over a protocol called `MoldUDP64`, UDP multicast. Orders go over `OUCH`, on TCP.
> **CME**, the Chicago futures exchange — market data over `MDP 3.0`, UDP multicast with binary `SBE` encoding. Orders over `iLink 3` on TCP.
> **NYSE** — `Pillar` UDP multicast for data, with redundant A and B lines for reliability. FIX over TCP for orders.
>
> **Independently invented. Independently the same answer.** UDP for the broadcast, TCP for the per-client transaction.

`▶ NEXT  →  SLIDE 22`

---

## ▶ SLIDE 22 — CME's clever hybrid (13:35 – 14:15, 약 40초)

**화면:** UDP 멀티캐스트 + TCP recovery 흐름도

> CME takes this one step further with a **clever hybrid**.
>
> Market data flows over UDP multicast — fast, no head-of-line blocking.
> Each message carries a **sequence number**.
> If a subscriber detects a gap — for example, sequence one-oh-two is missing —
> it sends a query over a **separate TCP recovery channel** asking for that specific packet.
>
> The hot path stays on UDP. Recovery happens **out-of-band**, only when needed.
> Subscribers without gaps pay nothing for reliability they don't use.
> **Best of both worlds** — UDP speed, TCP recovery, no head-of-line blocking.

`▶ NEXT  →  SLIDE 23`

---

## ▶ SLIDE 23 — Top HFT firms, same recipe (14:15 – 14:45, 약 30초)

**화면:** Citadel · Jane Street · Jump · Virtu 4-card grid

> And the top HFT firms apply the same recipe — only harder.
> Citadel Securities, Jane Street, Jump Trading, Virtu Financial.
> All of them: **UDP multicast** for market data, **TCP** for orders, **kernel bypass** for both.
>
> Jane Street's public engineering blog states it explicitly — and I quote:
> *"P99 latency is what we optimize, not mean."*
> This is **exactly** what Hanju's experiment measured.

`▶ NEXT  →  SLIDE 24`

---

## ▶ SLIDE 24 — Our data ↔ industry practice (14:45 – 15:30, 약 45초)

**화면:** 좌우 분할 표 (Our experiment ↔ Industry does)

> Now — the direct mapping between our experiment and industry practice.
>
> **We measured** TCP's P99 at two hundred and five milliseconds under loss.
> **Industry uses** UDP multicast for market data — NASDAQ MoldUDP64.
>
> **We measured** UDP losing eight out of a thousand but keeping the tail flat.
> **Industry uses** UDP plus TCP recovery only on gaps — CME MDP 3.0.
>
> **We measured** TCP guaranteeing delivery at the cost of tail latency.
> **Industry uses** TCP for order entry, where correctness beats speed — NYSE Pillar.
>
> **We didn't guess.** We measured the exact trade-off the entire industry is built around.

`▶ NEXT  →  SLIDE 25`

---

## ▶ SLIDE 25 — Conclusion & future directions (15:30 – 16:15, 약 45초)

**화면:** 좌(What we learned) · 우(Future directions)

> To conclude. We learned four things.
> One — the HFT bottleneck is **software**, not physics. Processing delay and queueing delay.
> Two — **kernel bypass** attacks processing delay. DPDK, OpenOnload, RDMA.
> Three — **protocol split** attacks queueing delay and tail latency. UDP plus TCP.
> Four — both layers must be optimized together. Neither alone is enough.
>
> Looking forward — **QUIC** and **SRT** are user-space transports with built-in loss recovery.
> **SmartNICs** and **P4-programmable switches** push logic into the network fabric itself.
> **FPGA acceleration** runs trading logic in hardware.
> The real question for the next five years is —
> how much of an entire trading strategy can fit **inside the NIC itself**.

`▶ NEXT  →  SLIDE 26`

---

## ▶ SLIDE 26 — Q&A and Closing (16:15 – 16:35, 약 20초)

**화면:** "Q & A" 메가 텍스트 + References + repo link

> **One microsecond is not just a number.**
> It is the difference between a profitable trade and a missed one —
> and the industry has built an entire technology stack to chase it.
>
> Thank you for listening.
> Our key references and the project repository are on this slide.
> We will be happy to take any questions in the offline Q&A session.
>
> Thank you.

`▶ END (마지막 슬라이드 유지, 발표 종료)`

---

## 발표 팁

- **속도:** 분당 약 140 단어. 마무리 톤은 다른 파트보다 약간 **느리고 묵직하게**.
- **인용 처리:** Slide 23의 Jane Street 인용 — *"P99 latency is what we optimize, not mean."* 는 살짝 톤을 낮춰 인용임을 명확히.
- **결정적 문장:** Slide 24의 *"We didn't guess. We measured the exact trade-off the entire industry is built around."* — 짧게 끊고 청중을 한 번 본다. 발표 전체의 클라이맥스.
- **마무리 호흡:** Slide 26 "One microsecond is not just a number." 다음 **0.5초 멈춤** → "It is the difference..."
- **종료 인사:** "Thank you." 후 무대 정면을 향해 2초 정도 시선 유지 (영상 합본 시 fade-out 지점).

---

## 전체 발표 누적 타임라인 (참고)

| 시점 | 슬라이드 | 담당 | 비고 |
|---|---|---|---|
| 00:00 | 1 Title | 김보석 | 시작 |
| 00:08 | 2 Agenda | 김보석 | |
| 00:30 | 3 What is HFT | 김보석 | Part 1 시작 |
| 04:00 | 8 1μs = millions | 김정하 | Part 2 시작 |
| 08:10 | 14 Setup | 손한주 | Part 3 시작 |
| 12:10 | 20 Split protocol | 이준서 | Part 4 시작 |
| 16:15 | 26 Q&A | 이준서 | 마무리 |
| 16:35 | — | — | 종료 (총 16분 35초) |

PLAN.md §2 의 목표(총 16~17분) 안에 들어옴 ✓
