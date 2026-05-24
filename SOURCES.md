# SOURCES

These sources informed the choice of data shapes and the sample payload structure.

## SAP

- SAP Help: exporting ALV output to spreadsheets, which supports the flat-export onboarding path.
- SAP API Business Hub: purchase order processing OData APIs, which informed the SAP-style fields used in the sample export and parser.

## Utility electricity

- Green Button Alliance documentation on `UsagePoint`, `MeterReading`, `ReadingType`, and interval usage concepts.
- This is why the sample utility feed carries usage point ids, billing periods, tariff metadata, and interval readings instead of a toy monthly total only.

## Corporate travel

- SAP Concur receipts API and receipt schemas for air, hotel, and ground transport.
- This is why the demo feed uses category-specific receipts and lets air, hotel, and ground normalize differently.

## What would break in real deployment

- SAP: customer-specific SAP extract variants, localization, and custom material groups.
- Utility: provider-specific XML quirks, interval granularity differences, and tariff models.
- Travel: OAuth, pagination, schema drift, and missing itinerary enrichment.
