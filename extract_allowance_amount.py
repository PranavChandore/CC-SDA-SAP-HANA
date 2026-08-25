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
print(" INSPECTING ALLOWANCE AMOUNT & PARAMETERS FOR CONTRACT 00000000000000061742")
print("================================================================================")

sql = """
    SELECT 
        a.OID AS ALLOWANCE_OID,
        c.EXT_ID AS CONTRACT_EXT_ID,
        a.START_DATE,
        a.END_DATE,
        a.ALLO_DATA
    FROM SAPHANADB.CC_DEV_CACO c
    JOIN SAPHANADB.CC_DEV_ALLO a ON c.OID = a.CACO_OID
    WHERE c.EXT_ID = '00000000000000061742'
    ORDER BY a.OID
"""
cur.execute(sql)
rows = cur.fetchall()

print(f"Found {len(rows)} allowance instance(s) for contract 00000000000000061742:")

for r in rows:
    allo_oid = r[0]
    ext_id = r[1]
    sdate = r[2]
    edate = r[3]
    allo_blob = r[4]
    
    raw_bytes = allo_blob.read() if hasattr(allo_blob, 'read') else bytes(allo_blob)
    
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
        
    print(f"\n--------------------------------------------------------------------------------")
    print(f" Allowance OID: {allo_oid}")
    print(f" Start Date   : {sdate} | End Date: {edate}")
    print(f" Raw Bytes Len: {len(raw_bytes)}")
    print(f" Extracted Strings: {words}")
    
    # Scan for number 360 in bytes or strings
    # Check if 360 appears as text string '360' or binary integer/double
    has_360_str = '360' in words
    print(f" Contains '360' string? {has_360_str}")

con.close()
