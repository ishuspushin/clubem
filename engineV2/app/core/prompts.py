"""
Prompt management system for LLM interactions.
Applies: Template Method Pattern, Factory Pattern
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PromptType(Enum):
    """Types of prompts."""
    EXTRACTION = "extraction"
    CLASSIFICATION = "classification"
    VALIDATION = "validation"


@dataclass
class PromptTemplate:
    """Template for LLM prompts."""
    name: str
    platform: str
    prompt_type: PromptType
    template: str
    variables: list
    
    def format(self, **kwargs) -> str:
        """
        Format template with variables.
        
        Args:
            **kwargs: Variable values
            
        Returns:
            Formatted prompt
        """
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")


class PromptManager:
    """
    Manager for LLM prompts with template storage.
    
    Design Pattern: Factory Pattern, Template Method Pattern
    DSA: Hash Map for O(1) template lookup
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._templates: Dict[str, Dict[str, PromptTemplate]] = {}
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Load all prompt templates into memory."""
        try:
            # Extraction prompts for each platform
            extraction_templates = {
                'sharebite': self._get_sharebite_extraction_template(),
                'ezcater': self._get_ezcater_extraction_template(),
                'grubhub': self._get_grubhub_extraction_template(),
                'catercow': self._get_catercow_extraction_template(),
                'clubfeast': self._get_clubfeast_extraction_template(),
                'hungry': self._get_hungry_extraction_template(),
                'forkable': self._get_forkable_extraction_template(),
            }
            
            self._templates['extraction'] = extraction_templates
            
            self.logger.info(
                f"Loaded {len(extraction_templates)} extraction templates"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to load templates: {e}", exc_info=True)
            raise
    
    def _get_base_extraction_prompt(self) -> str:
        """Get base extraction prompt instructions."""
        return """You are an expert PDF data extractor specializing in restaurant group orders. Your task is to extract structured information with 100% accuracy and completeness.

**CRITICAL EXTRACTION RULES:**
1. **EXTRACT EVERYTHING:** Do not summarize or truncate. Capture every single detail.
2. **ACCURACY IS PARAMOUNT:** Double-check dates, times, and amounts.
3. **INFER LOGICALLY:**
   - If `order_subtotal` is missing, calculate it by summing individual item prices if available.
   - If `number_of_guests` is missing, count the number of individual orders/guests.
   - If `client_name` is generic (e.g., "Guest"), try to find the company name in the header/footer.
4. **MODIFICATIONS VS COMMENTS:**
   - **Modifications:** Structural changes to the item (e.g., "No Onions", "Add Chicken", "Gluten Free", "Coke"). These are ingredients or choices.
   - **Comments:** Delivery instructions (e.g., "Leave at front desk") or general notes (e.g., "Allergy Alert").
5. **GUEST NAMES:**
   - Preserve original format (e.g., "John D.", "John Doe", "J. Doe").
   - If a name is "Guest 1", "Guest 2", extract as-is but flag as placeholder if asked.
6. **OUTPUT FORMAT:**
   - Return ONLY valid JSON.
   - No markdown formatting (no ```json ... ```).
   - Ensure all arrays are properly closed.

**FIELD SPECIFIC INSTRUCTIONS:**
- `requested_pick_up_date`: Format as YYYY-MM-DD if possible, or keep original string if ambiguous.
- `group_order_pick_time`: Keep original format (e.g., "11:30 AM - 12:00 PM").
- `order_subtotal`: Extract numerical value (e.g., "123.45"). Remove '$'.
- `modifications`: MUST be a JSON Array of strings (e.g., ["No Cheese", "Extra Sauce"]).

"""
    
    def _get_sharebite_extraction_template(self) -> PromptTemplate:
        """Get Sharebite extraction template."""
        template = self._get_base_extraction_prompt() + """
**SHAREBITE ORDER STRUCTURE:**

Extract the following from this Sharebite PDF:

**ORDER-LEVEL:**
- Business Client: "Group Sharebite"
- Client Name: Company placing order
- Client Information: Full address and phone
- Group Order Number: Format YEX######
- Group Order Pick Time: Pickup/delivery time
- Order Subtotal: Dollar amount (numeric only)
- Requested Pick Up Date: Date in format
- Number of Guests: Integer count
- Delivery: "Pickup" or "Delivery"

