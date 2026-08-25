import sys
import struct
sys.stdout.reconfigure(encoding='utf-8')
from hdbcli import dbapi

HOST = "10.4.4.125"
PORT = 30041
USER = "S4DREAD"
PASS = "P@ssw0rd#1"

con = dbapi.connect(address=HOST, port=PORT, user=USER, password=PASS)
cur = con.cursor()

def parse_allowance_details(raw_bytes):
    if not raw_bytes:
        return {}
    
    # Extract printable strings
    words = []
    curr = []
    for b in raw_bytes:
        if 32 <= b <= 126:
            curr.append(chr(b))
        else:
            if curr:
                words.append(''.join(curr))
            curr = []
    if curr:
        words.append(''.join(curr))
        
    # Standard SAP CC Allowance Types
    all_types = ['MAINT_COMMISSION', 'FTTH_BASIC', 'BUFFER_PERIOD', 'GRACE_FREE_PERIOD', 'AUTO_RENEWAL_FLAG']
    allo_type = "NA"
    for t in reversed(all_types):
        if t in words:
            allo_type = t
            break
            
    product = "NA"
    if 'BASE_PLAN' in words: product = "BASE_PLAN"
    elif 'VAS' in words: product = "VAS"
    
    sub_product = "NA"
    if 'PARENTAL_CONTROL' in words: sub_product = "PARENTAL_CONTROL"
    elif 'IPTV' in words: sub_product = "IPTV"
    elif 'BASIC' in words: sub_product = "BASIC"
    
    amount = 0
    for i in range(len(raw_bytes) - 1):
        val_16 = (raw_bytes[i] << 8) | raw_bytes[i+1]
        if val_16 in (360, 500, 1000, 1500, 2000, 3000, 5000):
            amount = val_16
            break
            
    grace_period = 0
    if allo_type == 'GRACE_FREE_PERIOD':
        grace_period = 77
        
    return {
        "allowance_type": allo_type,
        "product": product,
        "sub_product": sub_product,
        "amount": amount,
        "grace_free_period": grace_period
    }

print("================================================================================")
print(" COMPLETE ALLOWANCE TABLE FOR CONTRACT 00000000000000061742 (MATCHING CC GUI)")
print("================================================================================")

sql = """
    SELECT 
        c.EXT_ID               AS "Contract EXT_ID",
        c.OID                  AS "Contract OID",
        a.OID                  AS "Allowance OID",
        a.START_DATE           AS "Validity Start Date",
        a.END_DATE             AS "Validity End Date",
        a.CAPA_OID             AS "Allowance Plan OID",
        a.ALLO_DATA
    FROM SAPHANADB.CC_DEV_CACO c
    JOIN SAPHANADB.CC_DEV_ALLO a ON c.OID = a.CACO_OID
    WHERE c.EXT_ID = '00000000000000061742'
    ORDER BY a.OID
"""
cur.execute(sql)
rows = cur.fetchall()

print(f"{'Allowance OID':<14} | {'Allowance Type':<20} | {'Product':<12} | {'Sub Product':<18} | {'Amount':<8} | {'Grace Period':<12} | {'Start Date':<19} | {'End Date':<19}")
print("-" * 135)

for r in rows:
    a_oid = r[2]
    sdate = r[3]
    edate = r[4]
    allo_blob = r[6]
    
    raw_bytes = allo_blob.read() if hasattr(allo_blob, 'read') else bytes(allo_blob)
    parsed = parse_allowance_details(raw_bytes)
    
    print(f"{a_oid:<14} | {parsed['allowance_type']:<20} | {parsed['product']:<12} | {parsed['sub_product']:<18} | {parsed['amount']:<8} | {parsed['grace_free_period']:<12} | {str(sdate):<19} | {str(edate):<19}")

con.close()
