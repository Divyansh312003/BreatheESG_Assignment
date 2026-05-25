# DECISIONS

## 1. Use a flat SAP export instead of live SAP connectivity

- Choice: upload a realistic SAP MM-style CSV export.
- Why: it is the fastest credible onboarding path in a short prototype and avoids inventing SAP auth/integration details that cannot be validated here.
- What I would ask the PM: do analysts initially receive recurring SAP extracts by email/SFTP, or do we actually control SAP-side API access?

## 2. Use a Green Button-style utility feed instead of PDF bill OCR

- Choice: parse a structured XML subset with usage point, meter reading, billing period, and interval usage.
- Why: it surfaces the normalization problems the assignment cares about without spending the entire prototype budget on OCR.
- What I would ask the PM: what percentage of onboarded customers can provide machine-readable utility exports versus PDF-only bills?

## 3. Use Concur-like travel receipts instead of a direct third-party login flow

- Choice: sync a local JSON snapshot shaped like travel receipt data.
- Why: it demonstrates the API-pull model and category-specific travel normalization while keeping the demo self-contained and reviewable.
- What I would ask the PM: does the target customer already centralize travel through a single platform, or do we need to reconcile multiple providers?

## 4. Use one normalized ledger table

- Choice: put all reviewable business activity into `ActivityRecord`.
- Why: analysts review one queue, not three systems. Source-specific detail still lives in payload JSON.
- What I would ask the PM: do reviewers need separate work queues by source or one blended queue with filters?

## 5. Keep auth out of scope

- Choice: no login wall in the prototype.
- Why: the assignment prioritizes ingestion, normalization, reviewability, and judgment. Mock auth would add surface area without increasing signal.
- What I would ask the PM: is SSO mandatory for evaluation, or is role modeling enough for the prototype?

## 6. Use SQLite locally

- Choice: local SQLite database under Django 4.2.
- Why: Django 5 was incompatible with the host SQLite version. Django 4.2 solves the runtime constraint while keeping the relational model portable.
- What I would ask the PM: is local reproducibility or production database fidelity more important for the hiring exercise?
