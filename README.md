# Earthlink App & SAP CC SDA Integration Repository

This repository contains the analysis, verification tools, and end-to-end integration workflows for SAP Convergent Charging (SAP CC), SAP HANA SDA Virtual Tables, and S/4HANA Contract Management.

---

## 🌟 Featured Documentation

- 📖 **[SAP CC Grace Period Discovery Story](file:///c:/Users/prana/Downloads/earthlink-app/SAP_CC_GRACE_PERIOD_DISCOVERY_STORY.md)**  
  Detailed investigation, SDA table permission audit, allowance BLOB decoding (`GRACE_FREE_PERIOD = 77`), and cross-matching with SAP CC Core Tool GUI.

- ⚡ **[Quick Reference Guide](file:///c:/Users/prana/Downloads/earthlink-app/QUICK_REFERENCE.md)**  
  Quick lookup guide for environment parameters, database ports, and user credentials.

- 📊 **[Subscription Expiry & Applied Offers](file:///c:/Users/prana/Downloads/earthlink-app/SUBSCRIPTION_EXPIRY_APPLIED_OFFER.md)**  
  Logic and SQL queries for tracking plan expiry and discount flat offers.

---

## 🛠️ SAP CC Virtual Tables Reference (SDA)

| Virtual Table | Remote Object | Schema | Role |
| :--- | :--- | :--- | :--- |
| `SAPHANADB.CC_DEV_SUBSCRIBER_ACCOUNT` | `SUBSCRIBER_ACCOUNT` | `SAPHANADB` | Subscriber Account Master Container |
| `SAPHANADB.CC_DEV_CACO` | `CACO` | `SAPHANADB` | Provider / Charging Contracts |
| `SAPHANADB.CC_DEV_COUNTER` | `COUNTER` | `SAPHANADB` | High-speed Quotas & Usage Balances |
| `SAPHANADB.CC_DEV_ALLO` | `ALLO` | `SAPHANADB` | Allowances & Grace Period Data |
| `SAPHANADB.CC_DEV_CACI` | `CACI` | `SAPHANADB` | Contract Items & Active Plans |
| `SAPHANADB.CC_DEV_CACI_PARAMETER` | `CACI_PARAMETER` | `SAPHANADB` | Contract Parameters |

---

## 🚀 Key Scripts

- `dev_hana_check.py`: Alignment check script for DEV HANA.
- `diagnose_sda_privileges.py`: SDA privilege diagnostic helper.
- `find_grace_period_in_cc.py`: Grace period and allowance extraction tool.
