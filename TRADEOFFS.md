# TRADEOFFS

## 1. I did not build editable normalization transforms per field

- Why not: the assignment rewards defendable scope. I prioritized a strong first-pass normalization model and review audit trail over a large transformation builder.

## 2. I did not build OCR for PDF utility bills

- Why not: it would consume most of the implementation budget and distract from the cross-source review model. Structured utility data was the sharper prototype choice.

## 3. I did not implement user authentication and role-based permissions

- Why not: the prototype is intended to demonstrate ingestion, mapping, anomaly surfacing, and analyst sign-off. The review state and audit model are ready for auth to be layered on later.
