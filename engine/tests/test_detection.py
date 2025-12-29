from __future__ import annotations

from pathlib import Path

from grouporderai.parsing.schema_loader import SchemaLoader


def test_detect_platform_from_text(tmp_path: Path):
    # Create a minimal schema folder with one schema
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)

    (schemas_dir / "demo.json").write_text(
        """
        {
          "platform_info": {"platform_id": "demo", "business_client": "Group - Demo", "order_type": "individual_orders"},
          "detection": {"min_matches": 1, "patterns": ["DEMO_PLATFORM"]},
          "extraction_rules": {"main_order_info": {"fields": {}}},
          "output_mapping": {"main_order_information": {}}
        }
        """.strip(),
        encoding="utf-8",
    )

    loader = SchemaLoader(str(schemas_dir))
    detected = loader.detect_platform_from_text("hello DEMO_PLATFORM world")
    assert detected == "demo"
