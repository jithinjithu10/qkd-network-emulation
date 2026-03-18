# QKD Key Management System (KMS) – Weeks 4–6 Implementation

This project implements a Centralized Key Management System (KMS) 
for a QKD-enabled network architecture.

The system models realistic QKD classical control-plane behavior 
including buffering, lifecycle enforcement, policy control, and 
role-based key separation.

---

## Week 4 – Core KMS Architecture

Implemented:
- Centralized KMS (ETSI-style service exposure)
- Key lifecycle management (GENERATED → READY → RESERVED → CONSUMED → EXPIRED)
- Persistent storage using SQLite
- Audit logging with UTC timestamps
- Client–server deployment model (FastAPI-based REST APIs)

Key APIs:
- GET_STATUS
- KEY GENERATION
- KEY ALLOCATION
- KEY CONSUMPTION

---

## Week 5 – Advanced Key Storage and Buffering

Implemented:
- Q Buffer (Generated/Ready key pool)
- S Buffer (Session-reserved key pool)
- ENC / DEC role-based key separation
- TTL-based expiry enforcement
- Persistent lifecycle transitions
- Role-aware key selection

Architecture Model:
- Q Buffer → Holds available keys
- S Buffer → Holds session-reserved keys
- Database-backed storage for reliability

---

## Week 6 – Policy-Driven KMS

Implemented:
- Per-application key usage limits
- Freshness-based key filtering
- TTL validation before allocation
- Adaptive refill threshold logic
- Role-aware refill decisions
- Session-level quota enforcement

Policy Engine Responsibilities:
- Prevent excessive key usage
- Reject stale/expired keys
- Trigger refill when buffer drops below threshold

---

## Current System Architecture

Application Layer
    ↓
Service Interface Layer (FastAPI APIs)
    ↓
Policy Engine
    ↓
Q / S Buffers
    ↓
Persistent Storage (SQLite)
    ↓
Audit Logging

---

## Components

- `kms_iitr.py` → Central KMS (Server)
- `kms_local.py` → Client / Application Interface
- `models.py` → Key model, lifecycle states, role definitions
- `storage.py` → SQLite persistent storage
- `buffers.py` → In-memory Q/S buffers
- `policy.py` → Policy engine
- `audit.py` → Append-only audit logging

---

## Running the System

### Start Server

```bash
uvicorn kms_iitr:app --host 0.0.0.0 --port 8001
