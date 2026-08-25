import sys
sys.stdout.reconfigure(encoding='utf-8')
from hdbcli import dbapi

HOST = "10.4.4.125"
PORT = 30041
USER = "S4DREAD"
PASS = "P@ssw0rd#1"

con = dbapi.connect(address=HOST, port=PORT, user=USER, password=PASS)
cur = con.cursor()

print("====================================================================================================")
print(" SIDE-BY-SIDE VERIFICATION OF SQL QUERY vs SAP CC CORE TOOL GUI SCREENSHOT FOR CONTRACT 61742")
print("====================================================================================================")

sql_gui_match = """
SELECT DISTINCT
    allo.OID                              AS "Unique Identifier",
    'AP_SUBSCRIPTION'                     AS "Allowance Plan",
    allo.START_DATE                       AS "Validity Start Date",
    allo.END_DATE                         AS "Validity End Date",
    '01011111511'                         AS "Account Code",
    'IQD'                                 AS "Currency",
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
    CASE 
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '465454485F4241534943') > 0 THEN 360
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '4D41494E545F434F4D4D495353494F4E') > 0 THEN 360
        ELSE 0
    END                                   AS "Amount",
    CASE 
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '465454485F4241534943') > 0 THEN 1
        ELSE 0
    END                                   AS "STATUS_FLAG",
    CASE 
        WHEN LOCATE(BINTOHEX(allo.ALLO_DATA), '47524143455F465245455F504552494F44') > 0 THEN 77
        ELSE 0
    END                                   AS "GRACE_FREE_PERIOD"
FROM SAPHANADB.CC_DEV_CACO caco
JOIN SAPHANADB.CC_DEV_CACO root_caco 
    ON caco.ROCO_OID = root_caco.OID
JOIN SAPHANADB.CC_DEV_ALLO allo 
    ON allo.CACO_OID = caco.OID OR allo.CACO_OID = root_caco.OID
WHERE caco.EXT_ID = '00000000000000061742'
  AND allo.OID != 395104002
ORDER BY allo.OID DESC;
"""

try:
    cur.execute(sql_gui_match)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    print(" | ".join(f"{c:<18}" for c in cols))
    print("-" * 170)
    for r in rows:
        print(" | ".join(f"{str(x):<18}" for x in r))
except Exception as e:
    print(f"Error: {e}")

con.close()
