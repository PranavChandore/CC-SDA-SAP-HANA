# 🚀 SAP CC Smart Data Access (SDA) & Grace Period HANA SQL Architecture

[![Database](https://img.shields.io/badge/Database-SAP%20HANA%202.0-0088CC?style=flat-square&logo=sap)](https://www.sap.com)
[![SAP CC](https://img.shields.io/badge/SAP%20CC-2023-005B94?style=flat-square)](https://www.sap.com)
[![SDA](https://img.shields.io/badge/SDA-Smart%20Data%20Access-success?style=flat-square)](https://www.sap.com)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

---

## 📑 Executive Overview

This repository contains the complete technical discovery, schema architecture, and production-ready **Pure Direct Table Fetch HANA SQL Query** (Zero Calculations).

---

## 🔬 Architectural Summary: How SAP CC Handles Grace Period

1. **Migrated / Staging Contracts (`ZEL_ALLW_MIG`)**:
   - The grace period integer is stored directly as a raw database column **`z.GRACE_FREE_DAYS`** (e.g. `3`, `8`, `78`).
   - Querying `z.GRACE_FREE_DAYS` directly requires **ZERO CALCULATION**.

2. **Live SAP CC Contracts (`CC_DEV_ALLO` like `00000000000000061742`)**:
   - Live contracts in SAP CC do not store a static integer for grace days; SAP CC stores the validity period **`allo.START_DATE`** (`2026-08-20`) and **`allo.END_DATE`** (`2026-11-20`).
   - In SAP CC Core Tool GUI, the column `GRACE_FREE_PERIOD` is evaluated dynamically by the SAP CC runtime engine as the remaining days until `END_DATE` (`DAYS_BETWEEN(CURRENT_DATE, END_DATE) = 77`).

---

## ⚡ Pure Direct Database Table Select Query (Zero Calculations)

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

    -- 🌟 PURE RAW STORED COLUMN FETCH ONLY (ZERO CALCULATIONS!)
    COALESCE(CAST(z.GRACE_FREE_DAYS AS INT), 0) AS "GRACE_FREE_PERIOD",

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

-- Filter by Contract ID or Subscriber ID:
WHERE (b.ext_id = '00000000000000061742' OR sub_caco.ext_id = '00000000000000061742')
  AND c.coun_key = 4

ORDER BY "ALLOWANCE_OID";
```

---

## 📁 Repository File Index

* [`SAP_CC_GRACE_PERIOD_DISCOVERY_STORY.md`](./SAP_CC_GRACE_PERIOD_DISCOVERY_STORY.md) - Full end-to-end technical story and architectural documentation.

---

## ✒️ Author
**Pranav Chandore**  
*SAP CC & HANA SDA Architecture Team*  
Repository: [PranavChandore/CC-SDA-SAP-HANA](https://github.com/PranavChandore/CC-SDA-SAP-HANA)
