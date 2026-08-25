# 🚀 SAP CC Smart Data Access (SDA) & Grace Period HANA SQL Architecture

[![Database](https://img.shields.io/badge/Database-SAP%20HANA%202.0-0088CC?style=flat-square&logo=sap)](https://www.sap.com)
[![SAP CC](https://img.shields.io/badge/SAP%20CC-2023-005B94?style=flat-square)](https://www.sap.com)
[![SDA](https://img.shields.io/badge/SDA-Smart%20Data%20Access-success?style=flat-square)](https://www.sap.com)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

---

## 📑 Executive Overview

This repository contains the complete technical discovery, schema architecture, and production-ready **Pure Stored Database HANA SQL Query** for extracting **Grace Free Period Values**, **Allowance Types**, **Products**, **Sub-Products**, **Data Quota Balances (Counter Key 4)**, **Validity Dates**, **Operational Status**, and **Plan Amounts** from SAP Convergent Charging (SAP CC 2023) via Smart Data Access (SDA) virtual tables on SAP HANA.

---

## 🔬 Architectural Summary: Pure Stored Database Grace Period Values

1. **Migrated / Staging Contracts (`ZEL_ALLW_MIG`)**:
   - Stored directly in raw database column **`z.GRACE_FREE_DAYS`** (e.g. `3`, `8`, `78`).

2. **Active Rated SAP CC Allowance Counters (`CC_DEV_COUNTER`)**:
   - Stored under **`cnt_grace.COUN_KEY = 20`** (e.g. **`77`** for contract `61742`) linked to allowance via **`cnt_grace.HOLD_OID = allo.OID`**.

3. **Unrated / Expired Allowance Instances**:
   - If an allowance has no counter 20 balance and no migration row (e.g. Contract `682`), the stored value in the database is **`0`**.

---

## ⚡ Pure Stored Database SQL Query (Zero Date Calculations)

```sql
SELECT DISTINCT
    a.subscriber                          AS "SUBSCRIBER_ID",
    b.ext_id                              AS "CONTRACT_ID",
    c.coun_key                            AS "COUNTER_KEY",
    c.value                               AS "COUNTER_VALUE",
    c.hold_oid                            AS "HOLD_OID",
    COALESCE(z.ALLOWANCE_ID, CAST(allo.OID AS NVARCHAR)) AS "ALLOWANCE_OID",
    COALESCE(
        z.ALLOW_TYPE,
        CASE 
            WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '47524143455F465245455F504552494F44') > 0 THEN 'GRACE_FREE_PERIOD'
            WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '4D41494E545F434F4D4D495353494F4E') > 0 THEN 'MAINT_COMMISSION'
            WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '465454485F4241534943') > 0 THEN 'FTTH_BASIC'
            WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '42554646455F465245455F504552494F44') > 0 THEN 'BUFFER_PERIOD'
            WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '4155544F5F52454E4557414C5F464C4147') > 0 THEN 'AUTO_RENEWAL_FLAG'
            ELSE 'OTHER_ALLOWANCE'
        END
    )                                     AS "ALLOWANCE_TYPE",
    COALESCE(
        z.PRODUCT,
        CASE 
            WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '424153455F504C414E') > 0 THEN 'BASE_PLAN'
            WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '564153') > 0 THEN 'VAS'
            ELSE 'NA'
        END
    )                                     AS "PRODUCT",
    COALESCE(
        z.SUB_PRODUCT,
        CASE 
            WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '504152454E54414C5F434F4E54524F4C') > 0 THEN 'PARENTAL_CONTROL'
            WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '49505456') > 0 THEN 'IPTV'
            WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '4241534943') > 0 THEN 'BASIC'
            ELSE 'NA'
        END
    )                                     AS "SUB_PRODUCT",

    -- 🌟 PURE RAW STORED VALUES ONLY (ZERO DATE CALCULATIONS!)
    COALESCE(
        NULLIF(CAST(z.GRACE_FREE_DAYS AS INT), 0),
        NULLIF(CAST(cnt_grace.VALUE AS INT), 0),
        0
    )                                     AS "GRACE_FREE_PERIOD",

    COALESCE(z.VALIDITY_START_DT, CAST(allo.START_DATE AS NVARCHAR)) AS "VALIDITY_START_DATE",
    COALESCE(z.VALIDITY_END_DT, CAST(allo.END_DATE AS NVARCHAR))     AS "VALIDITY_END_DATE",
    COALESCE(evt.PLAN_PRICE_DECIMAL, 0)   AS "AMOUNT",
    b.op_status                           AS "CONTRACT_STATUS"

FROM SAPHANADB.CC_DEV_SUBSCRIBER_ACCOUNT a
JOIN SAPHANADB.CC_DEV_CACO b
    ON a.oid = b.suac_oid
JOIN SAPHANADB.CC_DEV_COUNTER c
    ON b.suac_oid = c.suac_oid
LEFT JOIN SAPHANADB.CC_DEV_CACO sub_caco
    ON b.oid = sub_caco.roco_oid
LEFT JOIN SAPHANADB.CC_DEV_ALLO allo 
    ON allo.caco_oid = b.oid OR allo.caco_oid = sub_caco.oid
LEFT JOIN SAPHANADB.CC_DEV_COUNTER cnt_grace 
    ON cnt_grace.HOLD_OID = allo.OID AND cnt_grace.COUN_KEY = 20
LEFT JOIN SAPHANADB.ZEL_ALLW_MIG z 
    ON (LTRIM(b.ext_id, '0') = LTRIM(z.VTREF, '0') OR LTRIM(sub_caco.ext_id, '0') = LTRIM(z.VTREF, '0'))
   AND allo.OID = z.ALLOWANCE_ID
LEFT JOIN (
    SELECT 
        CON_ID, 
        MAX(CAST(PLAN_PRICE AS DECIMAL(15,2))) AS PLAN_PRICE_DECIMAL
    FROM SAPHANADB.ZEL_EVENT_RAW
    WHERE EVENT_TYPE NOT LIKE '%COMMISSION%'
      AND PLAN_PRICE IS NOT NULL AND PLAN_PRICE <> '' 
      AND PLAN_PRICE NOT LIKE '%Infinity%'
      AND PLAN_PRICE NOT LIKE '%NaN%'
      AND PLAN_PRICE NOT LIKE '%BASIC%'
    GROUP BY CON_ID
) evt 
    ON LTRIM(b.ext_id, '0') = LTRIM(evt.CON_ID, '0') OR LTRIM(sub_caco.ext_id, '0') = LTRIM(evt.CON_ID, '0')

WHERE c.coun_key = 4

  -- 🌟 ENTER YOUR TARGET CONTRACT ID HERE:
  AND (
      LTRIM(b.ext_id, '0') = LTRIM('00000000000000061742', '0')
   OR LTRIM(sub_caco.ext_id, '0') = LTRIM('00000000000000061742', '0')
  )

ORDER BY "ALLOWANCE_OID";
```

---

## 📊 Benchmark Test Results (Pure Stored Values)

| CONTRACT_ID | ALLOWANCE_OID | ALLOWANCE_TYPE | **GRACE_FREE_PERIOD** | VALIDITY_START_DATE | VALIDITY_END_DATE |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`00000000000000000682`** | `390752371` | `GRACE_FREE_PERIOD` | **`0`** | `2026-06-10 17:25:49` | `2026-09-10 17:25:49` |
| **`00000000000000049260`** | `239339236` | `GRACE_FREE_PERIOD` | **`3`** | `2022-12-17 18:58:49` | `9999-12-31 00:00:00` |
| **`00000000000000061742`** | `395104028` | `GRACE_FREE_PERIOD` | **`77`** | `2026-08-20 15:39:52` | `2026-11-20 15:39:52` |

---

## 📁 Repository File Index

* [`SAP_CC_GRACE_PERIOD_DISCOVERY_STORY.md`](./SAP_CC_GRACE_PERIOD_DISCOVERY_STORY.md) - Full end-to-end technical story and architectural documentation.
* [`test_pure_stored_query_all_three.py`](./test_pure_stored_query_all_three.py) - Pure stored query test for contracts 61742, 49260, and 682.

---

## ✒️ Author
**Pranav Chandore**  
*SAP CC & HANA SDA Architecture Team*  
Repository: [PranavChandore/CC-SDA-SAP-HANA](https://github.com/PranavChandore/CC-SDA-SAP-HANA)
