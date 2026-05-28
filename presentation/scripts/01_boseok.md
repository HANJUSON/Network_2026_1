# 김보석 — Opening + Part 1: The Problem

> **담당 슬라이드:** 1 – 7 (Title + Agenda + Part 1 전체)
> **목표 시간:** 약 4분 00초 (Opening 30초 + Part 1 3분 30초)
> **약 540 단어** · 분당 약 135 wpm 기준
>
> 가이드: PLAN.md §5.2 — 짧은 문장 우선, 슬라이드를 그대로 읽지 말 것, **강조 단어는 굵게**.
> 슬라이드 전환은 `▶ NEXT` 마커가 나오는 순간에 리모컨을 누른다.

---

## ▶ SLIDE 1 — Title (00:00 – 00:08, 약 8초)

**화면:** `CN_Module5_Group7` — Topic / 팀원 카드

> Good afternoon, everyone. We are **Group Seven**.
> Today's topic is **Network Latency in High-Frequency Trading** —
> why **one microsecond** is worth millions of dollars, and where it disappears.

`▶ NEXT  →  SLIDE 2`

---

## ▶ SLIDE 2 — Agenda (00:08 – 00:30, 약 22초)

**화면:** 4-card agenda (Problem · Solution · Validation · Application)

> Our talk has **four parts**.
> First, **I** will explain the problem — what HFT is, and which network delays software can actually control.
> Then **Jungha** shows the industry's main solution: **kernel bypass**.
> Next, **Hanju** runs the experiment that validates the theory with our own measurements.
> And finally, **Junseo** connects everything to how real exchanges — NASDAQ, CME, NYSE — apply this in practice.
> Let's begin with the problem.

`▶ NEXT  →  SLIDE 3`

---

## ▶ SLIDE 3 — What is HFT, and why μs matter (00:30 – 01:15, 약 45초)

**화면:** HFT 정의 + ~50% 비중 + $100M / ms

> **High-Frequency Trading** is algorithmic, microsecond-scale automated trading.
> Machines decide and submit orders — not humans.
> About **fifty percent** of all US equity volume is HFT.
> According to **industry estimates**, a **one-millisecond** latency advantage is worth roughly
> **tens of millions of dollars per year** to a major investment bank.
> This is not a niche academic problem. It is a **fifty-percent-of-the-market** problem.

`▶ NEXT  →  SLIDE 4`

---

## ▶ SLIDE 4 — Tail latency beats mean (01:15 – 02:00, 약 45초)

**화면:** Tail latency 분포 곡선 (mean vs P99)

> In HFT, only **the first arriving order** captures the trade. Second place wins nothing.
> So a system with a mean of one hundred microseconds but a P99 tail of **two hundred milliseconds**
> is effectively unusable. The mean lies.
> **The tail is where the money lives — or where it evaporates.**
> For the rest of this presentation, our key metric is one specific number:
> **P99 round-trip time under packet loss.**

`▶ NEXT  →  SLIDE 5`

---

## ▶ SLIDE 5 — Four sources of network delay (02:00 – 02:40, 약 40초)

**화면:** 4-step timeline (d_proc, d_queue, d_trans, d_prop)

> From the Kurose and Ross textbook, every packet pays **four taxes** on its journey.
> **Processing delay** — header inspection, kernel work, decoding.
> **Queueing delay** — time waiting in buffers before transmission.
> **Transmission delay** — pushing bits onto the link at line rate.
> And **propagation delay** — the actual travel through fiber, at near light-speed.
> Total delay is the sum of these four.
> Remember this decomposition — it is the foundation for everything that follows.

`▶ NEXT  →  SLIDE 6`

---

## ▶ SLIDE 6 — Which delays can software actually move? (02:40 – 03:20, 약 40초)

**화면:** 4-delay 표 (d_proc, d_queue가 software lever)

> Now — which of these four can software actually move?
> **Propagation** is fixed. It is a real-estate problem, solved by **co-location**.
> **Transmission** is also effectively constant once you upgrade to ten- or hundred-gigabit links.
> That leaves us with two software-controlled delays — **processing** and **queueing**.
> **Light speed is fixed. Software isn't.**
> And it turns out these are exactly the two delays that dominate microsecond-scale systems.

`▶ NEXT  →  SLIDE 7`

---

## ▶ SLIDE 7 — d_queue is non-linear (03:20 – 04:00, 약 40초)

**화면:** 큐잉 지연 곡선 (ρ → 1에서 폭발) + Flash Crash 메모

> Queueing delay has one dangerous property — it is **non-linear**.
> As traffic intensity rho approaches capacity, queueing delay does not grow gradually.
> It **explodes**.
> A single burst of packet loss or retransmission can push the tail
> from microseconds to **hundreds of milliseconds**.
> The 2014 US Treasury **Flash Crash** showed exactly this in production — a thirty-three basis-point swing in ten minutes.
> Average is fine until rho approaches one. Then everything explodes.

> *(짧은 호흡)*

> So — how does the industry actually escape this kernel-level bottleneck?
> **Jungha** will show you.

`▶ HANDOFF → JUNGHA (Part 2 시작)`

---

## 발표 팁

- **속도:** 분당 약 130 단어. 영어가 빠르게 느껴지면 의도적으로 마침표마다 0.3초 멈출 것.
- **강조 단어:** 굵은 단어는 **반 박자 늦게 + 살짝 크게** 발음.
- **시선:** Slide 3의 "$100M" 와 Slide 7의 "explodes" 에서 청중을 한 번씩 본다.
- **리모컨:** 슬라이드 전환은 마침표 직후, 다음 문장을 시작하기 *직전*에 누른다 (영상 합본 시 컷 지점 깔끔).
- **인계:** Slide 7 마지막 "Jungha will show you." 다음 약 1초 침묵 후 자리 이동 (편집 시 cross-fade 가능).
