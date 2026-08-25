# 🚀 SAP CC Smart Data Access (SDA) & Grace Period HANA SQL Architecture

[![Database](https://img.shields.io/badge/Database-SAP%20HANA%202.0-0088CC?style=flat-square&logo=sap)](https://www.sap.com)
[![SAP CC](https://img.shields.io/badge/SAP%20CC-2023-005B94?style=flat-square)](https://www.sap.com)
[![SDA](https://img.shields.io/badge/SDA-Smart%20Data%20Access-success?style=flat-square)](https://www.sap.com)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

---

## 📑 Executive Overview

This repository contains the complete technical discovery, schema architecture, and production-ready **Dynamic Master SAP HANA SQL Query** for extracting **Grace Free Period Values (Dynamically Computed for Every Customer)**, **Allowance Types**, **Products**, **Sub-Products**, **Data Quota Balances (Counter Key 4)**, **Validity Dates**, and **Plan Fees** from SAP Convergent Charging (SAP CC 2023) via Smart Data Access (SDA) virtual tables on SAP HANA.

---

## 🌟 Why Hardcoding `THEN 77` is Incorrect & Why Dynamic `DAYS_BETWEEN` is Required

Hardcoding `THEN 77` inside a `CASE` statement is flawed because different customers have different configured grace periods (e.g., 14 days, 30 days, 60 days, 92 days, or 1,004 days).

### 🔬 Empirical Database Evidence Across Multiple Customers:
- **Contract `00000000000000061742`**: `START_DATE` = `2026-08-20`, `END_DATE` = `2026-11-20` $\rightarrow$ **`92` Grace Days**
- **Contract `00000000000000053642`**: `START_DATE` = `2024-01-19`, `END_DATE` = `2026-10-19` $\rightarrow$ **`1,004` Grace Days**

Using `DAYS_BETWEEN(CAST(allo.START_DATE AS DATE), CAST(allo.END_DATE AS DATE))` guarantees that **every customer gets their exact dynamic grace period value directly from the database without any hardcoded values**.

---

## ⚡ Production Dynamic HANA SQL Query (Zero Hardcoding)

```sql
SELECT DISTINCT
    sa.SUBSCRIBER                         AS "SUBSCRIBER_ID",
    caco.EXT_ID                           AS "CONTRACT_ID",
    caco.OID                              AS "CONTRACT_OID",
    root_caco.EXT_ID                      AS "ROOT_CONTRACT_ID",
    allo.OID                              AS "ALLOWANCE_OID",
    CASE 
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '47524143455F465245455F504552494F44') > 0 THEN 'GRACE_FREE_PERIOD'
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '4D41494E545F434F4D4D495353494F4E') > 0 THEN 'MAINT_COMMISSION'
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '465454485F4241534943') > 0 THEN 'FTTH_BASIC'
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '4255464645525F504552494F44') > 0 THEN 'BUFFER_PERIOD'
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '4155544F5F52454E4557414C5F464C4147') > 0 THEN 'AUTO_RENEWAL_FLAG'
        ELSE 'OTHER_ALLOWANCE'
    END                                   AS "ALLOWANCE_TYPE",
    CASE 
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '424153455F504C414E') > 0 THEN 'BASE_PLAN'
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '564153') > 0 THEN 'VAS'
        ELSE 'NA'
    END                                   AS "PRODUCT",
    CASE 
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '504152454E54414C5F434F4E54524F4C') > 0 THEN 'PARENTAL_CONTROL'
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '49505456') > 0 THEN 'IPTV'
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '4241534943') > 0 THEN 'BASIC'
        ELSE 'NA'
    END                                   AS "SUB_PRODUCT",

    -- 1. Dynamic Grace Free Period Value in Days (Directly Computed for Every Customer)
    CASE 
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '47524143455F465245455F504552494F44') > 0 
         AND YEAR(allo.END_DATE) < 2099
        THEN DAYS_BETWEEN(CAST(allo.START_DATE AS DATE), CAST(allo.END_DATE AS DATE))
        ELSE 0
    END                                   AS "GRACE_FREE_PERIOD_VALUE",

    -- 2. Dynamic Remaining Grace Days Countdown
    CASE 
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '47524143455F465245455F504552494F44') > 0 
         AND YEAR(allo.END_DATE) < 2099
        THEN GREATEST(0, DAYS_BETWEEN(CURRENT_DATE, CAST(allo.END_DATE AS DATE)))
        ELSE 0
    END                                   AS "GRACE_REMAINING_DAYS",

    allo.START_DATE                       AS "VALIDITY_START_DATE",
    allo.END_DATE                         AS "VALIDITY_END_DATE",
    COALESCE(
        NULLIF(m.VARIANT_NAME, ''), 
        NULLIF(evt.CUST_PLAN_NAME, ''), 
        'BASIC'
    )                                     AS "PLAN_NAME",
    COALESCE(evt.PLAN_PRICE_DECIMAL, 0)   AS "AMOUNT",
    COALESCE(cnt.VALUE, 0)                AS "COUNTER_4_VALUE",
    caco.OP_STATUS                        AS "CONTRACT_STATUS"
FROM SAPHANADB.CC_DEV_CACO caco
JOIN SAPHANADB.CC_DEV_SUBSCRIBER_ACCOUNT sa 
    ON sa.OID = caco.SUAC_OID
JOIN SAPHANADB.CC_DEV_CACO root_caco 
    ON caco.ROCO_OID = root_caco.OID
LEFT JOIN SAPHANADB.CC_DEV_ALLO allo 
    ON allo.CACO_OID = caco.OID OR allo.CACO_OID = root_caco.OID
LEFT JOIN SAPHANADB.CC_DEV_COUNTER cnt 
    ON cnt.SUAC_OID = sa.OID AND cnt.COUN_KEY = 4
LEFT JOIN SAPHANADB.ZVEL_CS_MASTER(CURRENT_DATE, CURRENT_TIME) m 
    ON LTRIM(caco.EXT_ID, '0') = LTRIM(m.VTREF, '0') 
   AND m.PLAN_TYPE = 'BASE_PLAN'
LEFT JOIN (
    SELECT 
        CON_ID, 
        MAX(NULLIF(CUST_PLAN_NAME, '')) AS CUST_PLAN_NAME,
        MAX(CAST(PLAN_PRICE AS DECIMAL(15,2))) AS PLAN_PRICE_DECIMAL
    FROM SAPHANADB.ZEL_EVENT_RAW
    WHERE EVENT_TYPE NOT LIKE '%COMMISSION%'
      AND PLAN_PRICE IS NOT NULL AND PLAN_PRICE <> '' 
      AND PLAN_PRICE NOT LIKE '%Infinity%'
      AND PLAN_PRICE NOT LIKE '%NaN%'
      AND PLAN_PRICE NOT LIKE '%BASIC%'
    GROUP BY CON_ID
) evt 
    ON LTRIM(caco.EXT_ID, '0') = LTRIM(evt.CON_ID, '0')

-- Filter by Contract ID(s):
WHERE caco.EXT_ID = '00000000000000061742'

-- Or Filter by Subscriber / Customer ID(s):
-- WHERE sa.SUBSCRIBER IN ('0011111151', '0000073467', '0000634156')

ORDER BY sa.SUBSCRIBER, caco.EXT_ID, allo.OID;
```

---

## 📊 1,000-Account Benchmark Audit Results

We executed an automated benchmark script against 1,000 active contracts in DEV HANA (`10.4.4.125:30041`):

```text
================================================================================
 RUNNING BULK VALIDATION OF MASTER QUERY ACROSS 1,000 CONTRACT ACCOUNTS
================================================================================
[OK] Query executed successfully in 4.43 seconds!
Total Allowance Records Retrieved: 3115

--------------------------------------------------------------------------------
 SUMMARY METRICS FOR 1,000 CONTRACTS
--------------------------------------------------------------------------------
Distinct Subscriber Accounts: 734
Distinct Contracts Analyzed:  1000
Total Allowance Instances:    3115

Allowance Type Breakdown:
  - OTHER_ALLOWANCE     : 1463 records
  - FTTH_BASIC          : 578 records
  - GRACE_FREE_PERIOD   : 374 records
  - BUFFER_PERIOD       : 373 records
  - AUTO_RENEWAL_FLAG   : 327 records
```

---

## 📁 Repository File Index

* [`SAP_CC_GRACE_PERIOD_DISCOVERY_STORY.md`](./SAP_CC_GRACE_PERIOD_DISCOVERY_STORY.md) - Full end-to-end technical story and architectural documentation.
* [`test_dynamic_grace_no_hardcoding.py`](./test_dynamic_grace_no_hardcoding.py) - Python script proving dynamic grace value calculations across multiple contracts without hardcoding.
* [`test_1000_accounts_bulk_validation.py`](./test_1000_accounts_bulk_validation.py) - 1,000-account bulk benchmark test script.

---

## ✒️ Author
**Pranav Chandore**  
*SAP CC & HANA SDA Architecture Team*  
Repository: [PranavChandore/CC-SDA-SAP-HANA](https://github.com/PranavChandore/CC-SDA-SAP-HANA)
