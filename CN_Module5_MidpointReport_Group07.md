# Computer Networks - Module 5 Midpoint Report

## Group 07

---

## 1. Project Overview

### 1.1 Introduction

The financial markets have evolved dramatically over the past decades, with High-Frequency Trading (HFT) emerging as a dominant force in modern electronic markets. HFT firms leverage advanced technologies to execute trades in microseconds, capitalizing on minute price discrepancies across different trading venues. At the heart of this technological arms race lies the choice of network protocol - a decision that can mean the difference between profitable trades and missed opportunities.

This project investigates a fundamental question in network protocol design for trading systems: **How does the choice between TCP and UDP affect the latency performance of a high-frequency trading system?**

### 1.2 Motivation

In high-frequency trading, every microsecond matters. Trading firms invest millions in co-location services, specialized hardware, and network optimization to gain even the slightest edge. The network protocol layer represents a critical decision point in this optimization process:

- **TCP** provides reliable, ordered delivery with built-in congestion control, but introduces overhead through acknowledgment mechanisms, retransmissions, and head-of-line blocking.

- **UDP** offers minimal overhead and lower potential latency by eliminating the reliability mechanisms, but requires application-layer implementations for reliability and ordering.

Understanding the practical implications of these trade-offs is essential for designing efficient trading systems.

### 1.3 Objectives

The primary objectives of this research are:

1. To measure and compare the end-to-end latency of TCP and UDP in a simulated HFT environment
2. To analyze the factors contributing to latency differences between the two protocols
3. To provide empirical insights for practitioners making protocol selection decisions

---

## 2. System Architecture

### 2.1 Architecture Overview

The system architecture follows a client-server model designed to simulate a simplified high-frequency trading environment. The architecture consists of two primary components:

- **HFT Server**: Handles order processing, order book management, and order matching
- **HFT Client**: Generates test orders and measures end-to-end latency

The client and server communicate over both TCP and UDP protocols, allowing for direct comparison of latency performance under identical conditions.

### 2.2 Server Components

#### 2.2.1 Order Book

The order book maintains the current state of limit orders for each trading symbol. It supports:

- Adding new orders to the appropriate side (bid/ask)
- Canceling existing orders
- Matching orders when price-time priority conditions are met
- Maintaining aggregated price levels for efficient market data

#### 2.2.2 Order Handler

The order handler processes incoming orders and generates responses. It includes:

- **Order Validator**: Validates order parameters (symbol, price, quantity, order type)
- **Order Processor**: Executes valid orders against the order book
- **Response Generator**: Creates standardized order response messages

#### 2.2.3 Matching Engine

The matching engine implements a price-time priority matching algorithm:

1. Orders are matched when the bid price meets or exceeds the ask price
2. At the same price level, earlier orders have priority
3. Partial fills are supported when the matching quantity is insufficient

### 2.3 Client Components

#### 2.3.1 Benchmark Engine

The benchmark engine orchestrates the latency measurement process:

- Configurable number of warmup orders to stabilize performance
- Configurable number of test orders for statistical analysis
- Configurable order interval to simulate realistic trading patterns

#### 2.3.2 Latency Measurement

The client measures round-trip time (RTT) for each order:

1. Client sends an order and records the send timestamp
2. Server processes the order and sends back a response
3. Client receives the response and records the receive timestamp
4. RTT is calculated as the difference between timestamps

#### 2.3.3 Results Analysis

The benchmark generates comprehensive statistics including:

- Mean, median, and percentile latencies
- Minimum and maximum latencies
- Standard deviation and variance

---

## 3. Protocol Implementation

### 3.1 TCP Implementation

The TCP implementation focuses on minimizing latency through several optimizations:

- **TCP_NODELAY**: Disable Nagle's algorithm to send packets immediately without waiting for full segments
- **Socket Timeout**: Appropriate timeout values to detect connection issues quickly
- **Buffer Sizing**: Large send and receive buffers for high-throughput scenarios

The TCP server accepts connections and processes each client in a separate thread, allowing concurrent order processing.

### 3.2 UDP Implementation

The UDP implementation prioritizes minimal overhead:

- **No Connection State**: Eliminates connection establishment overhead
- **Direct Send/Receive**: Application directly sends and receives datagrams
- **Minimal Header**: 8-byte UDP header vs. 20+ byte TCP header

The UDP server uses a single thread with non-blocking receive to handle multiple clients.

### 3.3 Protocol Comparison

| Feature | TCP | UDP |
|---------|-----|-----|
| Reliability | Guaranteed | Best-effort |
| Ordering | Ordered | None |
| Congestion Control | Yes | No |
| Connection State | Required | None |
| Header Overhead | 20+ bytes | 8 bytes |
| Latency Potential | Higher | Lower |
| Implementation Complexity | Lower | Higher |

---

## 4. Testing Methodology

### 4.1 Test Configuration

The benchmark uses the following configuration:

- **Warmup Orders**: 100 orders to warm up caches and stabilize performance
- **Test Orders**: 10,000 orders for statistical significance
- **Order Interval**: 100 microseconds between orders
- **Symbols**: BTC-USD, ETH-USD, AAPL

### 4.2 Test Parameters

Each test order includes:

- Random symbol selection from configured symbols
- Random side (buy/sell)
- Random price within a realistic range
- Random quantity within configured limits

### 4.3 Measurement Process

The measurement process follows these steps:

1. **Warmup Phase**: 100 orders sent to stabilize system state
2. **Test Phase**: 10,000 orders sent with precise timing
3. **Analysis Phase**: Statistical analysis of collected latencies

### 4.4 Performance Metrics

The following metrics are collected and analyzed:

- **Mean Latency**: Average round-trip time
- **Median Latency**: 50th percentile latency
- **P95 Latency**: 95th percentile latency
- **P99 Latency**: 99th percentile latency
- **Min/Max Latency**: Extreme values
- **Standard Deviation**: Variability in latency

---

## 5. Expected Results

### 5.1 Anticipated Observations

Based on protocol characteristics, we expect:

1. **UDP to show lower average latency** due to:
   - No connection establishment overhead
   - No retransmission handling
   - No head-of-line blocking
   - Smaller header size

2. **TCP to show more consistent latency** due to:
   - Built-in congestion control
   - Reliability mechanisms
   - Less susceptible to packet loss effects

3. **Protocol performance to converge under high load** as:
   - TCP's congestion control stabilizes
   - Network conditions become the limiting factor

### 5.2 Implications for HFT Systems

The results will inform protocol selection decisions for trading system architects:

- Low-latency requirements may favor UDP with application-layer reliability
- Reliability-critical applications may prefer TCP with optimizations
- Hybrid approaches may offer optimal balance for specific use cases

---

## 6. Conclusion

This project provides empirical insights into the latency characteristics of TCP and UDP in high-frequency trading contexts. By implementing both protocols in a controlled environment and measuring their performance under identical conditions, we aim to quantify the practical implications of protocol choice.

The findings will contribute to the understanding of network protocol performance in time-critical financial applications and provide guidance for system architects making protocol selection decisions.

---

## References

1. Academic literature on High-Frequency Trading
2. RFC 793 - Transmission Control Protocol
3. RFC 768 - User Datagram Protocol
4. Industry best practices for low-latency trading systems

---

**Course**: Computer Networks (CN)  
**Module**: Module 5 - Midpoint Report  
**Group**: Group 07  
**Date**: 2026