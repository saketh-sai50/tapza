# Tapza MVP — Local Setup & Verification Guide

This guide explains how to run, test, and demonstrate the Tapza Pharmacy Management and Medicine Ordering MVP.

---

## 1. System Architecture Summary

- **Backend**: Python 3.10+ with Flask REST API
- **Database**: SQLite 3 with Write-Ahead Logging (`WAL` mode) and atomic `BEGIN IMMEDIATE` transaction locking
- **Frontend**: Expo React Native (TypeScript, Expo Router, Expo Web)
- **Roles**: Customer, Pharmacy, Admin
- **Zones Supported**: `Warangal`, `Hanamkonda`, `Kazipet`

---

## 2. Seeded Test Credentials

### 2.1 Administrator
- **Email**: `admin@tapza.com`
- **Password**: `Admin@123`
- **Role**: `ADMIN`
- **Permissions**: Platform metrics, Excel catalogue imports, pharmacy status toggles, zone reassignment, global order audit.

### 2.2 Customer Demo Account
- **Email**: `warangal.customer@example.com`
- **Password**: `CustomerPass@123`
- **Zone**: `Warangal`
- *(Customers can also register fresh accounts with any email and select Warangal, Hanamkonda, or Kazipet).*

### 2.3 45 Seeded Zone-Wise Pharmacies
All 45 pharmacies from your test dataset are seeded and active. You can log in using either the **Username** or **Email** (`<username>@tapza.com`):

#### Warangal Zone (15 Pharmacies)
| Pharmacy Name | Username | Password | Phone |
| :--- | :--- | :--- | :--- |
| Sri Lakshmi Care Pharmacy | `testpharm001` | `testpharm@001` | 9000000001 |
| Green Cross Medicals | `testpharm002` | `testpharm@002` | 9000000002 |
| CityWell Pharmacy | `testpharm003` | `testpharm@003` | 9000000003 |
| Aarogya Plus Medical Store | `testpharm004` | `testpharm@004` | 9000000004 |
| People's Health Pharmacy | `testpharm005` | `testpharm@005` | 9000000005 |
| MediBridge Medicals | `testpharm006` | `testpharm@006` | 9000000006 |
| Sunrise Family Pharmacy | `testpharm007` | `testpharm@007` | 9000000007 |
| CarePoint Medicals | `testpharm008` | `testpharm@008` | 9000000008 |
| Vijaya Wellness Pharmacy | `testpharm009` | `testpharm@009` | 9000000009 |
| TrustCare Medical Store | `testpharm010` | `testpharm@010` | 9000000010 |
| PrimeLife Pharmacy | `testpharm011` | `testpharm@011` | 9000000011 |
| HealthNest Medicals | `testpharm012` | `testpharm@012` | 9000000012 |
| MedSpring Pharmacy | `testpharm013` | `testpharm@013` | 9000000013 |
| WellLeaf Medical Store | `testpharm014` | `testpharm@014` | 9000000014 |
| CareSquare Pharmacy | `testpharm015` | `testpharm@015` | 9000000015 |

#### Hanamkonda Zone (15 Pharmacies)
| Pharmacy Name | Username | Password | Phone |
| :--- | :--- | :--- | :--- |
| Hanamkonda Health Hub | `testpharm016` | `testpharm@016` | 9000000016 |
| BlueCross Medicals | `testpharm017` | `testpharm@017` | 9000000017 |
| FamilyFirst Pharmacy | `testpharm018` | `testpharm@018` | 9000000018 |
| ... | ... | ... | ... |
| VitalCare Pharmacy | `testpharm030` | `testpharm@030` | 9000000030 |

#### Kazipet Zone (15 Pharmacies)
| Pharmacy Name | Username | Password | Phone |
| :--- | :--- | :--- | :--- |
| Kazipet Care Pharmacy | `testpharm031` | `testpharm@031` | 9000000031 |
| MediTrust Medicals | `testpharm032` | `testpharm@032` | 9000000032 |
| HealthBridge Pharmacy | `testpharm033` | `testpharm@033` | 9000000033 |
| ... | ... | ... | ... |
| PrimeCare Pharmacy | `testpharm045` | `testpharm@045` | 9000000045 |

---

## 3. How to Run the Backend

Open a PowerShell terminal in the project directory:

```powershell
# 1. Activate workspace virtual environment
.\backend\.venv\Scripts\Activate.ps1

# 2. Run Flask REST API
python backend\run.py
```

The REST API will start on `http://127.0.0.1:5000`.

- Health check: `http://127.0.0.1:5000/api/health`
- Medicines catalogue: `http://127.0.0.1:5000/api/medicines`

---

## 4. How to Run the Automated Test Suites

All tests run against the database and REST endpoints:

```powershell
# Run the complete CEO two-way communication workflow:
python backend\test_user_exact_flow.py

# Run comprehensive E2E and security verification:
python backend\test_stage9_e2e_security.py
```

---

## 5. Walkthrough of Your Exact Testing Workflow

### Step 1: Customer Places an Order in Warangal
1. Log in as a Customer (or register a new Customer selecting `Warangal` as your zone).
2. Browse medicines (e.g. Paracetamol, Amoxicillin), add to cart.
3. Review cart, set your delivery address in Warangal, and click **Start 4-Minute Broadcast**.
4. The 4-minute timer starts ticking down. The order is automatically broadcast to all 15 pharmacies in Warangal!

### Step 2: Log into Pharmacy 1 (`testpharm001`)
1. Log out or open an incognito window.
2. Log in with:
   - **Username**: `testpharm001`
   - **Password**: `testpharm@001`
3. In the **Broadcasts** radar, you will see the incoming order with the live 4-minute countdown.
4. Click **Submit Quote &rarr;**.
5. Toggle item availability switches (e.g. mark both medicines "In Stock"), quote your prices, and click **Submit Quote**.

### Step 3: Log into Pharmacy 2 (`testpharm002`)
1. Log in with:
   - **Username**: `testpharm002`
   - **Password**: `testpharm@002`
2. View the same order in the Broadcasts radar.
3. Click **Submit Quote &rarr;**.
4. Mark Item 1 "In Stock" at a discounted price, and toggle Item 2 to **"Out of Stock"**.
5. Notice that Item 2's subtotal becomes **$0.00**. Click **Submit Quote** to send a Partial Quote.

### Step 4: Log back into Customer Account
1. Open notifications: you will see alerts from both `Sri Lakshmi Care Pharmacy` and `Green Cross Medicals`.
2. Open the order details screen:
   - See both quotes side-by-side.
   - Pharmacy 1 has a green **FULL FULFILLMENT** badge ($465.00).
   - Pharmacy 2 has an amber **PARTIAL FULFILLMENT** badge ($140.00), showing Item 2 crossed out and strictly billed at $0.00.
3. Click **Select Pharmacy** on Pharmacy 1 (Sri Lakshmi Care).
4. The transaction executes atomically: Pharmacy 1 is awarded, Pharmacy 2's quote is marked rejected, and the order is locked.

### Step 5: Pharmacy 1 Receives Award Notification and Confirms
1. Log back in as `testpharm001`.
2. In notifications: *"Customer selected your quote for Order #{id}. Please review and confirm dispatch."*
3. In **Orders**, open the pending order and click **Confirm Order**.
4. Progress the order through **Start Preparing** &rarr; **Dispatch Order** &rarr; **Mark Delivered**.
5. The customer receives notifications at each step, and can perform a simulated mock payment.
