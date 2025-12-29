# PDF Extraction Schema Documentation

## Overview

This schema-driven approach allows you to define extraction rules in JSON files instead of writing Python code for each platform. The universal parser reads these schemas and extracts data accordingly.

## Schema Structure

```
{
  "platform_info": { ... },      // Platform identification
  "detection": { ... },          // How to identify this PDF type
  "document_structure": { ... }, // PDF page organization
  "extraction_rules": { ... },   // The actual extraction patterns
  "post_processing": { ... },    // Data cleanup rules
  "output_mapping": { ... },     // Map to final output format
  "examples": { ... }            // Test cases
}
```

---

## Section Details

### 1. `platform_info`

Basic platform identification:

```json
{
  "platform_id": "grubhub",
  "business_client": "Group - Grubhub",
  "document_types": ["cover_sheet", "order_labels"],
  "combined_document": true
}
```

### 2. `detection`

How to identify if a PDF belongs to this platform:

```json
{
  "method": "pattern_match",
  "min_matches": 2,
  "patterns": [
    "Team Order Invoice",
    "admin\\.relay\\.delivery",
    "TEAM DELIVERY"
  ]
}
```

- `min_matches`: How many patterns must match to confirm platform
- `patterns`: Regular expressions to search for

### 3. `extraction_rules`

The core extraction logic. Three main sections:

#### 3.1 `main_order_info`

Order-level fields from cover sheet:

```json
{
  "fields": {
    "order_number": {
      "pattern": "Order:\\s*(#[\\d\\s\\-—]+)",
      "group": 1,
      "type": "string",
      "required": true,
      "post_process": ["trim"]
    }
  }
}
```

**Field Properties:**

| Property | Description | Example |
|----------|-------------|---------|
| `pattern` | Regex pattern to match | `"Order:\\s*(#.+)"` |
| `group` | Capture group number | `1` |
| `type` | Data type | `"string"`, `"integer"`, `"currency"`, `"date"`, `"time"` |
| `required` | Is field mandatory? | `true` / `false` |
| `post_process` | Cleanup operations | `["trim", "normalize_whitespace"]` |
| `method` | Extraction method | `"pattern"`, `"section_extract"`, `"multi_line_pattern"` |
| `scope` | Where to search | `"cover_sheet"`, `"all"` |

**Extraction Methods:**

1. **`pattern`** (default): Simple regex match
   ```json
   {
     "pattern": "Total:\\s*\\$([\\d.]+)",
     "group": 1
   }
   ```

2. **`section_extract`**: Extract from a section of text
   ```json
   {
     "method": "section_extract",
     "section_start": "Deliver to:",
     "section_end": "TEAM DELIVERY",
     "line_index": 1
   }
   ```

3. **`multi_line_pattern`**: Handle text spanning multiple lines
   ```json
   {
     "method": "multi_line_pattern",
     "start_pattern": "Deliver by",
     "end_patterns": ["\\d+ customers", "QUESTIONS"]
   }
   ```

4. **`conditional`**: Choose value based on pattern match
   ```json
   {
     "method": "conditional",
     "conditions": [
       {"pattern": "TEAM DELIVERY", "value": "Delivery"},
       {"pattern": "PICKUP", "value": "Pickup"}
     ],
     "default": "Delivery"
   }
   ```

5. **`sum_field`**: Calculate sum from array
   ```json
   {
     "method": "sum_field",
     "source": "individual_orders",
     "field": "subtotal"
   }
   ```

#### 3.2 `guest_sections`

How to split the PDF into individual guest orders:

```json
{
  "section_detection": {
    "method": "pattern_split",
    "pattern": "([A-Z][a-zA-Z]+)\\s+(\\d+)\\s*/\\s*(\\d+)",
    "captures": {
      "guest_name": 1,
      "guest_number": 2,
      "total_guests": 3
    }
  },
  "validation": {
    "must_contain": ["Qty", "Description", "Price"]
  }
}
```

#### 3.3 `individual_orders`

Extract data from each guest section:

```json
{
  "fields": {
    "guest_name": {
      "source": "section_header",
      "capture_group": 1
    },
    "items": {
      "method": "table_extract",
      "table_header": "Qty\\s+Description\\s+Price",
      "row_pattern": "^(\\d+)\\s+(.+?)\\s+\\$([\\d.]+)$",
      "columns": {
        "quantity": {"group": 1, "type": "integer"},
        "item_name": {"group": 2, "type": "string"},
        "price": {"group": 3, "type": "currency"}
      }
    },
    "modifications": {
      "method": "collect_until",
      "start_after": "item_line",
      "end_before": "next_item_line|Subtotal",
      "skip_patterns": ["^\\$", "^Qty"]
    }
  }
}
```

### 4. `post_processing`

Data cleanup rules:

```json
{
  "modifications_vs_comments": {
    "comment_indicators": ["\\bplease\\b", "\\ballergy"],
    "modification_indicators": ["No\\s+\\w+", "Add\\s+\\w+"]
  },
  "text_cleanup": {
    "remove_patterns": ["https://.*"],
    "normalize_whitespace": true
  }
}
```

### 5. `output_mapping`

Map extracted data to final output format:

```json
{
  "main_order_information": {
    "business_client": {"source": "platform_info.business_client"},
    "client_name": {"source": "main_order_info.client_name"},
    "client_information": {
      "template": "{address}, Phone: {phone}",
      "sources": {
        "address": "main_order_info.delivery_address",
        "phone": "main_order_info.phone"
      }
    }
  }
}
```

---

## Pattern Syntax Reference

| Pattern | Matches | Example |
|---------|---------|---------|
| `\\s+` | One or more whitespace | Spaces, tabs, newlines |
| `\\d+` | One or more digits | `123` |
| `\\w+` | Word characters | `Hello123` |
| `[A-Z]` | Single uppercase letter | `A`, `B`, `C` |
| `(?:...)` | Non-capturing group | Groups without capturing |
| `(...)` | Capturing group | Extracts matched text |
| `.*?` | Non-greedy any chars | Minimal match |
| `.+` | One or more any chars | Greedy match |
| `^` | Start of line | |
| `$` | End of line | |
| `\\b` | Word boundary | |

---

## Post-Process Operations

| Operation | Description |
|-----------|-------------|
| `trim` | Remove leading/trailing whitespace |
| `normalize_whitespace` | Replace multiple spaces with single space |
| `remove_if_address` | Remove if looks like an address |
| `extract_datetime` | Parse date/time from text |
| `uppercase` | Convert to uppercase |
| `lowercase` | Convert to lowercase |

---

## Creating a New Schema

1. **Analyze the PDF**: Extract text and identify patterns
2. **Define detection**: Unique patterns to identify the platform
3. **Map main_order_info**: Order-level fields from cover sheet
4. **Define guest_sections**: How to split into individual orders
5. **Map individual_orders**: Guest-level fields
6. **Add post_processing**: Cleanup rules
7. **Define output_mapping**: Map to final format
8. **Add examples**: Test cases for validation

---

## Example: Adding Sharebite

```json
{
  "platform_info": {
    "platform_id": "sharebite",
    "business_client": "Group - Sharebite"
  },
  
  "detection": {
    "patterns": ["care@sharebite.com", "GO\\s*#", "Sharebite"]
  },
  
  "extraction_rules": {
    "main_order_info": {
      "fields": {
        "order_number": {
          "pattern": "GO\\s*#?\\s*([A-Z0-9]+)",
          "group": 1
        }
      }
    }
  }
}
```
