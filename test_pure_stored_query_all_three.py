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
print(" PURE STORED DATABASE QUERY FOR CONTRACTS 61742, 49260, AND 682")
print("================================================================================")

sql_pure = """
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

    -- 🌟 PURE RAW STORED VALUES ONLY (ZERO DATE CALCULATIONS!)
    COALESCE(
        NULLIF(CAST(z.GRACE_FREE_DAYS AS INT), 0),
        NULLIF(CAST(cnt_grace.VALUE AS INT), 0),
        0
    )                                     AS "GRACE_FREE_PERIOD",

    COALESCE(z.VALIDITY_START_DT, CAST(allo.START_DATE AS NVARCHAR)) AS "VALIDITY_START_DATE",
    COALESCE(z.VALIDITY_END_DT, CAST(allo.END_DATE AS NVARCHAR))     AS "VALIDITY_END_DATE"

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
    ON cnt_grace.HOLD_OID = allo.OID AND cnt_grace.COUN_KEY = 20
LEFT JOIN SAPHANADB.ZEL_ALLW_MIG z 
    ON (LTRIM(b.ext_id, '0') = LTRIM(z.VTREF, '0') OR LTRIM(sub_caco.ext_id, '0') = LTRIM(z.VTREF, '0'))
   AND allo.OID = z.ALLOWANCE_ID

WHERE c.coun_key = 4
  AND (
      LTRIM(b.ext_id, '0') IN ('61742', '49260', '682')
   OR LTRIM(sub_caco.ext_id, '0') IN ('61742', '49260', '682')
  )
  AND (
      LOCATE(BINTOHEX(allo.ALLO_DATA), '47524143455F465245455F504552494F44') > 0
   OR z.ALLOW_TYPE = 'GRACE_FREE_PERIOD'
  )

ORDER BY b.ext_id;
"""

try:
    cur.execute(sql_pure)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    print(" | ".join(f"{c:<18}" for c in cols))
    print("-" * 150)
    for r in rows:
        print(" | ".join(f"{str(x):<18}" for x in r))
except Exception as e:
    print(f"Error: {e}")

con.close()
