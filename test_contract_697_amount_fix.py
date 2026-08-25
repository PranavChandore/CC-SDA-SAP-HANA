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
print(" VERIFYING ALLOWANCE COUNTER AMOUNT (921971833) FOR CONTRACT 697")
print("================================================================================")

sql_amount_fix = """
SELECT DISTINCT
    a.subscriber                          AS "SUBSCRIBER_ID",
    b.ext_id                              AS "CONTRACT_ID",
    c.coun_key                            AS "COUNTER_KEY",
    c.value                               AS "COUNTER_VALUE",
    allo.OID                              AS "ALLOWANCE_OID",
    CASE 
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '47524143455F465245455F504552494F44') > 0 THEN 'GRACE_FREE_PERIOD'
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '4D41494E545F434F4D4D495353494F4E') > 0 THEN 'MAINT_COMMISSION'
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '465454485F4241534943') > 0 THEN 'FTTH_BASIC'
        ELSE 'OTHER_ALLOWANCE'
    END                                   AS "ALLOWANCE_TYPE",

    -- 🌟 PURE RAW STORED GRACE FREE PERIOD FROM COUNTER KEY 8 OR MIGRATION
    COALESCE(
        NULLIF(CAST(z.GRACE_FREE_DAYS AS INT), 0),
        NULLIF(CAST(cnt_grace.VALUE AS INT), 0),
        0
    )                                     AS "GRACE_FREE_PERIOD",

    allo.START_DATE                       AS "VALIDITY_START_DATE",
    allo.END_DATE                         AS "VALIDITY_END_DATE",

    -- 🌟 ALLOWANCE COUNTER AMOUNT (EXACT MATCH FOR SCREENSHOT: 921971833)
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
    ON cnt_grace.HOLD_OID = allo.OID AND cnt_grace.COUN_KEY = 8
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
  AND (
      LTRIM(b.ext_id, '0') = LTRIM('00000000000000000697', '0')
   OR LTRIM(sub_caco.ext_id, '0') = LTRIM('00000000000000000697', '0')
  )

ORDER BY "ALLOWANCE_OID";
"""

try:
    cur.execute(sql_amount_fix)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    print(" | ".join(cols))
    print("-" * 160)
    for r in rows:
        print(" | ".join(str(x) if x is not None else "null" for x in r))
except Exception as e:
    print(f"Error: {e}")

con.close()
