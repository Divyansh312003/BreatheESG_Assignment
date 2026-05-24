import csv
import io
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal, InvalidOperation

from core.constants import ActivityCategory, IssueSeverity, ScopeCategory


CURRENCY_TO_USD = {
    "USD": Decimal("1.00"),
    "EUR": Decimal("1.08"),
    "GBP": Decimal("1.26"),
}

VOLUME_TO_LITER = {
    "L": Decimal("1"),
    "LTR": Decimal("1"),
    "LITERS": Decimal("1"),
    "GAL": Decimal("3.78541"),
}

AIRPORT_DISTANCE_MILES = {
    ("LHR", "AMS"): Decimal("231"),
    ("AMS", "LHR"): Decimal("231"),
    ("LHR", "CDG"): Decimal("215"),
    ("CDG", "LHR"): Decimal("215"),
}

SAP_HEADER_ALIASES = {
    "purchasingdocument": "document_id",
    "beleg": "document_id",
    "purchasingitem": "line_item",
    "position": "line_item",
    "companycode": "company_code",
    "buchungskreis": "company_code",
    "plant": "plant_code",
    "werk": "plant_code",
    "postingdate": "posting_date",
    "buchungsdatum": "posting_date",
    "material": "material_code",
    "materialdescription": "material_description",
    "materialbezeichnung": "material_description",
    "materialgroup": "material_group",
    "materialgruppe": "material_group",
    "quantity": "quantity",
    "menge": "quantity",
    "orderunit": "unit",
    "unit": "unit",
    "einheit": "unit",
    "netpriceamount": "amount",
    "betrag": "amount",
    "documentcurrency": "currency",
    "waehrung": "currency",
    "supplier": "supplier",
    "lieferant": "supplier",
}


def _parse_decimal(value):
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, AttributeError):
        return None


