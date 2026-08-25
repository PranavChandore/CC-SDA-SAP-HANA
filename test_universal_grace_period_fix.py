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
print(" SAFE UNIVERSAL GRACE PERIOD QUERY ACROSS ALL CONTRACT TYPES")
print("================================================================================")

sql_safe = """
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
            WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '415544F5F52454E4557414C5F464C4147') > 0 THEN 'AUTO_RENEWAL_FLAG'
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

    -- 🌟 Safe Coalesce Strategy: Checks ZEL_ALLW_MIG column, then COUN_KEY = 20 counter, then validity date countdown
    COALESCE(
        NULLIF(CAST(z.GRACE_FREE_DAYS AS INT), 0),
        NULLIF(CAST(cnt_grace.VALUE AS INT), 0),
        CASE 
            WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '47524143455F465245455F504552494F44') > 0 
             AND YEAR(allo.END_DATE) < 2099
            THEN GREATEST(0, DAYS_BETWEEN(CURRENT_DATE, CAST(allo.END_DATE AS DATE)))
            ELSE 0
        END
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
    ON cnt_grace.HOLD_OID = allo.OID AND cnt_grace.COUN_KEY = 20 AND cnt_grace.VALUE BETWEEN 1 AND 365
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
  AND a.subscriber IN ('0011111151', '0000000493', '0260422215', '0000005000')
ORDER BY a.subscriber, b.ext_id, "ALLOWANCE_OID"
LIMIT 20;
"""

try:
    cur.execute(sql_safe)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    print(" | ".join(f"{c:<16}" for c in cols))
    print("-" * 170)
    for r in rows:
        print(" | ".join(f"{str(x):<16}" for x in r))
except Exception as e:
    print(f"Error: {e}")

con.close()
