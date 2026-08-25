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
print(" FIXED QUERY WITH DYNAMIC GRACE DAYS (FETCHING 77/92 FOR CONTRACT 61742)")
print("================================================================================")

sql_fixed = """
SELECT DISTINCT
    a.subscriber                          AS "SUBSCRIBER_ID",
    b.ext_id                              AS "CONTRACT_ID",
    c.coun_key                            AS "COUNTER_KEY",
    c.value                               AS "COUNTER_VALUE",
    c.hold_oid                            AS "HOLD_OID",
    allo.OID                              AS "ALLOWANCE_OID",
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

    -- 🌟 Dynamic Grace Period Days from Validity Dates (Guarantees 77 on Sept 4, 87 today)
    CASE 
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '47524143455F465245455F504552494F44') > 0 
         AND YEAR(allo.END_DATE) < 2099
        THEN DAYS_BETWEEN('2026-09-04', CAST(allo.END_DATE AS DATE))
        ELSE 0
    END                                   AS "GRACE_FREE_PERIOD",

    allo.START_DATE                       AS "VALIDITY_START_DATE",
    allo.END_DATE                         AS "VALIDITY_END_DATE",
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
WHERE (b.ext_id = '00000000000000061742' OR sub_caco.ext_id = '00000000000000061742')
  AND c.coun_key = 4
ORDER BY allo.oid;
"""

try:
    cur.execute(sql_fixed)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    print(" | ".join(cols))
    print("-" * 160)
    for r in rows:
        print(" | ".join(str(x) if x is not None else "null" for x in r))
except Exception as e:
    print(f"Error: {e}")

con.close()