def _parse_date(value):
    if not value:
        return None
    cleaned = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(cleaned.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _find_text(element, tag_names):
    for tag_name in tag_names:
        found = element.find(".//{*}%s" % tag_name)
        if found is not None and found.text:
            return found.text.strip()
    return ""


def parse_sap_export(file_bytes):
    decoded = file_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))
    issues = []
    records = []
    preview = []

    if not reader.fieldnames:
        return {
            "records": [],
            "issues": [
                {
                    "severity": IssueSeverity.ERROR,
                    "line_number": None,
                    "field_name": "file",
                    "message": "The SAP export file is missing headers.",
                    "raw_payload": {},
                }
            ],
            "preview": [],
            "rejected_count": 1,
        }

    normalized_headers = {}
    for raw_header in reader.fieldnames:
        header_key = raw_header.replace(" ", "").replace("_", "").lower()
        normalized_headers[raw_header] = SAP_HEADER_ALIASES.get(header_key, header_key)

    rejected_count = 0

    for line_number, raw_row in enumerate(reader, start=2):
        row = {}
        for raw_key, value in raw_row.items():
            row[normalized_headers.get(raw_key, raw_key)] = (value or "").strip()

        if len(preview) < 3:
            preview.append(row)

        required_fields = [
            "document_id",
            "line_item",
            "plant_code",
            "posting_date",
            "material_group",
            "material_description",
            "amount",
            "currency",
        ]
        missing_fields = [field for field in required_fields if not row.get(field)]
        if missing_fields:
            rejected_count += 1
            issues.append(
                {
                    "severity": IssueSeverity.ERROR,
                    "line_number": line_number,
                    "field_name": ",".join(missing_fields),
                    "message": "Missing required SAP fields: {}.".format(", ".join(missing_fields)),
                    "raw_payload": row,
                }
            )
            continue

        posting_date = _parse_date(row.get("posting_date"))
        amount = _parse_decimal(row.get("amount"))
        quantity = _parse_decimal(row.get("quantity"))
        currency = row.get("currency", "").upper()

        if posting_date is None or amount is None:
            rejected_count += 1
            issues.append(
                {
                    "severity": IssueSeverity.ERROR,
                    "line_number": line_number,
                    "field_name": "posting_date,amount",
                    "message": "The SAP row has an invalid date or amount.",
                    "raw_payload": row,
                }
            )
            continue

        material_group = row.get("material_group", "").upper()
        material_code = row.get("material_code", "")
        unit = row.get("unit", "").upper()
        suspicion_reasons = []

        if material_group.startswith("FUEL"):
            category = ActivityCategory.FUEL
            scope = ScopeCategory.SCOPE_1
            normalized_unit = "L"
            factor_code = "sap_fuel_diesel_liter" if "DIESEL" in material_group else "sap_fuel_gasoline_liter"
            normalized_quantity = None
            if quantity is not None and unit in VOLUME_TO_LITER:
                normalized_quantity = quantity * VOLUME_TO_LITER[unit]
                if unit != "L":
                    suspicion_reasons.append("Fuel volume was converted from {} to liters.".format(unit))
            else:
                suspicion_reasons.append("Fuel quantity could not be normalized to liters.")
        else:
            category = ActivityCategory.PROCUREMENT
            scope = ScopeCategory.SCOPE_3
            normalized_unit = "USD_SPEND"
            fx_rate = CURRENCY_TO_USD.get(currency)
            if fx_rate is None:
                rejected_count += 1
                issues.append(
                    {
                        "severity": IssueSeverity.ERROR,
                        "line_number": line_number,
                        "field_name": "currency",
                        "message": "Unsupported procurement currency: {}.".format(currency),
                        "raw_payload": row,
                    }
                )
                continue
            normalized_quantity = amount * fx_rate
            factor_code = "sap_procurement_generic_spend_usd"
            if material_group == "RAW_MATERIAL":
                factor_code = "sap_procurement_raw_material_spend_usd"
            elif material_group == "OFFICE_FURNITURE":
                factor_code = "sap_procurement_office_furniture_spend_usd"
            if currency != "USD":
                suspicion_reasons.append("Procurement spend was converted from {} to USD.".format(currency))

        records.append(
            {
                "external_id": "{}-{}".format(row["document_id"], row["line_item"]),
                "source_line_number": line_number,
                "source_document_identifier": row["document_id"],
                "activity_date": posting_date,
                "period_start": None,
                "period_end": None,
                "description": row.get("material_description") or material_code,
                "quantity_value": quantity,
                "quantity_unit": unit,
                "normalized_quantity": normalized_quantity,
                "normalized_unit": normalized_unit,
                "currency_code": currency,
                "spend_amount": amount,
                "factor_code": factor_code,
                "facility_alias": row.get("plant_code"),
                "category": category,
                "scope": scope,
                "suspicion_reasons": suspicion_reasons,
                "source_payload": row,
                "normalized_payload": {
                    "companyCode": row.get("company_code"),
                    "materialCode": material_code,
                    "materialGroup": material_group,
                    "supplier": row.get("supplier"),
                },
            }
        )

    return {
        "records": records,
        "issues": issues,
        "preview": preview,
        "rejected_count": rejected_count,
    }


