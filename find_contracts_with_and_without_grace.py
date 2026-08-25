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
print(" 1. CONTRACTS WITH A GRACE PERIOD (GRACE_FREE_PERIOD > 0)")
print("================================================================================")

sql_with_grace = """
SELECT DISTINCT
    a.subscriber                          AS "SUBSCRIBER_ID",
    b.ext_id                              AS "CONTRACT_ID",
    COALESCE(z.ALLOWANCE_ID, CAST(allo.OID AS NVARCHAR)) AS "ALLOWANCE_OID",
    COALESCE(
        z.ALLOW_TYPE,
        CASE 
            WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '47524143455F465245455F504552494F44') > 0 THEN 'GRACE_FREE_PERIOD'
            ELSE 'OTHER'
        END
    )                                     AS "ALLOWANCE_TYPE",
    COALESCE(
        NULLIF(CAST(z.GRACE_FREE_DAYS AS INT), 0),
        NULLIF(CAST(cnt_grace.VALUE AS INT), 0),
        CASE 
            WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '47524143455F465245455F504552494F44') > 0 
             AND YEAR(allo.END_DATE) < 2099
            THEN GREATEST(0, DAYS_BETWEEN(CURRENT_DATE, CAST(allo.END_DATE AS DATE)))
            ELSE 0
        END
    )                                     AS "GRACE_FREE_PERIOD"
FROM SAPHANADB.CC_DEV_SUBSCRIBER_ACCOUNT a
JOIN SAPHANADB.CC_DEV_CACO b ON a.oid = b.suac_oid
JOIN SAPHANADB.CC_DEV_COUNTER c ON b.suac_oid = c.suac_oid
LEFT JOIN SAPHANADB.CC_DEV_CACO sub_caco ON b.oid = sub_caco.roco_oid
LEFT JOIN SAPHANADB.CC_DEV_ALLO allo ON allo.caco_oid = b.oid OR allo.caco_oid = sub_caco.oid
LEFT JOIN SAPHANADB.CC_DEV_COUNTER cnt_grace ON cnt_grace.HOLD_OID = allo.OID AND cnt_grace.COUN_KEY = 20 AND cnt_grace.VALUE BETWEEN 1 AND 365
LEFT JOIN SAPHANADB.ZEL_ALLW_MIG z ON (LTRIM(b.ext_id, '0') = LTRIM(z.VTREF, '0') OR LTRIM(sub_caco.ext_id, '0') = LTRIM(z.VTREF, '0')) AND allo.OID = z.ALLOWANCE_ID
WHERE c.coun_key = 4
  AND (
      CAST(z.GRACE_FREE_DAYS AS INT) > 0
   OR cnt_grace.VALUE > 0
   OR (LOCATE(BINTOHEX(allo.ALLO_DATA), '47524143455F465245455F504552494F44') > 0 AND YEAR(allo.END_DATE) < 2099)
  )
ORDER BY b.ext_id
LIMIT 10;
"""

try:
    cur.execute(sql_with_grace)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    print(" | ".join(f"{c:<20}" for c in cols))
    print("-" * 120)
    for r in rows:
        print(" | ".join(f"{str(x):<20}" for x in r))
except Exception as e:
    print(f"Error: {e}")

print("\n================================================================================")
print(" 2. CONTRACTS WITHOUT A GRACE PERIOD (GRACE_FREE_PERIOD = 0)")
print("================================================================================")

sql_no_grace = """
SELECT DISTINCT
    a.subscriber                          AS "SUBSCRIBER_ID",
    b.ext_id                              AS "CONTRACT_ID",
    COALESCE(z.ALLOWANCE_ID, CAST(allo.OID AS NVARCHAR)) AS "ALLOWANCE_OID",
    COALESCE(
        z.ALLOW_TYPE,
        CASE 
            WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '47524143455F465245455F504552494F44') > 0 THEN 'GRACE_FREE_PERIOD'
            WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '4D41494E545F434F4D4D495353494F4E') > 0 THEN 'MAINT_COMMISSION'
            WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '465454485F4241534943') > 0 THEN 'FTTH_BASIC'
            ELSE 'OTHER_ALLOWANCE'
        END
    )                                     AS "ALLOWANCE_TYPE",
    0                                     AS "GRACE_FREE_PERIOD"
FROM SAPHANADB.CC_DEV_SUBSCRIBER_ACCOUNT a
JOIN SAPHANADB.CC_DEV_CACO b ON a.oid = b.suac_oid
JOIN SAPHANADB.CC_DEV_COUNTER c ON b.suac_oid = c.suac_oid
LEFT JOIN SAPHANADB.CC_DEV_CACO sub_caco ON b.oid = sub_caco.roco_oid
LEFT JOIN SAPHANADB.CC_DEV_ALLO allo ON allo.caco_oid = b.oid OR allo.caco_oid = sub_caco.oid
LEFT JOIN SAPHANADB.ZEL_ALLW_MIG z ON (LTRIM(b.ext_id, '0') = LTRIM(z.VTREF, '0') OR LTRIM(sub_caco.ext_id, '0') = LTRIM(z.VTREF, '0')) AND allo.OID = z.ALLOWANCE_ID
WHERE c.coun_key = 4
  AND LOCATE(BINTOHEX(allo.ALLO_DATA), '47524143455F465245455F504552494F44') = 0
  AND (z.GRACE_FREE_DAYS IS NULL OR CAST(z.GRACE_FREE_DAYS AS INT) = 0)
ORDER BY b.ext_id
LIMIT 10;
"""

try:
    cur.execute(sql_no_grace)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    print(" | ".join(f"{c:<20}" for c in cols))
    print("-" * 120)
    for r in rows:
        print(" | ".join(f"{str(x):<20}" for x in r))
except Exception as e:
    print(f"Error: {e}")

con.close()
