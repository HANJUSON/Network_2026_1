# 김정하 — Part 2: The Solution (Kernel Bypass)

> **담당 슬라이드:** 8 – 13
> **목표 시간:** 약 4분 00초
> **약 550 단어** · 분당 약 135 wpm 기준
>
> 가이드: PLAN.md §5.2 — 짧은 문장 우선, 슬라이드를 그대로 읽지 말 것, **강조 단어는 굵게**.

---

## ▶ SLIDE 8 — 1μs = Millions, attack d_proc first (04:00 – 04:40, 약 40초)

**화면:** "20–60 μs wasted in the kernel" big-stat

> Thank you, Boseok. *(짧은 인사 — 1초)*
>
> So Boseok identified **processing delay** as one of the two software-controlled delays.
> Here is the uncomfortable truth — in a standard TCP/IP stack,
> almost **all** of that processing delay happens **inside the Linux kernel**.
> A single round-trip enters the kernel **twice** — once on receive, once on transmit.
> Each entry costs ten to thirty microseconds.
> So we waste **twenty to sixty microseconds per round-trip** just inside the kernel.
> The kernel is not slow because it is badly written. It is slow **by design** —
> for safety, fairness, and generality. HFT needs none of those.

`▶ NEXT  →  SLIDE 9`

---

## ▶ SLIDE 9 — The kernel IS the bottleneck (04:40 – 05:25, 약 45초)

**화면:** 5-step timeline, 가운데 3 단계 (NIC RX · Kernel RX · Logic · Kernel TX · NIC TX), 커널 단계 빨강

> Here is a single trading round-trip dissected. The **red blocks** are pure kernel overhead.
> The NIC receives the packet — one to three microseconds.
> Then the **kernel** takes ten to thirty microseconds to process it.
> The actual **trading logic** — the brains of the operation — runs in only **one to five** microseconds.
> Then the kernel takes another ten to thirty on the way out.
> Finally the NIC transmits — another one to three microseconds.
>
> Look at the ratio. We spend **ten times more time shuffling packets**
> than thinking about trades.
> Top firms target tick-to-trade under ten microseconds. That target is **impossible**
> if the kernel is still on the path.

`▶ NEXT  →  SLIDE 10`

---

## ▶ SLIDE 10 — Why the kernel wastes microseconds (05:25 – 06:05, 약 40초)

**화면:** 4-card grid (Interrupts · Copies · Context switching · Protocol processing)

> Why is the kernel so slow? **Four reasons**, all of them deliberate design choices.
>
> First, **interrupts** — every incoming packet raises an IRQ, causing a context switch and cache pollution.
> Second, **memory copies** — the packet is copied from NIC ring to kernel buffer to user buffer.
> Each copy costs hundreds of nanoseconds.
> Third, **context switching** — every system call crosses the user-kernel boundary, flushing registers and TLB.
> Fourth, **protocol processing** — the TCP state machine, congestion control, and scheduling —
> written for generality, not for one-microsecond targets.
>
> The conclusion writes itself.
> **If the kernel is the bottleneck, the answer is to skip it entirely.**

`▶ NEXT  →  SLIDE 11`

---

## ▶ SLIDE 11 — Three bypass approaches (06:05 – 06:50, 약 45초)

**화면:** 3-card grid (OpenOnload · DPDK · RDMA, 각 latency 표시)

> There are three main ways to bypass the kernel.
>
> **OpenOnload.** A user-space TCP/IP stack you inject via `LD_PRELOAD`.
> Your existing socket calls are rerouted. **Zero code change**. Latency drops to one to three microseconds.
> The catch — it needs a Solarflare NIC.
>
> **DPDK.** Poll-mode driver. The application owns the NIC directly and busy-polls for packets.
> Sub-microsecond. But it requires a **full rewrite** of the network code, plus huge pages and NUMA pinning.
>
> **RDMA.** The NIC writes directly to remote process memory, bypassing the CPU entirely.
> One to two microseconds, **zero-copy**. But you need an InfiniBand or RoCE fabric.

`▶ NEXT  →  SLIDE 12`

---

## ▶ SLIDE 12 — Deep dive: how each one skips the kernel (06:50 – 07:30, 약 40초)

**화면:** 4-layer stack (DPDK · OpenOnload · RDMA · Standard TCP), latency cost on right

> A quick deep dive on the mechanism.
>
> **DPDK** uses busy-polling — no interrupts at all. Huge pages avoid TLB misses. NUMA pinning keeps memory local.
> **OpenOnload** intercepts socket calls via `LD_PRELOAD` and reroutes them through a user-space TCP stack. Same API.
> **RDMA** goes furthest — it uses a **verbs API**, not BSD sockets, and the NIC reads and writes remote memory directly. The CPU is not involved at all.
>
> Compare these to **standard TCP** at the bottom — the kernel touches every packet. Thirty to sixty microseconds.
> Compatible with everything; fast at nothing.

`▶ NEXT  →  SLIDE 13`

---

## ▶ SLIDE 13 — Comparative matrix + handoff (07:30 – 08:10, 약 40초)

**화면:** Comparative matrix (TCP / OpenOnload / DPDK / RDMA × Latency · Code · HW · Best for)

> Here is the comparative matrix. Standard TCP at the top — slow but universal.
> OpenOnload — fast, no code change, but locked to Solarflare hardware.
> DPDK — fastest, but a full rewrite.
> RDMA — fast and zero-copy, but needs a different fabric entirely.
>
> The trade-off is **always the same**:
> **the more kernel you bypass, the faster you go — and the more your code and hardware must change.**
>
> *(짧은 호흡)*
>
> Now — these numbers are from industry whitepapers.
> But what about the underlying **TCP-versus-UDP gap** itself?
> Can we measure it ourselves, on our own laptops? **Hanju** ran the experiment.

`▶ HANDOFF → HANJU (Part 3 시작)`

---

## 발표 팁

- **속도:** 분당 약 135 단어. 기술 용어(DPDK, RDMA, LD_PRELOAD)는 **또박또박**.
- **숫자 강조:** "20–60 μs", "1–5 μs", "ten times more" 같은 비교 숫자는 한 박자 멈춘 뒤 발음.
- **약어 발음:** DPDK = "디-피-디-케이", RDMA = "알-디-엠-에이", `LD_PRELOAD` = "엘-디 프리로드".
- **시선:** Slide 9의 "ten times more" 와 Slide 13의 "always the same" 에서 청중을 본다.
- **인계:** "Hanju ran the experiment." 후 1초 침묵 → 자리 이동.
