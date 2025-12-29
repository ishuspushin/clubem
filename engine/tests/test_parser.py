from __future__ import annotations
from pathlib import Path

import pytest

from grouporderai.parsing.parser import UniversalParser


def test_universal_parser_minimal_main_order_info(tmp_path: Path):
    """
    Parse should not crash and should map business_client/client_name/guests.
    This uses text extraction indirectly in real runs; here we call parser internals by
    giving a fake "pdf path" is not feasible without a real PDF, so we test the
    mapping/extraction logic using a schema and calling _extract_main_order_info.
    """
    schema = {
        "platform_info": {"platform_id": "demo", "business_client": "Group - Demo", "order_type": "individual_orders"},
        "detection": {"min_matches": 1, "patterns": ["DEMO"]},
        "extraction_rules": {
            "main_order_info": {
                "fields": {
                    "client_name": {"pattern": r"Client:\s*([^\n]+)", "group": 1, "type": "string"},
                    "headcount": {"pattern": r"Guests:\s*(\d+)", "group": 1, "type": "integer"},
                }
            },
            "individual_orders": {},
        },
        "output_mapping": {
            "main_order_information": {
                "business_client": {"source": "platform_info.business_client"},
                "client_name": {"source": "main_order_info.client_name"},
                "number_of_guests": {"source": "main_order_info.headcount"},
                "requested_pick_up_time": {"value": ""},
                "requested_pick_up_date": {"value": ""},
                "delivery": {"value": ""},
                "order_subtotal": {"value": None},
                "client_information": {"value": ""},
            },
            "group_orders": {"group_order_number": {"value": ""}, "pick_time": {"value": ""}},
        },
    }

    parser = UniversalParser(schema)

    text = "Client: ACME Corp\nGuests: 25\n"
    info = parser._extract_main_order_info(text)

    assert info.business_client == "Group - Demo"
    assert info.client_name == "ACME Corp"
    assert info.number_of_guests == 25


def test_universal_parser_no_detection_rules_still_safe():
    schema = {
        "platform_info": {"platform_id": "demo", "business_client": "Group - Demo", "order_type": "individual_orders"},
        "detection": {"min_matches": 1, "patterns": ["DEMO"]},
        "extraction_rules": {"main_order_info": {"fields": {}}, "individual_orders": {}},
        "output_mapping": {"main_order_information": {}},
    }

    parser = UniversalParser(schema)
    info = parser._extract_main_order_info("anything")
    # Should not crash; client fields may be empty
    assert info.business_client in ("Group - Demo", "")
