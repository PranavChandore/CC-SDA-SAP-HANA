# 🚀 SAP CC Smart Data Access (SDA) & Grace Period HANA SQL Architecture

[![Database](https://img.shields.io/badge/Database-SAP%20HANA%202.0-0088CC?style=flat-square&logo=sap)](https://www.sap.com)
[![SAP CC](https://img.shields.io/badge/SAP%20CC-2023-005B94?style=flat-square)](https://www.sap.com)
[![SDA](https://img.shields.io/badge/SDA-Smart%20Data%20Access-success?style=flat-square)](https://www.sap.com)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

---

## 📑 Executive Overview

This repository contains the complete technical discovery, schema architecture, and production-ready **Universal Master SAP HANA SQL Query** for extracting **Grace Free Period Values**, **Allowance Amounts (e.g. `921971833`)**, **Allowance Types**, **Products**, **Sub-Products**, **Data Quota Balances**, **Validity Dates**, **Operational Status**, and **Plan Amounts** from SAP Convergent Charging (SAP CC 2023) via Smart Data Access (SDA) virtual tables on SAP HANA.

---

## 🔬 Architectural Discovery: Allowance Counter Mapping (`CC_DEV_COUNTER`)

Each Allowance Plan in SAP CC Core Tool GUI (e.g., Allowance `4064002`) maintains its counters inside **`SAPHANADB.CC_DEV_COUNTER`** linked via **`HOLD_OID = ALLO.OID`**:

| Counter Name in SAP CC GUI | `COUN_KEY` in `CC_DEV_COUNTER` | Sample Value (`Allowance 4064002`) |
| :--- | :--- | :--- |
| **`Amount`** | **`COUN_KEY = 4`** | **`921971833`** |
| **`STATUS_FLAG`** | **`COUN_KEY = 5`** | **`0`** |
| **`RENEWAL_START_DATE`** | **`COUN_KEY = 6`** | **`0`** |
| **`AUTO_RENEWAL_FLAG`** | **`COUN_KEY = 7`** | **`0`** |
| **`GRACE_FREE_PERIOD`** | **`COUN_KEY = 8` / `20`** | **`0` / `77`** |
| **`GRACE_PERIOD`** | **`COUN_KEY = 9`** | **`0`** |
| **`COMMITMENT_FULFILLED`** | **`COUN_KEY = 10`** | **`0`** |

---

## ⚡ Master Production HANA SQL Query (Exact Match for SAP CC GUI)

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

    -- 🌟 ALLOWANCE COUNTER AMOUNT (EXACT MATCH FOR GUI SCREENSHOT: 921971833)
    COALESCE(CAST(cnt_amt.VALUE AS DECIMAL(15,2)), evt.PLAN_PRICE_DECIMAL, 0) AS "AMOUNT",
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
LEFT JOIN SAPHANADB.CC_DEV_COUNTER cnt_amt
    ON cnt_amt.HOLD_OID = allo.OID AND cnt_amt.COUN_KEY = 4
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

  -- 🌟 ENTER TARGET CONTRACT ID HERE:
  AND (
      LTRIM(b.ext_id, '0') = LTRIM('00000000000000000697', '0')
   OR LTRIM(sub_caco.ext_id, '0') = LTRIM('00000000000000000697', '0')
  )

ORDER BY "ALLOWANCE_OID";
```

---

## 📊 Exact Match Verification Result (`Contract 00000000000000000697`)

| SUBSCRIBER_ID | CONTRACT_ID | ALLOWANCE_OID | ALLOWANCE_TYPE | **AMOUNT** | **GRACE_FREE_PERIOD** | **CONTRACT_STATUS** |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`0000000911`** | **`00000000000000000697`** | **`4064002`** | `OTHER_ALLOWANCE` | **`921971833`** | **`0`** | **`0`** |

---

## 📁 Repository File Index

* [`SAP_CC_GRACE_PERIOD_DISCOVERY_STORY.md`](./SAP_CC_GRACE_PERIOD_DISCOVERY_STORY.md) - Full end-to-end technical story and architectural documentation.
* [`test_contract_697_amount_fix.py`](./test_contract_697_amount_fix.py) - Script verifying Allowance Counter Amount 921971833 for Contract 697.

---

## ✒️ Author
**Pranav Chandore**  
*SAP CC & HANA SDA Architecture Team*  
Repository: [PranavChandore/CC-SDA-SAP-HANA](https://github.com/PranavChandore/CC-SDA-SAP-HANA)
