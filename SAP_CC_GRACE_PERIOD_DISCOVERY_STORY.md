# 📖 The Journey of Unlocking SAP CC Grace Period, Amounts & SDA Tables

> **System Target**: SAP Convergent Charging 2023 / SAP HANA DEV Database (`10.4.4.125:30041`)  
> **Schema**: `SAPHANADB`  
> **Key Entity**: Provider Contract `00000000000000061742` (`CACO.OID = 395304100`)  

---

## 📑 Executive Summary

This document captures the complete technical investigation, discovery, and verification process of retrieving **Grace Free Period (`GRACE_FREE_PERIOD`)**, **Allowance Type**, **Product**, **Sub Product**, **Allowance Amounts**, and validity parameters from SAP Convergent Charging (SAP CC) via Smart Data Access (SDA) on SAP HANA using generic SQL queries and Python tools.

---

## 📜 Chapter 1: The Quest & Initial Challenge

In SAP CC architecture, provider contracts manage customer subscriptions, counters, balances, and allowances. A critical requirement was to determine:
1. Whether all **6 core SAP CC virtual tables** are accessible without privilege/SDA permission errors.
2. Where and how the **Grace Free Period (`GRACE_FREE_PERIOD`)**, **Allowance Types**, and **Amounts** are stored in the underlying database for any customer or list of contracts.

---

## 🔬 Chapter 2: Smart Data Access (SDA) Permission Verification

We executed automated diagnostic scripts across the DEV HANA instance (`10.4.4.125:30041`, Schema `SAPHANADB`). All 6 virtual tables pointing to the remote SAP CC database (`CC_DEV`) were verified to be **100% active, error-free, and queryable**.

| Virtual Table Name | Remote Table | Status | Record Count | Architectural Role |
| :--- | :--- | :--- | :--- | :--- |
| `SAPHANADB.CC_DEV_SUBSCRIBER_ACCOUNT` | `SUBSCRIBER_ACCOUNT` | `[OK] Active` | 58,000+ | Master customer subscriber container (`SUAC_OID`) |
| `SAPHANADB.CC_DEV_CACO` | `CACO` | `[OK] Active` | 120,000+ | Charging contract header (`OID`, `ROCO_OID`, `EXT_ID`) |
| `SAPHANADB.CC_DEV_COUNTER` | `COUNTER` | `[OK] Active` | 850,000+ | High-speed numerical counters and data usage quotas |
| `SAPHANADB.CC_DEV_ALLO` | `ALLO` | `[OK] Active` | 2,100,000+ | Allowance instances, amounts, and validity periods |
| `SAPHANADB.CC_DEV_CACI` | `CACI` | `[OK] Active` | 450,000+ | Charging contract items & activated plan definitions |
| `SAPHANADB.CC_DEV_CACI_PARAMETER` | `CACI_PARAMETER` | `[OK] Active` | 1,200,000+ | Custom contract parameters from CRM / S/4HANA |

---

## 🛠️ Chapter 3: Universal Generic HANA SQL Query (For Multiple Customers / Contracts)

This generic query dynamically parses allowance types, products, sub-products, amounts, and **calculates the exact Grace Free Period Days (`DAYS_BETWEEN`)** for **any list of customers or contracts**:

```sql
SELECT 
    sa.SUBSCRIBER                         AS "SUBSCRIBER_ID",
    caco.EXT_ID                           AS "CONTRACT_ID",
    caco.OID                              AS "CONTRACT_OID",
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
    CASE 
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '47524143455F465245455F504552494F44') > 0 
        THEN DAYS_BETWEEN(CAST(allo.START_DATE AS DATE), CAST(allo.END_DATE AS DATE))
        ELSE 0
    END                                   AS "GRACE_FREE_PERIOD_DAYS",
    allo.START_DATE                       AS "VALIDITY_START_DATE",
    allo.END_DATE                         AS "VALIDITY_END_DATE",
    COALESCE(
        NULLIF(m.VARIANT_NAME, ''), 
        NULLIF(evt.CUST_PLAN_NAME, ''), 
        'BASIC'
    )                                     AS "PLAN_NAME",
    COALESCE(evt.PLAN_PRICE_DECIMAL, 0)   AS "AMOUNT",
    caco.OP_STATUS                        AS "CONTRACT_STATUS"
FROM SAPHANADB.CC_DEV_SUBSCRIBER_ACCOUNT sa
JOIN SAPHANADB.CC_DEV_CACO caco 
    ON sa.OID = caco.SUAC_OID
JOIN SAPHANADB.CC_DEV_ALLO allo 
    ON caco.OID = allo.CACO_OID
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
-- Filter by list of Subscribers / Customers:
WHERE sa.SUBSCRIBER IN ('0011111151', '0000073467', '0000634156')
-- Or filter by list of Contract IDs:
-- WHERE caco.EXT_ID IN ('00000000000000061742', '00000000000000061734')
ORDER BY sa.SUBSCRIBER, caco.EXT_ID, allo.OID;
```

---

## 📌 Query Usage Options

1. **For a List of Customers / Subscribers**:
   `WHERE sa.SUBSCRIBER IN ('0011111151', '0000073467', '0000634156')`
2. **For a List of Provider Contracts**:
   `WHERE caco.EXT_ID IN ('00000000000000061742', '00000000000000061734', '00000000000000061738')`
3. **For All Active Grace Allowances Across System**:
   `WHERE LOCATE(BINTOHEX(allo.ALLO_DATA), '47524143455F465245455F504552494F44') > 0`
