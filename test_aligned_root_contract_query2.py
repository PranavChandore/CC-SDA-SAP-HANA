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
print(" FULLY ALIGNED SINGLE-TABLE SQL QUERY (ROOT CONTRACT + COUNTER 4 + ALLOWANCES)")
print("================================================================================")

full_aligned_sql = """
SELECT 
    a.subscriber                          AS "SUBSCRIBER",
    b.ext_id                              AS "SHARED_ROOT_CONTRACT_ID",
    b.oid                                 AS "ROOT_CONTRACT_OID",
    c.coun_key                            AS "COUNTER_KEY",
    c.value                               AS "COUNTER_VALUE",
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
LEFT JOIN SAPHANADB.ZVEL_CS_MASTER(CURRENT_DATE, CURRENT_TIME) m 
    ON LTRIM(b.ext_id, '0') = LTRIM(m.vtref, '0') 
   AND m.plan_type = 'BASE_PLAN'
LEFT JOIN (
    SELECT 
        con_id, 
        MAX(NULLIF(cust_plan_name, '')) AS CUST_PLAN_NAME,
        MAX(CAST(plan_price AS DECIMAL(15,2))) AS PLAN_PRICE_DECIMAL
    FROM SAPHANADB.ZEL_EVENT_RAW
    WHERE event_type NOT LIKE '%COMMISSION%'
      AND plan_price IS NOT NULL AND plan_price <> '' 
      AND plan_price NOT LIKE '%Infinity%'
      AND plan_price NOT LIKE '%NaN%'
      AND plan_price NOT LIKE '%BASIC%'
    GROUP BY con_id
) evt 
    ON LTRIM(b.ext_id, '0') = LTRIM(evt.con_id, '0')
WHERE a.subscriber = '0000073467'
  AND c.coun_key = 4
  AND b.oid = b.roco_oid
ORDER BY allo.oid;
"""

try:
    cur.execute(full_aligned_sql)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    print(" | ".join(cols))
    print("-" * 160)
    for r in rows:
        print(" | ".join(str(x) if x is not None else "null" for x in r))
except Exception as e:
    print(f"Error in full aligned SQL: {e}")

con.close()
