"""
diagnose_sda_privileges.py
-------------------------------------------------------------------------
Script to diagnose and verify SAP HANA SDA Insufficient Privilege (Error 258)
on remote database instances (CC_DEV / CCD).

Run this script with python to inspect the exact missing privileges.
-------------------------------------------------------------------------
"""
import sys

def print_solution_sql():
    print("=" * 80)
    print("               SAP HANA SDA PRIVILEGE FIX - SQL COMMANDS")
    print("=" * 80)
    print("\n1. RUN DIAGNOSTIC ON REMOTE DB (CC_DEV / CCD):")
    print("   -----------------------------------------------------------------")
    print("   CALL SYS.GET_INSUFFICIENT_PRIVILEGE_ERROR_DETAILS('901B7DD54335734FAD6662CE86F56852', ?);")
    print("   CALL SYS.GET_INSUFFICIENT_PRIVILEGE_ERROR_DETAILS('24248E35261BF247BB1F88A553FBA522', ?);")
    print("\n2. RUN GRANT COMMANDS ON REMOTE DB (CC_DEV / CCD) as DB ADMIN:")
    print("   -----------------------------------------------------------------")
    print("   -- Option A: Grant SELECT on the entire COREUSER schema (Recommended)")
    print("   GRANT SELECT ON SCHEMA \"COREUSER\" TO <REMOTE_SDA_USER>;")
    print("\n   -- Option B: Grant SELECT specifically on CACO table")
    print("   GRANT SELECT ON \"COREUSER\".\"CACO\" TO <REMOTE_SDA_USER>;")
    print("\n   -- Option C: Grant Catalog Read Privileges")
    print("   GRANT CATALOG READ TO <REMOTE_SDA_USER>;")
    print("=" * 80)

def main():
    print("Attempting to connect to SAP HANA to diagnose SDA issue...")
    try:
        from hdbcli import dbapi
    except ImportError:
        print("[!] 'hdbcli' library is not installed in current Python environment.")
        print("    You can run: pip install hdbcli")
        print_solution_sql()
        return

    # Prompt or configure connection parameters if executing directly
    host = input("Enter Remote HANA Host/IP (or press Enter for standard SQL output): ").strip()
    if not host:
        print_solution_sql()
        return

    port = int(input("Enter Remote HANA Port (e.g. 30015 / 30515): ").strip())
    user = input("Enter Admin Username (e.g. SYSTEM): ").strip()
    password = input("Enter Password: ").strip()

    try:
        conn = dbapi.connect(address=host, port=port, user=user, password=password)
        cursor = conn.cursor()
        print("\n[+] Successfully connected to SAP HANA Database!")

        guid = "901B7DD54335734FAD6662CE86F56852"
        print(f"\n[*] Running GET_INSUFFICIENT_PRIVILEGE_ERROR_DETAILS for GUID '{guid}'...")
        cursor.execute(f"CALL SYS.GET_INSUFFICIENT_PRIVILEGE_ERROR_DETAILS('{guid}', ?)")
        rows = cursor.fetchall()
        for r in rows:
            print("   Diagnostic Result:", r)

        remote_user = input("\nEnter the Remote SDA User ID identified from diagnosis: ").strip()
        if remote_user:
            sql_grant = f'GRANT SELECT ON SCHEMA "COREUSER" TO "{remote_user}"'
            confirm = input(f"Execute '{sql_grant}'? (y/n): ").strip().lower()
            if confirm == 'y':
                cursor.execute(sql_grant)
                conn.commit()
                print(f"[+] Successfully granted SELECT on SCHEMA 'COREUSER' to '{remote_user}'!")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[!] Error: {e}")
        print_solution_sql()

if __name__ == "__main__":
    main()
