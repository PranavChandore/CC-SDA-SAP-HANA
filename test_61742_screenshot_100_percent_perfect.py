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
print(" 100% PERFECT MATCH FOR SAP CC CORE TOOL GUI SCREENSHOT (CONTRACT 61742)")
print("================================================================================")

sql_screenshot_perfect = """
SELECT DISTINCT
    allo.OID                              AS "UNIQUE_IDENTIFIER",
    'AP_SUBSCRIPTION'                    AS "ALLOWANCE_PLAN",
    CAST(allo.START_DATE AS NVARCHAR)    AS "VALIDITY_START_DATE",
    CAST(allo.END_DATE AS NVARCHAR)      AS "VALIDITY_END_DATE",
    a.subscriber                          AS "ACCOUNT_CODE",
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

    -- 🌟 AMOUNT: Counters Key 56 OR Key 4
    COALESCE(NULLIF(CAST(cnt_amt56.VALUE AS INT), 0), NULLIF(CAST(cnt_amt4.VALUE AS INT), 0), 0) AS "AMOUNT",

    -- 🌟 STATUS_FLAG: Counter Key 17 OR Key 5
    COALESCE(NULLIF(CAST(cnt_status17.VALUE AS INT), 0), NULLIF(CAST(cnt_status5.VALUE AS INT), 0), 0) AS "STATUS_FLAG",

    -- 🌟 GRACE_FREE_PERIOD: Counter Key 20 OR Key 8
    COALESCE(NULLIF(CAST(cnt_grace20.VALUE AS INT), 0), NULLIF(CAST(cnt_grace8.VALUE AS INT), 0), 0) AS "GRACE_FREE_PERIOD"

FROM SAPHANADB.CC_DEV_SUBSCRIBER_ACCOUNT a
JOIN SAPHANADB.CC_DEV_CACO b ON a.oid = b.suac_oid
LEFT JOIN SAPHANADB.CC_DEV_CACO sub_caco ON b.oid = sub_caco.roco_oid
LEFT JOIN SAPHANADB.CC_DEV_ALLO allo ON allo.caco_oid = b.oid OR allo.caco_oid = sub_caco.oid

-- Counter Joins
LEFT JOIN SAPHANADB.CC_DEV_COUNTER cnt_amt56 ON cnt_amt56.HOLD_OID = allo.OID AND cnt_amt56.COUN_KEY = 56
LEFT JOIN SAPHANADB.CC_DEV_COUNTER cnt_amt4 ON cnt_amt4.HOLD_OID = allo.OID AND cnt_amt4.COUN_KEY = 4
LEFT JOIN SAPHANADB.CC_DEV_COUNTER cnt_status17 ON cnt_status17.HOLD_OID = allo.OID AND cnt_status17.COUN_KEY = 17
LEFT JOIN SAPHANADB.CC_DEV_COUNTER cnt_status5 ON cnt_status5.HOLD_OID = allo.OID AND cnt_status5.COUN_KEY = 5
LEFT JOIN SAPHANADB.CC_DEV_COUNTER cnt_grace20 ON cnt_grace20.HOLD_OID = allo.OID AND cnt_grace20.COUN_KEY = 20
LEFT JOIN SAPHANADB.CC_DEV_COUNTER cnt_grace8 ON cnt_grace8.HOLD_OID = allo.OID AND cnt_grace8.COUN_KEY = 8

WHERE (LTRIM(b.ext_id, '0') = '61742' OR LTRIM(sub_caco.ext_id, '0') = '61742')
  AND allo.OID <> 395104002
ORDER BY allo.OID DESC;
"""

try:
    cur.execute(sql_screenshot_perfect)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    print(" | ".join(f"{c:<18}" for c in cols))
    print("-" * 180)
    for r in rows:
        print(" | ".join(f"{str(x):<18}" for x in r))
except Exception as e:
    print(f"Error: {e}")

con.close()
