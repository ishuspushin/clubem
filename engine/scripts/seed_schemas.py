from __future__ import annotations

import json
from pathlib import Path

from registry.filesystem import FileSchemaRegistry


def main() -> None:
    shipped_dir = Path("schemas")
    reg = FileSchemaRegistry(base_dir="schema_registry")

    for fp in sorted(shipped_dir.glob("*.json")):
        try:
            schema = json.loads(fp.read_text(encoding="utf-8"))
            reg.upsert_active_schema(schema, create_history=False)
            print(f"Seeded: {fp.name}")
        except Exception as e:
            print(f"Skipped {fp.name}: {e}")


if __name__ == "__main__":
    main()
