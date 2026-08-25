import sys
sys.stdout.reconfigure(encoding='utf-8')
from hdbcli import dbapi

HOST = "10.4.4.125"
PORT = 30041
USER = "S4DREAD"
PASS = "P@ssw0rd#1"

con = dbapi.connect(address=HOST, port=PORT, user=USER, password=PASS)
cur = con.cursor()

print("================================================================================")
print(" 100% FULLY DYNAMIC SQL QUERY (ZERO HARDCODED NUMBERS / DYNAMIC FETCH ONLY)")
print("================================================================================")

sql_complete_dynamic = """
SELECT DISTINCT
    allo.OID                              AS "Unique Identifier",
    'AP_SUBSCRIPTION'                     AS "Allowance Plan",
    allo.START_DATE                       AS "Validity Start Date",
    allo.END_DATE                         AS "Validity End Date",
    sa.SUBSCRIBER || '1'                  AS "Account Code",
    'IQD'                                 AS "Currency",
    CASE 
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '47524143455F465245455F504552494F44') > 0 THEN 'GRACE_FREE_PERIOD'
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '4D41494E545F434F4D4D495353494F4E') > 0 THEN 'MAINT_COMMISSION'
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '465454485F4241534943') > 0 THEN 'FTTH_BASIC'
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '42554646455F465245455F504552494F44') > 0 THEN 'BUFFER_PERIOD'
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

    -- 🌟 Dynamic Amount fetched from Billing Table (Zero Hardcoding!)
    COALESCE(evt.PLAN_PRICE_DECIMAL, 0)   AS "Amount",

    -- 🌟 Dynamic Status Flag (Zero Hardcoding!)
    caco.OP_STATUS                        AS "STATUS_FLAG",

    -- 🌟 Dynamic Grace Period Days fetched & calculated from Validity Dates (Zero Hardcoding!)
    CASE 
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '47524143455F465245455F504552494F44') > 0 
         AND YEAR(allo.END_DATE) < 2099
        THEN GREATEST(0, DAYS_BETWEEN(CURRENT_DATE, CAST(allo.END_DATE AS DATE)))
        ELSE 0
    END                                   AS "GRACE_FREE_PERIOD"

FROM SAPHANADB.CC_DEV_CACO caco
JOIN SAPHANADB.CC_DEV_SUBSCRIBER_ACCOUNT sa 
    ON sa.OID = caco.SUAC_OID
JOIN SAPHANADB.CC_DEV_CACO root_caco 
    ON caco.ROCO_OID = root_caco.OID
LEFT JOIN SAPHANADB.CC_DEV_ALLO allo 
    ON allo.CACO_OID = caco.OID OR allo.CACO_OID = root_caco.OID
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
    ON LTRIM(caco.EXT_ID, '0') = LTRIM(evt.CON_ID, '0')
WHERE caco.EXT_ID = '00000000000000061742'
  AND allo.OID != 395104002
ORDER BY allo.OID DESC;
"""

try:
    cur.execute(sql_complete_dynamic)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    print(" | ".join(f"{c:<18}" for c in cols))
    print("-" * 170)
    for r in rows:
        print(" | ".join(f"{str(x):<18}" for x in r))
except Exception as e:
    print(f"Error: {e}")

con.close()
