# Clubem

Clubem is an internal operations platform for processing large restaurant Group Orders received as PDFs from third‑party food‑ordering platforms.

It acts as the **control plane** between raw PDF uploads and finalized POS‑ready order outputs.

---

## What Clubem Does

- Accepts multiple PDF uploads per order
- Sends PDFs to an external extraction engine
- Validates and normalizes returned JSON
- Enables admin oversight and manual correction
- Generates standardized outputs:
  - Google Sheets
  - Excel
  - PDF
- Automatically emails results

---

## What Clubem Does NOT Do

- OCR or PDF parsing
- Image processing
- Data extraction logic

Those are handled by a dedicated external engine.

---

## Supported Platforms

- Grubhub
- Forkable
- Sharebite
- CaterCow
- EzCater
- ClubFeast
- Hungry

---

## User Roles

### Admin
- Full system access
- Manage platforms, templates, and users
- View and correct all orders

### User
- Upload PDFs
- View own uploads and orders
- No system configuration access

---

## Tech Stack

- Next.js (App Router)
- TypeScript
- Tailwind CSS
- uploadthing (uploads)
- External extraction engine (integration)

---

## Project Structure (High-Level)

- /login – Authentication UI
- /admin – Admin dashboard
- /app – User dashboard
- /components – Reusable UI components
- /templates – Output interpretation profiles

---

## Order Lifecycle

1. Upload PDFs
2. Engine extraction
3. Template validation
4. Manual review (if required)
5. Output generation
6. Email delivery

---

## Development Notes

- UI-only authentication
- Role-based routing
- No UI libraries
- Designed for extension with backend services

---

## Prisma Schema Explanation

This application uses Prisma + MongoDB with a document-centric data model designed for processing large, multi-platform group food orders and generating dynamic Excel / JSON outputs.

The schema is intentionally flexible to support:

Multiple ordering platforms (Forkable, Grubhub, etc.)

Admin-defined data fields

Changing order formats without database migrations

Final, normalized group orders as the system’s source of truth

Core Concepts
1. Platform-Driven Formats

Each food-ordering platform can define its own field structure and layout, allowing the system to adapt to different PDF formats and extraction rules.

2. Document-Centric Orders

Orders are stored as final, processed documents, not as transactional line items.
All dynamic business data lives in JSON, enabling future changes without schema updates.

3. Admin-Configurable Fields

Admins control:

What fields exist

Their order and grouping

How data is rendered (key-value vs repeated rows)

How arrays expand into Excel columns

Models
User

Represents an authenticated system user.

Roles:
- ADMIN: Full access (platforms, fields, approvals)
- STAFF: Can upload and process orders


Key fields

username – unique login identifier

password – hashed password

role – user role

isApproved – approval gate for access

orders – orders created by the user

Platform

Represents a food-ordering platform (e.g. Forkable, Grubhub).

Platforms define how orders are structured via associated fields.

Key fields

name – platform name

status – active or disabled

fields – dynamic field definitions for this platform

orders – processed orders from this platform

Order

Represents a final, processed group order.

This is the system’s single source of truth after PDF processing and review.

Key fields

status – lifecycle state of the order

groupOrderNumber – platform order identifier

data – JSON document containing all extracted and normalized order data

manuallyEdited – indicates if admin edits were applied

platform – platform the order originated from

createdBy – user who uploaded/processed the order

Why data is JSON

Field structure can change over time

New fields can be added without migrations

Admin-defined fields map directly into this object

Section

Defines logical groupings of fields and how they are rendered.

Examples:

Order Information

Guest Items

Key fields

name – section title

rank – display order

level – ORDER or GUEST

renderType

KEY_VALUE – label/value layout

REPEATED_BLOCK – repeated rows (e.g. guest items)

Fields

Defines individual data fields used to extract, store, and render order information.

Fields are platform-specific.

Key fields

name – display label

key – maps directly into Order.data

rank – ordering within section

level

ORDER – single value per order

GUEST – repeated per guest

value – data type (TEXT, NUMBER, DATE, ARRAY, etc.)

expandArray – whether ARRAY values expand into multiple columns

maxColumns – maximum number of columns for expansion

section – grouping and render behavior

platform – owning platform
