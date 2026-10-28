# Tapza — Full-Stack Pharmacy Management & Medicine Ordering Platform

Tapza is an on-demand full-stack medicine ordering and pharmacy management platform built from scratch with Python Flask, SQLite (WAL mode with concurrency transaction protection), and Expo React Native / Web.

---

## Key Features

1. **Server-Enforced 4-Minute Broadcast Window**: Server-authoritative timer rejecting submissions past expiry (HTTP 410).
2. **Atomic Single-Pharmacy Selection**: ACID transaction with `BEGIN IMMEDIATE` row-locking preventing duplicate winner allocations (concurrency tested).
3. **Item-Level Pricing & Zero-Charge Guarantee**: Preserves original catalogue MRP. Unavailable items in partial quotes are strictly billed at $0.00.
4. **Mandatory Two-Way Communication**: Real-time notifications and state updates across Customers, Pharmacies, and Admins.
5. **Rejection Recovery Workflow**: If an awarded pharmacy rejects, the backend automatically re-opens the order to `PENDING_SELECTION` so the customer can award an alternative quote.
6. **45 Pre-Seeded Zone-Wise Pharmacies**: 15 in Warangal, 15 in Hanamkonda, 15 in Kazipet with usernames `testpharm001` through `testpharm045`.
7. **Validated Excel Importers**: Bulk onboarding for medicines and pharmacies with row-level validation.
8. **Simulated Mock Payment**: Explicitly labelled test payment simulation modal and endpoint.

---

## Documentation

- [Architecture Specification](docs/ARCHITECTURE.md)
- [Setup & Verification Guide](docs/SETUP_GUIDE.md)

---

## Quick Start

```powershell
# Run backend server
.\backend\.venv\Scripts\Activate.ps1
python backend\run.py

# Run exact user workflow verification
python backend\test_user_exact_flow.py
```
