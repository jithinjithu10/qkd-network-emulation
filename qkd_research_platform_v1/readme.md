# QKD Research Platform v1
## Adaptive Quantum Key Management System (Weeks 1–12)

This project implements a **research-grade Quantum Key Management System (KMS)** 
designed for QKD-enabled networks.

The system models realistic QKD classical control-plane behavior including:

- Buffer-first key architecture
- Adaptive policy control
- Quantum-quality filtering (QBER / entropy aware)
- Stress-mode simulations
- Real-time monitoring and visualization
- ETSI-style service abstraction

---

#  Research Goals

This platform is designed to experimentally evaluate:

- Buffer pressure impact on key allocation
- Adaptive quantum threshold tuning
- Key exhaustion behavior
- Policy mode switching (Baseline vs Adaptive vs Stress)
- Allocation latency trends
- System robustness under attack simulation

---

#  System Architecture

Application Layer  
    ↓  
Service Interface (FastAPI)  
    ↓  
Adaptive Policy Engine  
    ↓  
Q Buffer (READY Keys)  
    ↓  
S Buffer (Session-Reserved Keys)  
    ↓  
Persistent Storage (SQLite)  
    ↓  
Audit Logging  

---

#  Key Design Features

## 1️ Buffer-First Architecture
- QBuffer holds READY keys
- SBuffer holds session-reserved keys
- Memory-first for realistic QKD behavior
- SQLite used only for audit persistence

## 2️ Adaptive Policy Engine
Modes:
- BASELINE
- ADAPTIVE
- STRESS

Adaptive logic:
- Dynamically adjusts QBER threshold
- Dynamically adjusts entropy threshold
- Reacts to buffer pressure
- Detects exhaustion conditions

## 3️ Quantum-Aware Key Model
Each key stores:
- Bit Error Rate (QBER)
- Entropy score
- Amplification factor
- Link quality
- TTL
- Role (ENC / DEC)

## 4️ Stress Simulation
- Key exhaustion simulation
- Allocation pressure testing
- Failure-rate monitoring

## 5️ Live Monitoring
- Streamlit dashboard
- Real-time buffer metrics
- Policy threshold visualization
- Latency tracking

---