**INDIVIDUAL ORDERS** (for EACH guest):
- Group Order Number: Same as above
- Guest Name: Full name with any floor/location info
- Item Name: Exact item name
- Modifications: List of strings (e.g., ["Chicken", "No Onion"])
- Comments: Special instructions

**PDF CONTENT:**
{pdf_text}

**OUTPUT FORMAT (JSON only):**
{{
    "order_level": {{
        "business_client": "Group Sharebite",
        "client_name": "",
        "client_information": "",
        "group_order_number": "",
        "group_order_pick_time": "",
        "order_subtotal": "",
        "requested_pick_up_date": "",
        "number_of_guests": 0,
        "delivery": ""
    }},
    "individual_orders": [
        {{
            "group_order_number": "",
            "guest_name": "",
            "item_name": "",
            "modifications": [],
            "comments": ""
        }}
    ]
}}
"""
        
        return PromptTemplate(
            name="sharebite_extraction",
            platform="sharebite",
            prompt_type=PromptType.EXTRACTION,
            template=template,
            variables=['pdf_text']
        )
    
    def _get_ezcater_extraction_template(self) -> PromptTemplate:
        """Get EzCater extraction template."""
        template = self._get_base_extraction_prompt() + """
**EZCATER ORDER STRUCTURE:**

Extract from this EzCater PDF:

**ORDER-LEVEL:**
- Business Client: "Group EzCater"
- Client Name: Delivery recipient company
- Client Information: Full delivery address, contact name, phone
- Group Order Number: Order # format
- Group Order Pick Time: Delivery time with window
- Order Subtotal: Subtotal before fees/tax (numeric only)
- Requested Pick Up Date: Delivery date
- Number of Guests: Headcount shown (or sum of items if missing)
- Delivery: Usually "Delivery"

**INDIVIDUAL ORDERS:**
NOTE: EzCater often shows quantities but NOT individual guest names.
- If guest names not provided, use "[Not provided]" or "Quantity: X"
- Group Order Number: Same as order level
- Guest Name: If available, otherwise "[Not provided]"
- Item Name: Menu item name
- Modifications: List of strings (e.g., ["Packaging: Individual", "Chicken"])
- Comments: Setup requirements, delivery instructions

**PDF CONTENT:**
{pdf_text}

**OUTPUT FORMAT (JSON only):**
{{
    "order_level": {{
        "business_client": "Group EzCater",
        "client_name": "",
        "client_information": "",
        "group_order_number": "",
        "group_order_pick_time": "",
        "order_subtotal": "",
        "requested_pick_up_date": "",
        "number_of_guests": 0,
        "delivery": ""
    }},
    "individual_orders": [
        {{
            "group_order_number": "",
            "guest_name": "",
            "item_name": "",
            "modifications": [],
            "comments": ""
        }}
    ]
}}
"""
        
        return PromptTemplate(
            name="ezcater_extraction",
            platform="ezcater",
            prompt_type=PromptType.EXTRACTION,
            template=template,
            variables=['pdf_text']
        )
    
    def _get_grubhub_extraction_template(self) -> PromptTemplate:
        """Get Grubhub extraction template."""
        template = self._get_base_extraction_prompt() + """
**GRUBHUB ORDER STRUCTURE:**

Extract from this Grubhub Team Order PDF:

**ORDER-LEVEL:**
- Business Client: "Group Grubhub"
- Client Name: Delivery company name
- Client Information: Delivery address, contact, phone
- Group Order Number: Order number format
- Group Order Pick Time: Delivery time
- Order Subtotal: Calculate from individual orders if not shown (numeric only)
- Requested Pick Up Date: Order date
- Number of Guests: Customer count (count unique names if not shown)
- Delivery: "Delivery" or "Pickup"

**INDIVIDUAL ORDERS** (Grubhub shows detailed per-guest receipts):
- Group Order Number: Same as order level
- Guest Name: Individual customer name
- Item Name: Menu item ordered
- Modifications: List of strings (e.g., ["Spicy", "Extra Rice"])
- Comments: Special instructions if present

**PDF CONTENT:**
{pdf_text}

