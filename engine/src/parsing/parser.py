from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from domain.models import GroupOrder, IndividualOrder, MainOrderInfo, ParsedOrder
from .text_extract import TextExtractor


class PatternMatcher:
    """Applies extraction patterns from schema to text."""

    def __init__(self, schema: Dict[str, Any]) -> None:
        self.schema = schema

    def extract_field(self, text: str, field_config: Dict[str, Any]) -> Any:
        method = field_config.get("method", "pattern")

        if method == "pattern":
            return self._extract_pattern(text, field_config)
        if method == "section_extract":
            return self._extract_section(text, field_config)
        if method == "conditional":
            return self._extract_conditional(text, field_config)
        if method == "first_match":
            return self._extract_first_match(text, field_config)
        if method == "collect_until":
            return self._collect_until(text, field_config)

        return self._extract_pattern(text, field_config)

    def _extract_pattern(self, text: str, config: Dict[str, Any]) -> Any:
        pattern = config.get("pattern")
        if not pattern:
            return None

        flags = 0
        if str(config.get("flags", "")).lower() == "i":
            flags |= re.IGNORECASE
        if config.get("multiline"):
            flags |= re.MULTILINE

        match = re.search(pattern, text, flags)
        if not match:
            return None

        group = config.get("group", 1)
        try:
            value = match.group(group)
        except IndexError:
            value = match.group(0)

        return self._post_process(value, config)

    def _extract_section(self, text: str, config: Dict[str, Any]) -> Any:
        start_pattern = config.get("section_start", "")
        end_pattern = config.get("section_end", "$")
        pattern = f"{start_pattern}\\s*\\n?(.*?)(?={end_pattern})"

        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if not match:
            return None

        section = match.group(1).strip()
        lines = [line.strip() for line in section.split("\n") if line.strip()]

        skip = int(config.get("skip_lines", 0) or 0)
        if skip:
            lines = lines[skip:]

        line_index = config.get("line_index")
        if line_index is not None and lines:
            if int(line_index) < len(lines):
                return self._post_process(lines[int(line_index)], config)
            return None

        if config.get("join_lines"):
            return self._post_process(" ".join(lines), config)

        return self._post_process(lines[0] if lines else None, config)

    def _extract_conditional(self, text: str, config: Dict[str, Any]) -> Any:
        conditions = config.get("conditions", [])
        for condition in conditions:
            pattern = condition.get("pattern")
            flags = re.IGNORECASE if str(condition.get("flags", "")).lower() == "i" else 0
            if pattern and re.search(pattern, text, flags):
                return condition.get("value")
        return config.get("default")

    def _extract_first_match(self, text: str, config: Dict[str, Any]) -> Any:
        patterns = config.get("patterns", [])
        for pattern_config in patterns:
            if isinstance(pattern_config, dict):
                result = self.extract_field(text, pattern_config)
                if result:
                    return result
        return None

    def _collect_until(self, text: str, config: Dict[str, Any]) -> List[str]:
        start_after = config.get("start_after", "")
        end_before = config.get("end_before", "$")
        skip_patterns = config.get("skip_patterns", [])

        lines = text.split("\n")
        result: List[str] = []

        collecting = not bool(start_after)

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if start_after and re.search(start_after, line):
                collecting = True
                continue

            if collecting:
                if re.search(end_before, line):
                    break
                skip = any(re.search(p, line) for p in skip_patterns)
                if not skip:
                    result.append(line)

        return result

    def _post_process(self, value: Any, config: Dict[str, Any]) -> Any:
        if value is None:
            return None
        if not isinstance(value, str):
            return value

        operations = config.get("post_process", []) or []
        for op in operations:
            if op == "trim":
                value = value.strip()
            elif op == "normalize_whitespace":
                value = TextExtractor.normalize_whitespace(value)
            elif op == "dedupe_bold":
                value = TextExtractor.dedupe_bold_text(value)

        if config.get("dedupe_bold"):
            value = TextExtractor.dedupe_bold_text(value)

        field_type = config.get("type", "string")
        if field_type == "integer":
            try:
                return int(value)
            except (ValueError, TypeError):
                return 0
        if field_type == "currency":
            try:
                return float(value.replace(",", ""))
            except (ValueError, TypeError, AttributeError):
                return None

        return value


