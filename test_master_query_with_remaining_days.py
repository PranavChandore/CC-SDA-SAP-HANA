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
print(" MASTER QUERY WITH BOTH TOTAL GRACE DAYS & REMAINING GRACE DAYS")
print("================================================================================")

master_sql_both = """
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
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '47524143455F465245455F504552494F44') > 0 
         AND YEAR(allo.END_DATE) < 2099
        THEN DAYS_BETWEEN(CAST(allo.START_DATE AS DATE), CAST(allo.END_DATE AS DATE))
        ELSE 0
    END                                   AS "GRACE_TOTAL_DAYS",
    CASE 
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '47524143455F465245455F504552494F44') > 0 
         AND YEAR(allo.END_DATE) < 2099
        THEN GREATEST(0, DAYS_BETWEEN(CURRENT_DATE, CAST(allo.END_DATE AS DATE)))
        ELSE 0
    END                                   AS "GRACE_REMAINING_DAYS_TODAY",
    CASE 
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '47524143455F465245455F504552494F44') > 0 
         AND YEAR(allo.END_DATE) < 2099
        THEN GREATEST(0, DAYS_BETWEEN(CAST('2026-09-04' AS DATE), CAST(allo.END_DATE AS DATE)))
        ELSE 0
    END                                   AS "GRACE_REMAINING_DAYS_SEP4",
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
WHERE caco.EXT_ID = '00000000000000061742'
ORDER BY sa.SUBSCRIBER, caco.EXT_ID, allo.OID;
"""

try:
    cur.execute(master_sql_both)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    print(" | ".join(cols))
    print("-" * 160)
    for r in rows:
        print(" | ".join(str(x) if x is not None else "null" for x in r))
except Exception as e:
    print(f"Error: {e}")

con.close()
