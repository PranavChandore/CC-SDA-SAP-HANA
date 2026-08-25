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
print(" PURE DIRECT TABLE SELECT FROM ZEL_ALLW_MIG (ZERO CALCULATION / DIRECT FETCH ONLY)")
print("================================================================================")

sql_no_calc = """
SELECT DISTINCT
    a.subscriber                          AS "SUBSCRIBER_ID",
    b.ext_id                              AS "CONTRACT_ID",
    c.coun_key                            AS "COUNTER_KEY",
    c.value                               AS "COUNTER_VALUE",
    c.hold_oid                            AS "HOLD_OID",
    z.ALLOWANCE_ID                        AS "ALLOWANCE_OID",
    z.ALLOW_TYPE                          AS "ALLOWANCE_TYPE",
    z.PRODUCT                             AS "PRODUCT",
    z.SUB_PRODUCT                         AS "SUB_PRODUCT",

    -- 🌟 PURE RAW STORED COLUMN FETCH FROM DATABASE TABLE (ZERO CALCULATION!)
    CAST(z.GRACE_FREE_DAYS AS INT)        AS "GRACE_FREE_PERIOD",

    z.VALIDITY_START_DT                   AS "VALIDITY_START_DATE",
    z.VALIDITY_END_DT                     AS "VALIDITY_END_DATE",
    CAST(z.AMOUNT AS DECIMAL(15,2))       AS "AMOUNT",
    z.STATUS_FLAG                         AS "CONTRACT_STATUS"

FROM SAPHANADB.CC_DEV_SUBSCRIBER_ACCOUNT a
JOIN SAPHANADB.CC_DEV_CACO b
    ON a.oid = b.suac_oid
JOIN SAPHANADB.CC_DEV_COUNTER c
    ON b.suac_oid = c.suac_oid
JOIN SAPHANADB.ZEL_ALLW_MIG z 
    ON LTRIM(b.ext_id, '0') = LTRIM(z.VTREF, '0')
WHERE c.coun_key = 4
  AND CAST(z.GRACE_FREE_DAYS AS INT) > 0
ORDER BY b.ext_id, z.ALLOWANCE_ID
LIMIT 10;
"""

try:
    cur.execute(sql_no_calc)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    print(" | ".join(cols))
    print("-" * 160)
    for r in rows:
        print(" | ".join(str(x) if x is not None else "null" for x in r))
except Exception as e:
    print(f"Error: {e}")

con.close()
