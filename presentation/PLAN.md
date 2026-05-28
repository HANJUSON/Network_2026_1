# 최종 발표 자료 기획서 — Group 07

> **컴퓨터 네트워크 (DCCS307) Module 5 — Case Study Project**
> **주제:** Network Latency in High-Frequency Trading (HFT)
> **발표 언어:** 영어 (각자 개별 영상 녹화 후 편집 합본)
> **최종 산출물:** `presentation.html` (HTML 슬라이드 덱)
> **계획 작성일:** 2026-05-21

---

## 1. 발표 전체 컨셉

### 1.1 핵심 스토리라인 (One-Sentence Pitch)

> "HFT에서 1μs가 수백만 달러를 결정한다. 그 1μs가 어디서 새는지 (Problem), 산업이 어떻게 막는지 (Solution), 실측으로 증명하고 (Validation), 실제 거래소는 어떻게 적용하는지 (Application) 를 보여준다."

### 1.2 발표 흐름의 논리적 정당성

`logistics PDF`의 Recommended Presentation Structure(13~14쪽)와 일치시킨다:

| Logistics 권장 구조 | 우리 매핑 | 담당자 |
|---|---|---|
| 1. Introduction & Motivation | HFT란 무엇이며 왜 1μs가 돈인가 | 김보석 |
| 2. Problem Statement | 4대 지연 중 d_proc, d_queue가 병목 | 김보석 |
| 3. Solutions & Technical Approaches | Kernel Bypass (DPDK / OpenOnload / RDMA) | 김정하 |
| 3-b. Empirical Validation | TCP vs UDP 실측 (Docker + tc netem) | 손한주 |
| 4. Industry Applications, Trade-offs | NASDAQ, CME, NYSE, Citadel, Jane Street 사례 | 이준서 |
| 5. Conclusion & Future Directions | 종합 + 미래 (이준서 마무리 또는 손한주가 짧게 wrap-up) | 이준서 |

### 1.3 발표 순서 결정 근거

**김보석 → 김정하 → 손한주 → 이준서** 순서로 진행한다.

- **김보석이 첫 번째:** 청중이 HFT가 뭔지, 왜 큐잉/처리 지연이 핵심인지를 모르면 이후 모든 설명이 공중분해된다. 도메인과 4대 지연 정의가 모든 후속 슬라이드의 전제 조건.
- **김정하가 두 번째:** 김보석이 정의한 "d_proc 병목"을 산업이 어떻게 푸는지 (Kernel Bypass) 가 자연스러운 다음 질문이다.
- **손한주가 세 번째:** 김정하의 이론적 솔루션을 우리 팀이 어떻게 실측·검증했는지 보여주는 단계. "We didn't just read about it, we measured it."
- **이준서가 마지막:** 실측 결과를 실제 거래소가 어떻게 적용하는지로 연결하여 발표를 현실 세계에 착륙시킨다. Conclusion까지 함께 마무리.

각 사람의 슬라이드는 **연속된 블록**으로 구성되어야 한다 (영상 편집 합본 요구사항).

---

## 2. 발표 시간 배분 (가정: 총 15~20분)

| 파트 | 담당 | 슬라이드 수 (목표) | 영상 길이 (목표) |
|---|---|---|---|
| Opening (Title + Agenda) | 공동 (음성은 김보석) | 2 | 30초 |
| **Part 1 — Problem** | 김보석 | 4~5 | 3분 30초 |
| **Part 2 — Solution (Kernel Bypass)** | 김정하 | 5~6 | 4분 |
| **Part 3 — Empirical Validation** | 손한주 | 5~6 | 4분 |
| **Part 4 — Industry Cases & Conclusion** | 이준서 | 5~6 | 4분 |
| Closing (References + Q&A 안내) | 공동 (음성은 이준서) | 1 | 30초 |
| **합계** | | **22~26 슬라이드** | **약 16~17분** |

