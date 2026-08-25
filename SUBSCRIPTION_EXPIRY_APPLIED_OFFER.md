# Walkthrough & Implementation Plan: Subscription Expiry Notifications with Applied Offer

## Overview
We have identified the relevant MediationZone (MZ) workflows on QAS, verified the SAP HANA staging table `ZEL_CS_OFFERS_MT`, and added a backend service endpoint to calculate applied offer discounts for subscription expiry notifications.

---

## 1. Key Changes Made

### Backend Implementation (`other_tools.py`)
* Added the `/api/tools/subscription-offer/check` API endpoint.
* Enables support engineers and MZ notification scripts to pass a `contract_id` and `base_amount`.
* Queries `ZEL_CS_OFFERS_MT` on QAS or PROD to locate active offers (`STATUS = 'A'`).
* Calculates net renewal price ($\text{Final Amount} = \text{Base Amount} - \text{Discount}$) and renders a notification payload preview.

```python
@other_tools_bp.route("/api/tools/subscription-offer/check", methods=["POST"])
@login_required
def check_subscription_offer():
    # Queries ZEL_CS_OFFERS_MT for contract ID
    # Computes offer discount (percentage or flat amount)
    # Returns final renewal amount and notification payload preview
```

---

## 2. Verification & Testing

### 1. Code Compilation
Ran `py_compile` on `earthlink-app/backend/routes/tools/other_tools.py`:
* **Result:** Successfully compiled with 0 syntax errors.

### 2. Workflow Discovery on QAS
Verified the following MediationZone (MZ) workflows responsible for plan expiry and notification delivery:
* `Notifications.WFL_PlanExpiry.PLAN_EXPIRY`
* `Notifications.WFL_PlanExpiry.PLAN_EXPIRY_-7`
* `Notifications.WFL_PlanExpiry.PLAN_EXPIRY_3`
* `Notifications.WFL_Notification.SEND_NOTIFICATION`

---

## 3. Next Steps for QAS Deployment
1. Deploy the backend updates to the QAS app server.
2. In DigitalRoute MediationZone (MZ) on QAS, update the `Notifications.WFL_PlanExpiry.PLAN_EXPIRY` APL logic to query `ZEL_CS_OFFERS_MT` before constructing the `SEND_NOTIFICATION` payload.

---

# Implementation Plan: Include Applied Offer in Expiry Notifications

This plan details the step-by-step procedure to update the Plan Expiry Notification Workflow so that subscribers receive their plan renewal notification with the discounted amount (including applied offers) rather than the standard base plan price.

## User Review Required

> [!IMPORTANT]
> **Data Logic Rule:** Confirm whether the final notification amount should:
> 1. Show the final discounted amount only (e.g., *"Your plan expires on XX. Renewal amount: SAR 150"*).
> 2. Show both original and offer-applied amounts (e.g., *"Original: SAR 200, Offer Price: SAR 150"*).
> 3. Fall back to standard plan price if no active offer is found in `ZEL_CS_OFFERS_MT`.

> [!WARNING]
> Workflow changes in DigitalRoute MediationZone (MZ) on QAS require disabling `Notifications.WFL_PlanExpiry.PLAN_EXPIRY` temporarily, editing/compiling the APL/workflow configuration, and re-enabling it.

---

## Open Questions

> [!NOTE]
> 1. Is the offer discount expressed as a flat amount reduction or a percentage in `OFFER_CHARACTERISTICS_VALUE`?
> 2. Does `ZEL_CS_OFFERS_MT` contain all currently active customer offers, or should the current subscription API (`ProductAPI.WFL_ProductAPI.Current_subs_API`) also be queried as a backup?

---

## Step-by-Step Execution Plan

### Step 1: Verify Active Offers Data in QAS Database
Check how offer records are stored in the SAP HANA staging table `ZEL_CS_OFFERS_MT`.

Execute the following SQL query on HANA QAS (via Data Explorer tool or DB client):

```sql
SELECT 
    MANDT, 
    ORDER_ID, 
    CON_ID, 
    APPLIED_OFFER_PURCHASE_TYPE, 
    OFFER_ID, 
    MATNR, 
    OFFER_APPLIED_START_DATE, 
    OFFER_APPLIED_END_DATE, 
    OFFER_CHARACTERISTICS, 
    OFFER_CHARACTERISTICS_VALUE, 
    STATUS
FROM SAPHANADB.ZEL_CS_OFFERS_MT 
WHERE CON_ID = '<TEST_CONTRACT_ID>' 
  AND STATUS = 'A'
ORDER BY CREATE_TS DESC;
```
* Verify that `OFFER_APPLIED_START_DATE` and `OFFER_APPLIED_END_DATE` span the current/renewal period.

### Step 2: Update Data Retrieval in MediationZone (MZ) Workflow
In DigitalRoute MediationZone Desktop / APL code for workflow `Notifications.WFL_PlanExpiry.PLAN_EXPIRY` (and pre-expiry `PLAN_EXPIRY_-7` / `PLAN_EXPIRY_3`):

1. **Add Offer Query Logic:**
   - Query `ZEL_CS_OFFERS_MT` using contract ID (`CON_ID` / `VTREF`).
   - Filter by active date: `CURRENT_DATE BETWEEN OFFER_APPLIED_START_DATE AND OFFER_APPLIED_END_DATE` and `STATUS = 'A'`.
2. **Calculate Net Amount:**
   - If an active offer is found: $$\text{Final Amount} = \text{Base Plan Price} - \text{Offer Discount Amount}$$ (or apply percentage discount if `OFFER_CHARACTERISTICS` indicates percentage).
   - If no active offer exists: $$\text{Final Amount} = \text{Base Plan Price}$$.

### Step 3: Update Notification Payload & Template
In the `Notifications.WFL_Notification.SEND_NOTIFICATION` workflow:

1. Update the payload structure passed to `SEND_NOTIFICATION`:
   - Pass fields: `contractId`, `expiryDate`, `originalAmount`, `offerId`, `discountAmount`, `finalAmount`.
2. Update the SMS/Email notification template string:
   - **Example Template:**
     *"Dear Customer, your subscription for contract {CON_ID} expires on {EXPIRY_DATE}. Your renewal amount with applied offer ({OFFER_ID}) is {FINAL_AMOUNT} SAR. Renew now to stay connected!"*

### Step 4: Deploy & Test on QAS Environment
1. **Stop & Update MZ Workflows on QAS:**
   - Use the MZ Controller tool in the Earthlink Web App to pause `Notifications.WFL_PlanExpiry.PLAN_EXPIRY`.
   - Apply the updated workflow / APL code.
   - Restart the workflow via MZ Controller.
2. **Run End-to-End Simulation:**
   - Pick a test contract in QAS with an active offer in `ZEL_CS_OFFERS_MT`.
   - Trigger the `Notifications.WFL_PlanExpiry.PLAN_EXPIRY` workflow manually or wait for the scheduled batch execution.
   - Verify that the generated notification record in the notification log/queue reflects `finalAmount` with the applied offer.

---

## Verification Plan

### Manual & Staging Verification
* **Contract with Active Offer:** Confirm notification receives discounted price.
* **Contract without Offer:** Confirm notification defaults safely to standard plan price.
* **Expired/Inactive Offer:** Confirm notification ignores expired offer dates and uses standard plan price.
* **Log Inspection:** Check `Notifications.WFL_Notification` execution logs on QAS for clean completion without errors.
