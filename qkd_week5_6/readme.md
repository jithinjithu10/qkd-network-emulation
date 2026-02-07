# QKD Key Management System – Week 4

This project implements a standalone Central Key Management System (KMS)
for managing cryptographic keys in a QKD-enabled network.

## Features
- Centralized KMS architecture
- Key lifecycle management (READY, CONSUMED, EXPIRED)
- Persistent storage using SQLite
- Audit logging for traceability
- Client–server deployment model

## Components
- kms_iitr.py : Central KMS (Server)
- kms_local.py : Local client
- models.py : Key lifecycle model
- storage.py : SQLite-based storage
- audit.py : Audit logging

## Running the System

### Server