class UniversalParser:
    """Schema-driven PDF parser."""

    def __init__(self, schema: Dict[str, Any]) -> None:
        self.schema = schema
        self.matcher = PatternMatcher(schema)
        self.platform_info = schema.get("platform_info", {}) or {}

    def parse(self, pdf_path: str) -> ParsedOrder:
        combined_text, pages_text = TextExtractor.extract_all_text(pdf_path)

        preprocess = (
            self.schema.get("extraction_rules", {})
            .get("main_order_info", {})
            .get("text_preprocessing", {})
            or {}
        )
        if preprocess.get("dedupe_bold"):
            combined_text = TextExtractor.dedupe_bold_text(combined_text)
            pages_text = [TextExtractor.dedupe_bold_text(p) for p in pages_text]

        main_info = self._extract_main_order_info(combined_text)
        group_orders = self._extract_group_orders(combined_text, main_info)
        individual_orders = self._extract_individual_orders(combined_text, pages_text, main_info)

        return ParsedOrder(
            main_order_info=main_info,
            group_orders=group_orders,
            individual_orders=individual_orders,
            metadata={"platform": self.platform_info.get("platform_id"), "source_file": pdf_path},
        )

    def _extract_main_order_info(self, text: str) -> MainOrderInfo:
        rules = self.schema.get("extraction_rules", {}).get("main_order_info", {}) or {}
        fields = rules.get("fields", {}) or {}

        extracted: Dict[str, Any] = {}
        for field_name, field_config in fields.items():
            extracted[field_name] = self.matcher.extract_field(text, field_config)

        mapping = self.schema.get("output_mapping", {}).get("main_order_information", {}) or {}
        return MainOrderInfo(
            business_client=self._resolve_mapping(mapping.get("business_client"), extracted) or "",
            client_name=self._resolve_mapping(mapping.get("client_name"), extracted) or "",
            client_information=self._resolve_template(mapping.get("client_information"), extracted),
            order_subtotal=self._resolve_mapping(mapping.get("order_subtotal"), extracted),
            requested_pick_up_time=self._resolve_mapping(mapping.get("requested_pick_up_time"), extracted) or "",
            requested_pick_up_date=self._resolve_mapping(mapping.get("requested_pick_up_date"), extracted) or "",
            number_of_guests=self._resolve_mapping(mapping.get("number_of_guests"), extracted) or 0,
            delivery=self._resolve_mapping(mapping.get("delivery"), extracted) or "",
        )

    def _extract_group_orders(self, text: str, _main_info: MainOrderInfo) -> List[GroupOrder]:
        # Reuse the same extracted fields as in your original code (simple + robust)
        rules = self.schema.get("extraction_rules", {}).get("main_order_info", {}) or {}
        fields = rules.get("fields", {}) or {}

        extracted: Dict[str, Any] = {}
        for field_name, field_config in fields.items():
            extracted[field_name] = self.matcher.extract_field(text, field_config)

        mapping = self.schema.get("output_mapping", {}).get("group_orders", {}) or {}
        group_order_number = self._resolve_mapping(mapping.get("group_order_number"), extracted) or ""
        pick_time = self._resolve_mapping(mapping.get("pick_time"), extracted) or ""

        if not group_order_number and not pick_time:
            return []

        return [GroupOrder(group_order_number=group_order_number, pick_time=pick_time)]

    def _extract_individual_orders(
        self, text: str, pages: List[str], main_info: MainOrderInfo
    ) -> List[IndividualOrder]:
        rules = self.schema.get("extraction_rules", {}).get("individual_orders", {}) or {}
        order_type = self.platform_info.get("order_type", "individual_orders")

        # Get group order number from main order mapping (like your current parser)
        group_order_number = ""
        mapping_group = self.schema.get("output_mapping", {}).get("group_orders", {}) or {}
        main_fields = self.schema.get("extraction_rules", {}).get("main_order_info", {}).get("fields", {}) or {}
        extracted_main: Dict[str, Any] = {}
        for field_name, field_config in main_fields.items():
            extracted_main[field_name] = self.matcher.extract_field(text, field_config)
        group_order_number = self._resolve_mapping(mapping_group.get("group_order_number"), extracted_main) or ""
        company_name = extracted_main.get("client_name")
        if not isinstance(company_name, str):
            company_name = None

        if order_type == "catering":
            return self._parse_catering_items(text, group_order_number, rules)
        if order_type == "group_order_with_names":
            return self._parse_named_group_order(text, group_order_number, rules)

        return self._parse_individual_orders(text, pages, group_order_number, rules, company_name=company_name)

    # ---- your existing strategies (kept simple and defensive) ----

    def _parse_catering_items(self, text: str, group_order_number: str, rules: Dict[str, Any]) -> List[IndividualOrder]:
        orders: List[IndividualOrder] = []
        item_config = rules.get("item_detection", {}) or {}
        pattern = item_config.get("pattern") or r"([A-Za-z][A-Za-z \-/&]+?)\s*-\s*(\d+)\s*-\s*([\d,.]+)"

        for match in re.finditer(pattern, text):
            item_name = (match.group(1) or "").strip()
            try:
                servings = int(match.group(2))
            except (TypeError, ValueError):
                servings = 0

            item_start = match.end()
            next_item = re.search(pattern, text[item_start:])
            item_end = item_start + next_item.start() if next_item else len(text)
            item_block = text[item_start:item_end]

            allergens_match = re.search(r"Contains\s*:?\s*(.*?)\s*(Other Tags|$)", item_block, re.IGNORECASE | re.DOTALL)
            allergens = (allergens_match.group(1).strip() if allergens_match else "")

            tags_match = re.search(r"Other Tags\s*:?\s*(.*?)(Packaging|$)", item_block, re.IGNORECASE | re.DOTALL)
            tags = (tags_match.group(1).strip() if tags_match else "")

            packaging_match = re.search(r"Packaging\s*:?\s*(.*?)(Vendor Notes|$)", item_block, re.IGNORECASE | re.DOTALL)
            packaging = (packaging_match.group(1).strip() if packaging_match else "")

            modifications: List[str] = []
            if allergens:
                modifications.append(f"Contains {allergens}")
            if tags:
                modifications.append(f"Tags {tags}")

            orders.append(
                IndividualOrder(
                    group_order_number=group_order_number,
                    guest_name=f"Catering servings {servings}",
                    item_name=item_name,
                    modifications=modifications,
                    comments=(f"Packaging: {packaging}" if packaging else ""),
                )
            )

        return orders

    def _parse_named_group_order(self, text: str, group_order_number: str, rules: Dict[str, Any]) -> List[IndividualOrder]:
        orders: List[IndividualOrder] = []
        item_pattern = r"(\d+)x\s+(.+?)(?:\s{2,}|\s+-\s+|$)"
        guest_mod_pattern = r"([A-Za-z]+(?:\s+[A-Za-z]+)+)\s+-\s+(.+)$"

        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        current_item: Optional[str] = None
        current_qty = 0
        guest_assignments: List[dict] = []

        def flush() -> None:
            nonlocal current_item, current_qty, guest_assignments
            if not current_item or current_qty <= 0:
                current_item, current_qty, guest_assignments = None, 0, []
                return

            assigned = 0
            for g in guest_assignments:
                if assigned >= current_qty:
                    break
                mods: List[str] = []
                comments = ""
                if g.get("modification"):
                    mods.append(str(g["modification"]))
                if g.get("allergy"):
                    comments = f"ALLERGIES: {g['allergy']}"

                orders.append(
                    IndividualOrder(
                        group_order_number=group_order_number,
                        guest_name=str(g.get("guest_name") or "Unassigned"),
                        item_name=current_item,
                        modifications=mods,
                        comments=comments,
                    )
                )
                assigned += 1

            for i in range(assigned, current_qty):
                orders.append(
                    IndividualOrder(
                        group_order_number=group_order_number,
                        guest_name=f"Guest {i+1}",
                        item_name=current_item,
                        modifications=[],
                        comments="",
                    )
                )

            current_item, current_qty, guest_assignments = None, 0, []

        for line in lines:
            m_item = re.match(item_pattern, line)
            if m_item:
                flush()
                try:
                    current_qty = int(m_item.group(1))
                except (ValueError, TypeError):
                    current_qty = 0
                current_item = (m_item.group(2) or "").strip()
                continue

            m_guest = re.match(guest_mod_pattern, line)
            if m_guest and current_item:
                guest_name = (m_guest.group(1) or "").strip()
                mod_text = (m_guest.group(2) or "").strip()

                if "HAS ALLERGIES" in mod_text.upper():
                    allergy_match = re.search(r"HAS ALLERGIES\s*(.*)", mod_text, re.IGNORECASE)
                    allergy = allergy_match.group(1).strip() if allergy_match else ""
                    guest_assignments.append({"guest_name": guest_name, "modification": None, "allergy": allergy})
                else:
                    guest_assignments.append({"guest_name": guest_name, "modification": mod_text, "allergy": None})

        flush()
        return orders

    def _parse_individual_orders(
        self,
        text: str,
        pages: List[str],
        group_order_number: str,
        rules: Dict[str, Any],
        *,
        company_name: Optional[str] = None,
    ) -> List[IndividualOrder]:
        # Keep compatibility with your existing heuristics for Sharebite/Grubhub fallback
        if "Slip 1 of 1" in text:
            return self._parse_slip_format(text, group_order_number)

        guest_pattern_space = r"([A-Za-z]+(?:\s+[A-Za-z]+)*)\s+(\d+)\s+(\d+)"
        guest_pattern_slash = r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]*)?)\s+(\d+)\s*/\s*(\d+)"
        if re.search(guest_pattern_slash, text) or re.search(guest_pattern_space, text) or "Qty Description Price" in text:
            return self._parse_grubhub_format(pages, group_order_number, company_name=company_name)

        return self._parse_table_format(text, group_order_number)

    def _parse_slip_format(self, text: str, group_order_number: str) -> List[IndividualOrder]:
        orders: List[IndividualOrder] = []
        slips = re.split(r"Slip 1 of 1", text)

        for slip in slips[1:]:
            lines = [line.strip() for line in slip.split("\n") if line.strip()]
            if len(lines) < 2:
                continue

            guest_match = re.match(r"([A-Z][A-Za-z.\s]+)", lines[0])
            if not guest_match:
                continue
            guest_name = guest_match.group(1).strip()

            current_item: Optional[str] = None
            current_mods: List[str] = []
            current_comment = ""

            for line in lines[1:]:
                if any(skip in line for skip in ["Yext", "Terra -", "9th Avenue"]):
                    continue

                item_match = re.match(r"(\d+)x\s+(.+)$", line)
                if item_match:
                    if current_item:
                        orders.append(
                            IndividualOrder(
                                group_order_number=group_order_number,
                                guest_name=guest_name,
                                item_name=current_item,
                                modifications=current_mods,
                                comments=current_comment,
                            )
                        )
                    current_item = item_match.group(2).strip()
                    current_mods = []
                    current_comment = ""
                    continue

                if current_item and line.startswith("-"):
                    current_mods.append(line.lstrip("-").strip())
                elif current_item and line.lower().startswith("sp:"):
                    current_comment = line.split(":", 1)[-1].strip()

            if current_item:
                orders.append(
                    IndividualOrder(
                        group_order_number=group_order_number,
                        guest_name=guest_name,
                        item_name=current_item,
                        modifications=current_mods,
                        comments=current_comment,
                    )
                )

        return orders

    def _parse_grubhub_format(
        self, pages: List[str], group_order_number: str, *, company_name: Optional[str] = None
    ) -> List[IndividualOrder]:
        orders: List[IndividualOrder] = []
        guest_pattern = r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]*)?)\s+(\d+)\s*/\s*(\d+)"
        item_line_pattern = r"^(\d+)\s+(.+?)\s+\$([\d.]+)$"
        stop_line_pattern = r"^(Subtotal|Tax|Tip|TOTAL)\b|^Customer:|^Qty\b|^Description\b|^Price\b"
        skip_line_patterns = [
            r"^https?://",
            r"^https://",
            r"^Team Order Invoice$",
            r"^admin\.relay\.delivery",
            r"^\d+\s*/\s*\d+$",
            r"^\(\d{3}\)\s*\d{3}[-\s]?\d{4}$",
            r"^\d+\s+items?$",
        ]

        for page_text in pages:
            matches = list(re.finditer(guest_pattern, page_text))
            for i, match in enumerate(matches):
                guest_name = (match.group(1) or "").strip()
                start = match.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(page_text)
                section = page_text[start:end]
                current_item: Optional[str] = None
                current_mods: List[str] = []
                current_comment: str = ""

                for line in [ln.strip() for ln in section.split("\n") if ln.strip()]:
                    if re.match(stop_line_pattern, line, re.IGNORECASE):
                        continue

                    if any(re.search(p, line, re.IGNORECASE) for p in skip_line_patterns):
                        continue

                    if line == guest_name:
                        continue
                    if company_name and line.casefold() == company_name.strip().casefold():
                        continue

                    m_item = re.match(item_line_pattern, line)
                    if m_item:
                        if current_item:
                            orders.append(
                                IndividualOrder(
                                    group_order_number=group_order_number,
                                    guest_name=guest_name,
                                    item_name=current_item,
                                    modifications=current_mods,
                                    comments=current_comment,
                                )
                            )
                        current_item = (m_item.group(2) or "").strip()
                        current_mods = []
                        current_comment = ""
                        continue

                    if current_item and line.lower().startswith("instructions:"):
                        current_comment = line.split(":", 1)[-1].strip()
                        continue

                    if current_item:
                        current_mods.append(line)

                if current_item:
                    orders.append(
                        IndividualOrder(
                            group_order_number=group_order_number,
                            guest_name=guest_name,
                            item_name=current_item,
                            modifications=current_mods,
                            comments=current_comment,
                        )
                    )

        return orders

    def _parse_table_format(self, text: str, group_order_number: str) -> List[IndividualOrder]:
        orders: List[IndividualOrder] = []
        row_pattern = r"(\d+)x\s+([A-Za-z0-9].+?)\s{2,}([A-Z][A-Za-z.\s]+)$"
        for match in re.finditer(row_pattern, text):
            orders.append(
                IndividualOrder(
                    group_order_number=group_order_number,
                    guest_name=(match.group(3) or "").strip(),
                    item_name=(match.group(2) or "").strip(),
                    modifications=[],
                    comments="",
                )
            )
        return orders

    # ---- mapping helpers ----

    def _resolve_mapping(self, mapping: Optional[Dict[str, Any]], extracted: Dict[str, Any]) -> Any:
        if mapping is None:
            return None

        if isinstance(mapping, dict):
            if "value" in mapping:
                return mapping["value"]

            if "source" in mapping:
                source = str(mapping["source"])
                if source.startswith("platform_info."):
                    key = source.replace("platform_info.", "")
                    return self.platform_info.get(key)
                if source.startswith("main_order_info."):
                    key = source.replace("main_order_info.", "")
                    return extracted.get(key)
                return extracted.get(source)

        return None

    def _resolve_template(self, mapping: Optional[Dict[str, Any]], extracted: Dict[str, Any]) -> str:
        if mapping is None:
            return ""

        if isinstance(mapping, dict) and "template" in mapping:
            template = str(mapping.get("template") or "")
            sources = mapping.get("sources", {}) or {}
            values: Dict[str, Any] = {}

            for key, source in sources.items():
                source = str(source)
                if source.startswith("main_order_info."):
                    field = source.replace("main_order_info.", "")
                    values[key] = extracted.get(field) or ""
                else:
                    values[key] = extracted.get(source) or ""

            try:
                return template.format(**values)
            except KeyError:
                return ""

        return str(self._resolve_mapping(mapping, extracted) or "")