def parse_utility_green_button(file_bytes):
    root = ET.fromstring(file_bytes)
    issues = []
    records = []
    preview = []

    for meter_reading in root.findall(".//{*}MeterReading"):
        usage_point_id = _find_text(meter_reading, ["UsagePointId", "UsagePoint"])
        service_location = _find_text(meter_reading, ["ServiceLocation", "ServiceLocationId"])
        tariff = _find_text(meter_reading, ["TariffProfile", "TariffCode"])
        unit = _find_text(meter_reading, ["Unit", "uom"]).upper() or "KWH"
        period_start = _parse_date(_find_text(meter_reading, ["Start", "BillingStart"]))
        period_end = _parse_date(_find_text(meter_reading, ["End", "BillingEnd"]))

        total_value = Decimal("0")
        total_cost = Decimal("0")
        for reading in meter_reading.findall(".//{*}IntervalReading"):
            value = _parse_decimal(_find_text(reading, ["Value", "value"]))
            cost = _parse_decimal(_find_text(reading, ["Cost", "cost"]))
            if value is not None:
                total_value += value
            if cost is not None:
                total_cost += cost

        if len(preview) < 2:
            preview.append(
                {
                    "usagePointId": usage_point_id,
                    "serviceLocation": service_location,
                    "tariff": tariff,
                    "totalValue": str(total_value),
                }
            )

        if not usage_point_id or not service_location or not period_start or not period_end:
            issues.append(
                {
                    "severity": IssueSeverity.ERROR,
                    "line_number": None,
                    "field_name": "meter_reading",
                    "message": "Utility feed is missing a usage point, service location, or billing period.",
                    "raw_payload": {
                        "usagePointId": usage_point_id,
                        "serviceLocation": service_location,
                        "tariff": tariff,
                    },
                }
            )
            continue

        suspicion_reasons = []
        if period_start.day != 1 or period_end.day < 28:
            suspicion_reasons.append("Billing period does not align to a calendar month boundary.")

        records.append(
            {
                "external_id": "{}-{}".format(usage_point_id, period_end.isoformat()),
                "source_line_number": None,
                "source_document_identifier": usage_point_id,
                "activity_date": period_end,
                "period_start": period_start,
                "period_end": period_end,
                "description": "Electricity usage for {}".format(service_location),
                "quantity_value": total_value,
                "quantity_unit": unit,
                "normalized_quantity": total_value,
                "normalized_unit": "KWH",
                "currency_code": "USD",
                "spend_amount": total_cost if total_cost else None,
                "factor_code": "utility_electricity_grid_kwh",
                "facility_alias": service_location,
                "category": ActivityCategory.ELECTRICITY,
                "scope": ScopeCategory.SCOPE_2,
                "suspicion_reasons": suspicion_reasons,
                "source_payload": {
                    "usagePointId": usage_point_id,
                    "serviceLocation": service_location,
                    "tariff": tariff,
                    "unit": unit,
                },
                "normalized_payload": {
                    "tariff": tariff,
                    "usagePointId": usage_point_id,
                },
            }
        )

    return {
        "records": records,
        "issues": issues,
        "preview": preview,
        "rejected_count": len([issue for issue in issues if issue["severity"] == IssueSeverity.ERROR]),
    }


