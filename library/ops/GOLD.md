# Gold questions — ops domain

Owner-written acceptance rows for this domain, written ONCE, before the
domain was modeled. This table is MACHINE-PARSED by `tests/test_gold.py`
(and CI): each row's Question is run through the active read layer, and
the row passes if **Must contain** appears in recall.py output OR the
**Source** file appears in search.py results — mirroring the two
retrieval paths (loud-fail only when both miss). Adding a test = adding
a row. `primer` rows were written before real users existed; a failing
primer row is a modeling to-do, a failing real-user row is a fire.

| # | Question | Must contain | Source | Status |
|---|----------|--------------|--------|--------|
| 1 | Who approves a refund over £500? | Ops Manager | refund-approvals.md | primer |
| 2 | Who signs off an £800 refund? | Ops Manager | refund-approvals.md | primer |
| 3 | Who covers Ops Manager approvals in March? | Marcus Webb | ops-manager.md | primer |
| 4 | How fast are small refunds processed? | 48 | refund-approvals.md | primer |
| 5 | How are approved refunds paid out? | original payment method | refund-approvals.md | primer |
| 6 | Who approves supplier payments over £2,000? | Founder | supplier-payments.md | primer |
| 7 | What are supplier payment terms? | 30-day | supplier-payments.md | primer |
| 8 | What must happen before a new supplier's first invoice? | Tooling Inventory | supplier-payments.md | primer |
| 9 | Who owns onboarding? | Ops Manager | onboarding-process.md | primer |
| 10 | What is the day-one onboarding checklist? | tooling inventory | onboarding-process.md | primer |
| 11 | Who triages incidents? | Support Lead | incident-response.md | primer |
| 12 | Where do severity-1 incidents escalate? | Founder | incident-response.md | primer |
| 13 | When does a support ticket escalate? | Support Lead | customer-support-sop.md | primer |
| 14 | What is the ticket response SLA? | one business day | customer-support-sop.md | primer |
