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
print(" SAFE HANA SQL QUERY FOR POPULATING PLAN_NAME AND AMOUNT")
print("================================================================================")

sql_clean = """
SELECT 
    sa.SUBSCRIBER                         AS "SUBSCRIBER_ID",
    caco.EXT_ID                           AS "CONTRACT_ID",
    caco.OID                              AS "CONTRACT_OID",
    allo.OID                              AS "ALLOWANCE_OID",
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
WHERE caco.EXT_ID = '00000000000000061742'
ORDER BY allo.OID;
"""

try:
    cur.execute(sql_clean)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    print(" | ".join(cols))
    print("-" * 130)
    for r in rows:
        print(" | ".join(str(x) if x is not None else "null" for x in r))
except Exception as e:
    print(f"Error: {e}")

con.close()
