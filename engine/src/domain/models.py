from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional
import json


@dataclass
class MainOrderInfo:
    """Order-level information."""
    business_client: str = ""
    client_name: str = ""
    client_information: str = ""
    order_subtotal: Optional[float] = None
    requested_pick_up_time: str = ""
    requested_pick_up_date: str = ""
    number_of_guests: int = 0
    delivery: str = ""


@dataclass
class GroupOrder:
    """Group order reference."""
    group_order_number: str = ""
    pick_time: str = ""


@dataclass
class IndividualOrder:
    """Individual guest order item."""
    group_order_number: str = ""
    guest_name: str = ""
    item_name: str = ""
    modifications: List[str] = field(default_factory=list)
    comments: str = ""


@dataclass
class ParsedOrder:
    """Complete parsed order result."""
    main_order_info: MainOrderInfo
    group_orders: List[GroupOrder] = field(default_factory=list)
    individual_orders: List[IndividualOrder] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "main_order_information": asdict(self.main_order_info),
            "group_orders": [asdict(g) for g in self.group_orders],
            "individual_orders": [asdict(i) for i in self.individual_orders],
            "metadata": self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def get_filename(self) -> str:
        info = self.main_order_info
        return f"{info.business_client} - {info.requested_pick_up_date} - {info.number_of_guests}"

    @property
    def platform(self) -> Optional[str]:
        return self.metadata.get("platform")

    @property
    def total_items(self) -> int:
        return len(self.individual_orders)