**OUTPUT FORMAT (JSON only):**
{{
    "order_level": {{
        "business_client": "Group Grubhub",
        "client_name": "",
        "client_information": "",
        "group_order_number": "",
        "group_order_pick_time": "",
        "order_subtotal": "",
        "requested_pick_up_date": "",
        "number_of_guests": 0,
        "delivery": ""
    }},
    "individual_orders": [
        {{
            "group_order_number": "",
            "guest_name": "",
            "item_name": "",
            "modifications": [],
            "comments": ""
        }}
    ]
}}
"""
        
        return PromptTemplate(
            name="grubhub_extraction",
            platform="grubhub",
            prompt_type=PromptType.EXTRACTION,
            template=template,
            variables=['pdf_text']
        )
    
    def _get_catercow_extraction_template(self) -> PromptTemplate:
        """Get CaterCow extraction template."""
        template = self._get_base_extraction_prompt() + """
**CATERCOW ORDER STRUCTURE:**

CaterCow provides BOTH cover sheet and individual labels.

**ORDER-LEVEL (from cover sheet):**
- Business Client: "Group CaterCow"
- Client Name: Company name
- Client Information: Address, contact, phone
- Group Order Number: CaterCow Order ######
- Group Order Pick Time: Delivery time window
- Order Subtotal: Not always shown (calculate if possible, numeric only)
- Requested Pick Up Date: Delivery date
- Number of Guests: Headcount
- Delivery: "Delivery" usually

**INDIVIDUAL ORDERS (from labels):**
- Group Order Number: Same as order
- Guest Name: Name on label
- Item Name: Dish name
- Modifications: List of strings (Dietary, customizations, substitutions)
- Comments: Allergy info, special notes

**PDF CONTENT:**
{pdf_text}

**OUTPUT FORMAT (JSON only):**
{{
    "order_level": {{
        "business_client": "Group CaterCow",
        "client_name": "",
        "client_information": "",
        "group_order_number": "",
        "group_order_pick_time": "",
        "order_subtotal": "",
        "requested_pick_up_date": "",
        "number_of_guests": 0,
        "delivery": ""
    }},
    "individual_orders": [
        {{
            "group_order_number": "",
            "guest_name": "",
            "item_name": "",
            "modifications": [],
            "comments": ""
        }}
    ]
}}
"""
        
        return PromptTemplate(
            name="catercow_extraction",
            platform="catercow",
            prompt_type=PromptType.EXTRACTION,
            template=template,
            variables=['pdf_text']
        )
    
    def _get_clubfeast_extraction_template(self) -> PromptTemplate:
        """Get ClubFeast extraction template."""
        template = self._get_base_extraction_prompt() + """
**CLUBFEAST ORDER STRUCTURE:**

ClubFeast uses format HUE-L######-####.

**ORDER-LEVEL:**
- Business Client: "Group ClubFeast"
- Client Name: If shown
- Client Information: Pickup/delivery details
- Group Order Number: HUE format
- Group Order Pick Time: Time shown
- Order Subtotal: Dollar amount (numeric only)
- Requested Pick Up Date: Date
- Number of Guests: Item count or guest count
- Delivery: "Pickup" or "Delivery"

**INDIVIDUAL ORDERS (from labels):**
- Group Order Number: HUE number
- Guest Name: Name on label
- Item Name: Dish name
- Modifications: List of strings (Sauce choices, dietary info)
- Comments: Dietary tags, special requests

**PDF CONTENT:**
{pdf_text}

**OUTPUT FORMAT (JSON only):**
{{
    "order_level": {{
        "business_client": "Group ClubFeast",
        "client_name": "",
        "client_information": "",
        "group_order_number": "",
        "group_order_pick_time": "",
        "order_subtotal": "",
        "requested_pick_up_date": "",
        "number_of_guests": 0,
        "delivery": ""
    }},
    "individual_orders": [
        {{
            "group_order_number": "",
            "guest_name": "",
            "item_name": "",
            "modifications": [],
            "comments": ""
        }}
    ]
}}
"""
        
        return PromptTemplate(
            name="clubfeast_extraction",
            platform="clubfeast",
            prompt_type=PromptType.EXTRACTION,
            template=template,
            variables=['pdf_text']
        )
    
    def _get_hungry_extraction_template(self) -> PromptTemplate:
        """Get Hungry extraction template."""
        template = self._get_base_extraction_prompt() + """