> 영상 합본이므로 슬라이드 내 화면 전환 효과는 최소화하고, 각 사람의 마지막 슬라이드에 다음 발표자 이름을 자연스럽게 인계하는 한 줄을 넣는다 (예: "Next, Jeongha will explain how the industry bypasses this bottleneck.").

---

## 3. 파트별 상세 슬라이드 구성

### Part 0 — Opening (Slide 1~2)

#### Slide 1: Title Slide
- 제목: **"The Microsecond Arms Race: TCP, UDP, and the Kernel in High-Frequency Trading"**
- 부제: "Why 1μs is worth millions, and where it disappears"
- Group 07 — Boseok Kim, Jeongha Kim, Hanju Son, Junseo Lee
- DCCS307 Computer Networks, Module 5, 2026

#### Slide 2: Agenda
- 한 장에 4파트 + 담당자 사진/이름을 시각적으로 배치
- 청중에게 "각 파트가 어떻게 연결되는지" 한눈에 보여주는 다이어그램 1개

---

### Part 1 — Problem (김보석, Slide 3~7)

> **목표:** "HFT가 뭔지 모르는 청중을 5분 안에 'd_queue와 d_proc이 왜 통제 가능한 유일한 변수인지' 까지 끌고 간다."
>
> **원본 자료:** `김보석_HFT_problem_and_delay_analysis.pdf`

