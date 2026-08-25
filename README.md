# 🚀 SAP CC Smart Data Access (SDA) & Grace Period HANA SQL Architecture

[![Database](https://img.shields.io/badge/Database-SAP%20HANA%202.0-0088CC?style=flat-square&logo=sap)](https://www.sap.com)
[![SAP CC](https://img.shields.io/badge/SAP%20CC-2023-005B94?style=flat-square)](https://www.sap.com)
[![SDA](https://img.shields.io/badge/SDA-Smart%20Data%20Access-success?style=flat-square)](https://www.sap.com)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

---

## 📑 Executive Overview

This repository contains the complete technical discovery, schema architecture, and production-ready **Pure Database Table Fetch Query** (Zero Calculations) for extracting **Pre-Stored Grace Free Period Values**, **Allowance Types**, **Products**, **Sub-Products**, **Data Quota Balances (Counter Key 4)**, **Validity Dates**, **Operational Status**, and **Plan Amounts** directly from SAP HANA database tables.

---

## 🏛️ Exact Pre-Stored Database Table Location

| Requested Field | Database Table | Raw Stored Column (Zero Calculation) |
| :--- | :--- | :--- |
| **Subscriber Account** | `SAPHANADB.CC_DEV_SUBSCRIBER_ACCOUNT` | `a.subscriber` |
| **Charging Contract** | `SAPHANADB.CC_DEV_CACO` | `b.ext_id` |
| **Quota Counter Balance** | `SAPHANADB.CC_DEV_COUNTER` | `c.value (coun_key = 4)` |
| **Hold Identifier** | `SAPHANADB.CC_DEV_COUNTER` | `c.hold_oid` |
| **Allowance Instance OID** | `SAPHANADB.ZEL_ALLW_MIG` | `z.ALLOWANCE_ID` |
| **Allowance Type** | `SAPHANADB.ZEL_ALLW_MIG` | `z.ALLOW_TYPE` |
| **Product Name** | `SAPHANADB.ZEL_ALLW_MIG` | `z.PRODUCT` |
| **Sub-Product Name** | `SAPHANADB.ZEL_ALLW_MIG` | `z.SUB_PRODUCT` |
| **Pre-Stored Grace Period** | **`SAPHANADB.ZEL_ALLW_MIG`** | **`z.GRACE_FREE_DAYS`** |
| **Validity Dates** | `SAPHANADB.ZEL_ALLW_MIG` | `z.VALIDITY_START_DT`, `z.VALIDITY_END_DT` |

---

## ⚡ Pure Direct Database Table Select Query (Zero Calculations)

```sql
SELECT DISTINCT
    a.subscriber                          AS "SUBSCRIBER_ID",
    b.ext_id                              AS "CONTRACT_ID",
    c.coun_key                            AS "COUNTER_KEY",
    c.value                               AS "COUNTER_VALUE",
    c.hold_oid                            AS "HOLD_OID",
    z.ALLOWANCE_ID                        AS "ALLOWANCE_OID",
    z.ALLOW_TYPE                          AS "ALLOWANCE_TYPE",
    z.PRODUCT                             AS "PRODUCT",
    z.SUB_PRODUCT                         AS "SUB_PRODUCT",

    -- 🌟 PURE RAW STORED COLUMN FETCH FROM DATABASE TABLE (ZERO CALCULATION!)
    CAST(z.GRACE_FREE_DAYS AS INT)        AS "GRACE_FREE_PERIOD",

    z.VALIDITY_START_DT                   AS "VALIDITY_START_DATE",
    z.VALIDITY_END_DT                     AS "VALIDITY_END_DATE",
    CAST(z.AMOUNT AS DECIMAL(15,2))       AS "AMOUNT",
    z.STATUS_FLAG                         AS "CONTRACT_STATUS"

FROM SAPHANADB.CC_DEV_SUBSCRIBER_ACCOUNT a
JOIN SAPHANADB.CC_DEV_CACO b
    ON a.oid = b.suac_oid
JOIN SAPHANADB.CC_DEV_COUNTER c
    ON b.suac_oid = c.suac_oid
JOIN SAPHANADB.ZEL_ALLW_MIG z 
    ON LTRIM(b.ext_id, '0') = LTRIM(z.VTREF, '0')
WHERE c.coun_key = 4
  AND CAST(z.GRACE_FREE_DAYS AS INT) > 0
ORDER BY b.ext_id, z.ALLOWANCE_ID;
```

---

## 📁 Repository File Index

* [`SAP_CC_GRACE_PERIOD_DISCOVERY_STORY.md`](./SAP_CC_GRACE_PERIOD_DISCOVERY_STORY.md) - Full end-to-end technical story and architectural documentation.
* [`test_no_calc_pure_table_fetch.py`](./test_no_calc_pure_table_fetch.py) - Python script executing pure direct database table select from ZEL_ALLW_MIG for GRACE_FREE_DAYS without calculations.

---

## ✒️ Author
**Pranav Chandore**  
*SAP CC & HANA SDA Architecture Team*  
Repository: [PranavChandore/CC-SDA-SAP-HANA](https://github.com/PranavChandore/CC-SDA-SAP-HANA)