def parse_travel_receipts(file_bytes):
    payload = json.loads(file_bytes.decode("utf-8"))
    issues = []
    records = []
    preview = []
    rejected_count = 0

    for item in payload.get("receipts", []):
        receipt = item.get("receipt", {})
        schema = item.get("validationSchema", "")
        receipt_id = item.get("id")
        trip_id = receipt.get("tripId", receipt_id)
        travel_date = _parse_date(receipt.get("transactionDate") or receipt.get("bookingDate") or receipt.get("checkIn"))
        if not receipt_id or travel_date is None:
            rejected_count += 1
            issues.append(
                {
                    "severity": IssueSeverity.ERROR,
                    "line_number": None,
                    "field_name": "travel_receipt",
                    "message": "Travel receipt is missing an id or usable date.",
                    "raw_payload": item,
                }
            )
            continue

        if len(preview) < 3:
            preview.append({"id": receipt_id, "schema": schema, "tripId": trip_id})

        suspicion_reasons = []
        spend_amount = _parse_decimal(receipt.get("amount") or receipt.get("baseFare") or receipt.get("totalAmount"))
        currency = (receipt.get("currency") or "USD").upper()
        facility_alias = receipt.get("homeFacilityCode") or receipt.get("costCenter")

        if "air" in schema:
            distance = _parse_decimal(receipt.get("distanceMiles"))
            origin = (receipt.get("originAirportCode") or "").upper()
            destination = (receipt.get("destinationAirportCode") or "").upper()
            if distance is None:
                distance = AIRPORT_DISTANCE_MILES.get((origin, destination))
                if distance is not None:
                    suspicion_reasons.append("Flight distance was derived from airport codes.")
            if distance is None:
                rejected_count += 1
                issues.append(
                    {
                        "severity": IssueSeverity.ERROR,
                        "line_number": None,
                        "field_name": "distanceMiles",
                        "message": "Air receipt is missing a distance and the airport pair is not in the lookup table.",
                        "raw_payload": item,
                    }
                )
                continue
            records.append(
                {
                    "external_id": receipt_id,
                    "source_line_number": None,
                    "source_document_identifier": trip_id,
                    "activity_date": travel_date,
                    "period_start": None,
                    "period_end": None,
                    "description": "{} flight {}-{}".format(receipt.get("merchantName", "Travel"), origin, destination),
                    "quantity_value": distance,
                    "quantity_unit": "MILE",
                    "normalized_quantity": distance,
                    "normalized_unit": "MILE",
                    "currency_code": currency,
                    "spend_amount": spend_amount,
                    "factor_code": "travel_air_mile",
                    "facility_alias": facility_alias,
                    "category": ActivityCategory.AIR_TRAVEL,
                    "scope": ScopeCategory.SCOPE_3,
                    "suspicion_reasons": suspicion_reasons,
                    "source_payload": item,
                    "normalized_payload": {"origin": origin, "destination": destination},
                }
            )
        elif "hotel" in schema:
            check_in = _parse_date(receipt.get("checkIn"))
            check_out = _parse_date(receipt.get("checkOut"))
            nights = _parse_decimal(receipt.get("nights"))
            if nights is None and check_in and check_out:
                nights = Decimal(str((check_out - check_in).days))
                suspicion_reasons.append("Hotel nights were derived from check-in and check-out dates.")
            if nights is None:
                rejected_count += 1
                issues.append(
                    {
                        "severity": IssueSeverity.ERROR,
                        "line_number": None,
                        "field_name": "nights",
                        "message": "Hotel receipt is missing nights and usable dates.",
                        "raw_payload": item,
                    }
                )
                continue
            records.append(
                {
                    "external_id": receipt_id,
                    "source_line_number": None,
                    "source_document_identifier": trip_id,
                    "activity_date": check_out or travel_date,
                    "period_start": check_in,
                    "period_end": check_out,
                    "description": "{} hotel stay".format(receipt.get("merchantName", "Travel")),
                    "quantity_value": nights,
                    "quantity_unit": "NIGHT",
                    "normalized_quantity": nights,
                    "normalized_unit": "ROOM_NIGHT",
                    "currency_code": currency,
                    "spend_amount": spend_amount,
                    "factor_code": "travel_hotel_night",
                    "facility_alias": facility_alias,
                    "category": ActivityCategory.HOTEL,
                    "scope": ScopeCategory.SCOPE_3,
                    "suspicion_reasons": suspicion_reasons,
                    "source_payload": item,
                    "normalized_payload": {"city": receipt.get("city"), "country": receipt.get("country")},
                }
            )
        elif "ground" in schema:
            distance = _parse_decimal(receipt.get("distanceMiles"))
            if distance is None:
                rejected_count += 1
                issues.append(
                    {
                        "severity": IssueSeverity.ERROR,
                        "line_number": None,
                        "field_name": "distanceMiles",
                        "message": "Ground transport receipt is missing distance miles.",
                        "raw_payload": item,
                    }
                )
                continue
            records.append(
                {
                    "external_id": receipt_id,
                    "source_line_number": None,
                    "source_document_identifier": trip_id,
                    "activity_date": travel_date,
                    "period_start": None,
                    "period_end": None,
                    "description": "{} ground transport".format(receipt.get("vehicleType", "Ground")),
                    "quantity_value": distance,
                    "quantity_unit": "MILE",
                    "normalized_quantity": distance,
                    "normalized_unit": "MILE",
                    "currency_code": currency,
                    "spend_amount": spend_amount,
                    "factor_code": "travel_ground_mile",
                    "facility_alias": facility_alias,
                    "category": ActivityCategory.GROUND,
                    "scope": ScopeCategory.SCOPE_3,
                    "suspicion_reasons": suspicion_reasons,
                    "source_payload": item,
                    "normalized_payload": {"vehicleType": receipt.get("vehicleType")},
                }
            )
        else:
            rejected_count += 1
            issues.append(
                {
                    "severity": IssueSeverity.ERROR,
                    "line_number": None,
                    "field_name": "validationSchema",
                    "message": "Unsupported travel schema: {}.".format(schema),
                    "raw_payload": item,
                }
            )

    return {
        "records": records,
        "issues": issues,
        "preview": preview,
        "rejected_count": rejected_count,
    }