#### Slide 3: What is HFT, and Why Microseconds Matter
- HFT 정의: 알고리즘 기반 µs 단위 자동매매
- 미국 주식 거래량의 약 50%가 HFT
- 1ms 단축 = 일일 수익 수백만 달러 [Aquilina, Budish, O'Neill 2022]
- **핵심 메시지:** "This is not a niche problem. It's a 50%-of-the-market problem."

#### Slide 4: Winner-Takes-All — Why Tail Latency Beats Mean
- 가격 변동 순간 → 첫 번째 도착자만 수익 독점
- 평균 100μs인 시스템이 P99에서 200ms면 → "사실상 사용 불가능"
- **그림:** Tail latency 분포 곡선 (mean vs P99/P99.9 시각화)
- **메시지:** "HFT lives or dies at the tail, not at the average."

#### Slide 5: The Four Sources of Network Delay
- Kurose 교과서 4대 지연 다이어그램 (d_proc, d_queue, d_trans, d_prop)
- 각각의 정의를 한 줄씩
- **이 슬라이드는 다음 슬라이드의 전제**

#### Slide 6: Why d_queue and d_proc Are the *Only* Knobs We Can Turn
- 표 (김보석 PDF 3.1 절):
  | Delay | Control Lever | Project Relevance |
  |---|---|---|
  | d_prop | Co-location, microwave | 부동산/상수 |
  | d_trans | 10/40/100 GbE | 인터넷 인프라/상수 |
  | **d_proc** | Kernel bypass (DPDK, OpenOnload) | **소프트웨어 영역** |
  | **d_queue** | Protocol, QoS, buffer | **소프트웨어 영역** |
- **메시지:** "Light speed is fixed. Software isn't."

#### Slide 7: d_queue Is Non-Linear — That's the Real Danger
- Kurose의 packet queueing delay 그래프 (La/R → 1일 때 지연 폭발)
- Flash Crash (2014) 사례 1줄: "10년물 국채 33~34bp 급락, 10분 만에 회복"
- **메시지:** "Average is fine until ρ→1. Then everything explodes."
- **다음 파트 인계 멘트:** "So how does the industry actually escape this kernel-level bottleneck? Jeongha will show you."

---

### Part 2 — Solution: Kernel Bypass (김정하, Slide 8~13)

> **목표:** "Standard TCP/IP가 왜 못 따라가는지, 산업은 무엇으로 대체했는지를 비교 매트릭스로 끝낸다."
>
> **원본 자료:** `김정하_HFT_Kernel_Bypass_Networking.pdf` (이미 영어 슬라이드 형식, 거의 그대로 재사용 가능)

#### Slide 8: 1μs = Millions
- 도입 (김정하 PDF 2쪽)
- 김보석의 d_proc 병목 정의를 받아 "이제 그 d_proc을 어떻게 줄이는지 보여드리겠다"

#### Slide 9: The Kernel Is the Bottleneck
- Exchange → NIC → Kernel TCP/IP → App → Kernel → NIC 흐름도
- 단계별 latency: 커널 진입이 양방향 합쳐서 20~60μs 낭비
- (김정하 PDF 3쪽 그대로)

#### Slide 10: Why the Kernel Wastes Microseconds
- 4가지 원인: Interrupts, Memory copies, Context switching, Protocol processing
- **결론 박스:** "If the kernel is the bottleneck, the answer is to skip it entirely."
- (김정하 PDF 4쪽 그대로)

#### Slide 11: Three Bypass Approaches — Performance vs Compatibility
- DPDK / RDMA / OpenOnload 비교 그래프 (김정하 PDF 5쪽)
- 한 슬라이드에 3개 모두 한눈에

#### Slide 12: Deep Dive — DPDK, OpenOnload, RDMA (각 1줄씩)
- DPDK: Poll mode, Huge pages, NUMA pinning → < 1μs
- OpenOnload: LD_PRELOAD 호환 user-space TCP/IP → 1~3μs
- RDMA: NIC가 원격 메모리에 직접 쓰기, CPU 우회 → 1~2μs
- (김정하 PDF 6~8쪽 압축. 시간 부족 시 한 슬라이드로 합치고 디테일은 발표자 설명으로)

#### Slide 13: Comparative Matrix (Bottom Line)
- 김정하 PDF 9쪽 표 그대로 (Standard TCP/IP, OpenOnload, DPDK, RDMA × Latency, Code change, Hardware, Best for)
- **결론 박스:** "The more of the kernel you bypass, the faster you go — and the more your code and hardware must change."
- **다음 파트 인계 멘트:** "These numbers are from industry whitepapers. But what if we measure the *underlying* TCP vs UDP gap ourselves? Hanju will show you."

---

### Part 3 — Empirical Validation: TCP vs UDP Benchmark (손한주, Slide 14~19)

> **목표:** "Python + Docker만으로도 'TCP가 손실 환경에서 무너지는 비대칭'을 직접 보여줄 수 있다는 것을 증명한다. 우리가 직접 만든 시스템 + 실제 측정값."
>
> **원본 자료:** `README.md`, `hft_client/results/*.json`, `CN_Module5_MidpointReport_Group07.md`
>
> **차별점:** 우리 팀의 *유일한 1차 데이터*. 다른 3개 파트는 문헌 조사지만 이건 우리가 만든 것.

#### Slide 14: Our Experimental Setup
- 아키텍처 다이어그램:
  ```
  [hft-client 10.10.0.3] ─ Docker bridge ─ [hft-server 10.10.0.2]
                                ↑
                       tc netem (server egress)
  ```
- Why Docker, not localhost? → "Loopback bypasses NIC. We need a real interface."
- Why tc netem? → "Reproducible packet loss / delay / jitter."
- 사용 기술: Python 3, raw socket, Docker, tc netem
- 메시지: "We built our own HFT simulator end-to-end."

#### Slide 15: Baseline — TCP ≈ UDP (No Loss)
- 표 (README의 실측 결과):
  | Metric | TCP | UDP |
  |---|---|---|
  | Mean | 188.6 μs | 178.0 μs |
  | P99 | 375.7 μs | 386.1 μs |
- **메시지:** "Without packet loss, the choice barely matters. ~10μs gap."
- **그래서?** → "Now let's add 1% packet loss and see what happens."

#### Slide 16: The Bombshell — 1% Packet Loss
- 표:
  | Metric | TCP | UDP |
  |---|---|---|
  | Mean | **2,306 μs** | **177.9 μs** |
  | P99 | **204,812 μs (≈205 ms)** | **374.5 μs** |
  | Delivered | 1000/1000 | 992/1000 |
- **시각화:** P99 막대 그래프 (TCP의 막대가 UDP의 ~545배)
- **메시지:** "TCP's P99 exploded by 545× from a 1% loss rate."

#### Slide 17: Why? Linux RTO_min = 200ms
- TCP의 Retransmission Timeout 최소값 (200ms)이 어떻게 P99를 폭발시키는지 도식
- "TCP guarantees delivery — but its guarantee mechanism *is* the latency."
- **메시지:** 김보석의 "d_queue는 비선형이다" 그래프와 완벽히 일치

#### Slide 18: UDP Trade-off — 8/1000 Lost, but Tail Stays Flat
- UDP는 8개 손실 (1% 손실율) — but 나머지 992개는 baseline과 동일한 지연
- **메시지:** "UDP refuses to wait. That refusal *is* its speed."
- HFT에서 시세 데이터 1개 손실 = 다음 업데이트로 만회 가능
- HFT에서 P99 200ms 지연 = 거래 기회 영구 손실

#### Slide 19: What Our Data Proves
- 김보석의 이론 (d_queue 비선형 폭발) → 실측으로 확인 ✓
- 김정하의 "Standard TCP/IP는 30~60μs" → 우리 baseline 188μs는 Python 오버헤드 포함으로 정합 ✓
- **다음 파트 인계 멘트:** "Our numbers explain *why* real exchanges split their protocols. Junseo will show you who, where, and how."

---

### Part 4 — Industry Cases & Conclusion (이준서, Slide 20~25)

> **목표:** "이론(김보석) + 솔루션(김정하) + 실측(손한주)을 실제 NASDAQ/CME/NYSE/Citadel의 아키텍처에 매핑하여 발표를 현실에 착륙시킨다."
>
> **원본 자료:** `이준서_조사자료.pdf`

#### Slide 20: The Industry's Answer — Split the Protocol
- 도식:
  ```
  [Exchange Matching Engine]
        ├── Market Data Feed  → UDP Multicast (속도)
        └── Order Entry Gateway → TCP / FIX / OUCH / iLink (신뢰성)
  ```
- **메시지:** "Real exchanges don't pick TCP *or* UDP. They use both, by purpose."

#### Slide 21: Exchange Case Studies
- 한 슬라이드에 3대 거래소 비교:
  | Exchange | Market Data | Order Entry |
  |---|---|---|
  | NASDAQ | TotalView-ITCH over MoldUDP64 | OUCH over TCP |
  | CME | MDP 3.0 (UDP multicast + SBE) | iLink 3 |
  | NYSE | Pillar (UDP multicast, A/B redundant lines) | Pillar FIX Gateway (TCP) |
- 각 거래소 공식 문서 링크 (footnote)

#### Slide 22: The Clever Hybrid — CME's UDP + TCP Recovery
- CME의 핵심 트릭: UDP로 빠르게 받다가 sequence gap 발생 시에만 TCP로 재전송 요청
- 도식 (이준서 PDF 3~4쪽)
- **메시지:** "Best of both worlds — UDP speed, TCP recovery, no head-of-line blocking."

#### Slide 23: Top HFT Firms — Same Pattern
- Citadel Securities, Jane Street, Jump Trading, Virtu Financial
- 공통: UDP for market data, TCP for orders, kernel bypass for both
- Jane Street의 "P99 latency > mean latency"이 우리 실측과 정확히 일치하는 이유 강조

#### Slide 24: Our Data ↔ Industry Practice
- 좌우 분할 슬라이드:
  | Our Experiment Said | Industry Does |
  |---|---|
  | TCP P99 → 205ms under loss | NASDAQ Market Data = UDP |
  | UDP loses 8/1000 but tail stays flat | CME uses UDP + TCP recovery only on gaps |
  | TCP guarantees delivery at the cost of tail | NYSE Order Entry = TCP (correctness > speed) |
- **메시지:** "We didn't just guess. We measured the exact trade-off the industry is built around."

#### Slide 25: Conclusion & Future Directions
- **What we learned:**
  1. HFT bottleneck is software (d_proc + d_queue), not physics
  2. Kernel bypass (DPDK/OpenOnload/RDMA) attacks d_proc
  3. Protocol split (UDP+TCP) attacks d_queue/tail latency
  4. Both layers must be optimized together
- **Future directions:**
  - QUIC / SRT 같은 user-space transport
  - SmartNIC, P4-programmable switches
  - Hardware (FPGA) acceleration의 한계와 비용
- **마무리:** "1μs is not just a number. It's the difference between a profitable trade and a missed one."

#### Slide 26: References & Q&A
- 핵심 참고문헌 5~7개 (Aquilina 2022, Lockwood 2012, DPDK Guide, CME/NASDAQ/NYSE 공식 문서)
- GitHub 저장소 링크
- "Q&A → Offline session"

---

## 4. 시각 디자인 가이드

### 4.1 컬러 팔레트 (기존 `team_summary.html`과 일관성 유지 권장)
- 배경: 어두운 네이비 (`#0a0e27` 또는 화이트, 슬라이드 톤에 따라 선택)
- 강조 (TCP): `#00d4ff` 청록
- 강조 (UDP): `#ffaa00` 주황
- 위험/경고 (P99 폭발 같은 충격적 수치): `#ff4757` 빨강
- 정상/안정: `#00ff88` 초록

### 4.2 폰트
- 제목: Inter 또는 Pretendard Bold
- 본문: Inter Regular
- 숫자/코드: JetBrains Mono

### 4.3 슬라이드 디자인 원칙
1. **한 슬라이드 = 하나의 주장** (Kurose 책처럼 다 적지 말 것)
2. **숫자는 크게** (특히 205ms, 545×, 1μs 같은 충격적 수치)
3. **다이어그램 > 문장** (특히 김보석 4대 지연, 손한주 Docker 아키텍처, 이준서 거래소 도식)
4. **각 사람 파트의 첫 슬라이드 우상단에 작은 진행 표시바** (예: "Part 2 of 4 — Solution")

### 4.4 파트 간 시각적 구분
- 각 파트 시작 전에 풀스크린 섹션 헤더 슬라이드를 넣을지 검토 (시간 여유 있으면)
- 또는 헤더 색상 띠로만 구분 (시간 절약)

---

## 5. 영어 스크립트 작성 가이드

### 5.1 스크립트는 별도 파일로 관리
- `presentation/scripts/01_boseok.md`
- `presentation/scripts/02_jeongha.md`
- `presentation/scripts/03_hanju.md`
- `presentation/scripts/04_junseo.md`
- 각 파일에는 슬라이드 번호 + 영어 발표 스크립트 + 강조 단어 굵게 표시

### 5.2 영어 작성 원칙
- 평균 분당 130~150 단어 (학부 비원어민 기준)
- 짧은 문장 우선. "And" 대신 마침표.
- 슬라이드의 단어를 그대로 읽지 말 것 (슬라이드 = 시각 보조, 스크립트 = 청각 설명)
- 각 사람 마지막 슬라이드에 다음 발표자 인계 멘트 필수

### 5.3 인계 멘트 예시
- 김보석 → 김정하: "So we know *what* the bottleneck is. The next question is: how does the industry bypass the kernel? Jeongha."
- 김정하 → 손한주: "Kernel bypass attacks d_proc. But what about d_queue and the TCP-vs-UDP question? Hanju ran the experiment."
- 손한주 → 이준서: "Our numbers explain why exchanges split their protocols. Junseo will show who, where, and how."
- 이준서 → 끝: "Thank you. We'll take your questions in the offline Q&A."

---

## 6. HTML 구현 가이드

### 6.1 추천 프레임워크
- **Reveal.js** (CDN 한 줄로 시작 가능, GitHub Pages 호환, 키보드 네비게이션, 강의 발표에 표준)
- 대안: 직접 CSS + JS scroll-snap (가벼움 / 커스텀 자유도 ↑, 학습비용 ↓)
- 기존 `team_summary.html`이 이미 직접 작성 스타일이므로 톤 일관성을 위해 **직접 작성**을 추천

### 6.2 파일 구조
```
presentation/
├── PLAN.md                        ← 이 문서
├── presentation.html              ← 최종 HTML 슬라이드 (루트의 기존 것 대체할지는 별도 결정)
├── assets/
│   ├── css/style.css
│   ├── js/slides.js
│   └── img/                        ← 다이어그램 PNG/SVG
├── scripts/
│   ├── 01_boseok.md
│   ├── 02_jeongha.md
│   ├── 03_hanju.md
│   └── 04_junseo.md
└── (기존 PDF 자료들은 그대로 보존)
```

### 6.3 슬라이드 식별자 규칙
- 각 슬라이드에 `id="slide-XX"` 부여 (XX는 01~26)
- 각 사람 파트 시작 슬라이드에 `class="part-start"` (영상 녹화 시 시작 지점 식별 용이)
- 각 사람 파트 종료 슬라이드에 `class="part-end"` (편집 합본 시 컷 지점)

### 6.4 영상 녹화 친화 디자인
- 화면 좌하단에 작은 발표자 이름 라벨 고정 (편집 시 누가 말하는지 즉시 확인)
- 슬라이드 전환을 페이드 0.2초로 단순화 (영상 합본 시 ghost frame 방지)
- 라이브 데모 없음 (모든 결과는 정적 차트/표로)

---

## 7. 마감 일정 제안 (오늘 = 2026-05-21)

| 단계 | 마감 | 담당 |
|---|---|---|
| 1. 본 계획서 팀원 리뷰 및 합의 | D+1 (5/22) | 전원 |
| 2. 각 파트 영어 스크립트 초안 | D+3 (5/24) | 각자 |
| 3. HTML 슬라이드 구조 골격 작성 | D+3 (5/24) | 손한주 |
| 4. 각 파트 슬라이드 콘텐츠 채우기 | D+5 (5/26) | 각자 |
| 5. 통합 + 디자인 톤 정리 | D+6 (5/27) | 손한주 |
| 6. 각자 영상 녹화 | D+8 (5/29) | 각자 |
| 7. 영상 편집 합본 | D+9 (5/30) | TBD |
| 8. 최종 점검 + 제출 | D+10 (5/31) | 전원 |

> 실제 제출 마감일이 정해지면 위 일정을 역산하여 조정한다.

---

## 8. 미정 사항 / 팀 합의 필요 항목

1. **발표 총 시간** — logistics PDF에 명시 없음. 통상 학부 그룹 프로젝트 15~20분 가정. 교수 공지 확인 필요.
2. **영상 편집 담당자** — 아직 미정.
3. **Reveal.js vs 자체 HTML** — 본 계획서는 자체 HTML 추천. 팀 합의 필요.
4. **섹션 헤더 슬라이드 삽입 여부** — 시간 여유에 따라 결정.
5. **기존 `presentation.html` 처리** — 본 계획에 따라 새로 만들 경우 기존 파일은 보존(`presentation_old.html`)할지 덮어쓸지 결정.
6. **각 사람 영상 길이 균형** — 4분씩 균등 분배가 기본이나, 손한주 파트(실측 데이터)는 청중에게 가장 인상적이므로 4분 30초까지 늘리는 안 검토.

---

## 9. 본 계획서의 검증 기준 (Self-Check)

- [x] logistics PDF의 권장 발표 구조 5단계와 매핑되는가
- [x] 각 발표자의 슬라이드가 연속된 블록으로 배치되어 영상 합본이 자연스러운가
- [x] 4명 모두 자신의 조사자료(PDF)를 그대로 활용 가능한가
- [x] 우리 팀의 *1차 데이터* (실측 벤치마크)가 발표의 클라이맥스로 배치되는가
- [x] 영어 비원어민 발표자가 무리 없이 소화 가능한 분량인가 (사람당 ≤ 6 슬라이드)
- [x] 청중이 사전 지식 없이도 따라올 수 있는 도입부가 있는가
- [x] 영문 발표 / 한글 Q&A 가이드라인을 반영하고 있는가