**HUNGRY ORDER STRUCTURE:**

Hungry "Food Partner Order Form" - catering style.

**ORDER-LEVEL:**
- Business Client: "Group Hungry"
- Client Name: Client company if shown
- Client Information: Contact info
- Group Order Number: NYC#### or similar
- Group Order Pick Time: Pickup time
- Order Subtotal: Payout total (numeric only)
- Requested Pick Up Date: Event date
- Number of Guests: Headcount
- Delivery: Usually "Pickup"

**INDIVIDUAL ORDERS:**
NOTE: Hungry may show bulk items, not individual guest names.
- If bulk order, create entries based on quantities
- Group Order Number: Order number
- Guest Name: "[Not provided]" if bulk
- Item Name: Menu item
- Modifications: List of strings (Packaging info)
- Comments: Dietary info, vendor notes

**PDF CONTENT:**
{pdf_text}

**OUTPUT FORMAT (JSON only):**
{{
    "order_level": {{
        "business_client": "Group Hungry",
        "client_name": "",
        "client_information": "",
        "group_order_number": "",
        "group_order_pick_time": "",
        "order_subtotal": "",
        "requested_pick_up_date": "",
        "number_of_guests": 0,
        "delivery": ""
    }},
    "individual_orders": [
        {{
            "group_order_number": "",
            "guest_name": "",
            "item_name": "",
            "modifications": [],
            "comments": ""
        }}
    ]
}}
"""
        
        return PromptTemplate(
            name="hungry_extraction",
            platform="hungry",
            prompt_type=PromptType.EXTRACTION,
            template=template,
            variables=['pdf_text']
        )
    
    def _get_forkable_extraction_template(self) -> PromptTemplate:
        """Get Forkable extraction template."""
        template = self._get_base_extraction_prompt() + """
**FORKABLE ORDER STRUCTURE:**

Extract from Forkable order PDF:

**ORDER-LEVEL:**
- Business Client: "Group Forkable"
- Client Name: Company name
- Client Information: Delivery/pickup info
- Group Order Number: Order identifier
- Group Order Pick Time: Time
- Order Subtotal: Dollar amount (numeric only)
- Requested Pick Up Date: Date
- Number of Guests: Guest count
- Delivery: "Pickup" or "Delivery"

**INDIVIDUAL ORDERS:**
- Group Order Number: Order number
- Guest Name: Individual name
- Item Name: Menu item
- Modifications: List of strings (Options, Add-ons)
- Comments: Special instructions

**PDF CONTENT:**
{pdf_text}

**OUTPUT FORMAT (JSON only):**
{{
    "order_level": {{
        "business_client": "Group Forkable",
        "client_name": "",
        "client_information": "",
        "group_order_number": "",
        "group_order_pick_time": "",
        "order_subtotal": "",
        "requested_pick_up_date": "",
        "number_of_guests": 0,
        "delivery": ""
    }},
    "individual_orders": [
        {{
            "group_order_number": "",
            "guest_name": "",
            "item_name": "",
            "modifications": [],
            "comments": ""
        }}
    ]
}}
"""
        
        return PromptTemplate(
            name="forkable_extraction",
            platform="forkable",
            prompt_type=PromptType.EXTRACTION,
            template=template,
            variables=['pdf_text']
        )
    
    def get_extraction_prompt(
        self,
        platform: str,
        pdf_text: str
    ) -> str:
        """
        Get formatted extraction prompt for platform.
        
        Args:
            platform: Platform identifier
            pdf_text: Extracted PDF text
            
        Returns:
            Formatted prompt string
        """
        try:
            template = self._templates['extraction'].get(platform.lower())
            
            if not template:
                self.logger.warning(f"No template for platform: {platform}")
                # Use sharebite as default
                template = self._templates['extraction']['sharebite']
            
            prompt = template.format(pdf_text=pdf_text)
            return prompt
            
        except Exception as e:
            self.logger.error(f"Failed to get prompt: {e}", exc_info=True)
            raise
    
    def get_available_platforms(self) -> list[str]:
        """Get list of platforms with templates."""
        return list(self._templates['extraction'].keys())
