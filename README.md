# QKD Network Emulation — Week 3  
## Post-Processing Layer Implementation

This branch extends the Week-2 QKD network emulation by introducing a post-processing layer, completing the logical QKD key pipeline before storage.

---

## Week-3 Objective

The objective of Week-3 is to simulate the QKD post-processing stage in a system-level manner, focusing on architecture, correctness, and key lifecycle management, rather than physical quantum simulation.

The following abstractions are implemented:

- Key sifting  
- Error filtering  
- Privacy amplification  
- Export of verified keys to the Remote KMS  

---

## System Overview

The system consists of three independent services:

| Component | Role | Port |
|---------|------|------|
| Central Controller | Control-plane routing abstraction | 8000 |
| Local KMS (IIT Roorkee) | Raw key generation and post-processing | 8001 |
| Remote KMS (IIT Jammu) | Independent validation and storage | 8002 |

---

## Key Lifecycle (Week-3)

