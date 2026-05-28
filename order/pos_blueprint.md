# POS System Blueprint & Workflow (Strict MVP)

## 1. Core Logic & States
- EVERY order is a database record from the moment it's initiated. NO session-based carts.
- Order Model adjustments: 
  - `table` (ForeignKey to Table, null=True, blank=True)
  - `is_takeaway` (BooleanField, default=False)
  - `daily_number` (IntegerField). Increments sequentially every day for ALL orders, e.g., $daily\_number = max(daily\_number\_today) + 1$.
  - `status` (OPEN, PAID, CANCELLED)
- Pricing Math: $Total\_Price = \sum (quantity \times unit\_price\_snapshot)$.

## 2. Main POS Interface (Initial Load)
- Left Panel: Order details (Current active order, items, total, checkout button).
- Right Panel: Tables list, "Takeaway" button, Categories, and Menu Items.
- State: If no order is selected, the left panel is empty or prompts "Select a table or Takeaway".

## 3. Selecting Order Target (Table vs. Takeaway)
- Action: Cashier clicks a Table or the "Takeaway" button.
- Logic:
  - If Table: Check for an `OPEN` order for this table. If exists, load it. If not, create a new `OPEN` order ($is\_takeaway = False$).
  - If Takeaway: Create a new `OPEN` order ($is\_takeaway = True, table = Null$).
  - Assign a new continuous $daily\_number$ upon creation.

## 4. Modifying Order Items (HTMX)
- Action: Cashier clicks a Menu Item to add, or +/- buttons on the left panel to change quantity.
- Logic:
  - Add/Increase: Update or create `OrderItem` in DB. Fetch `unit_price_snapshot` directly from `MenuItem` at that exact moment.
  - Decrease/Remove: If $quantity - 1 == 0$, DELETE the `OrderItem` record entirely. Do NOT leave $quantity = 0$ in DB.
  - Recalculate: DB triggers/logic recalculates $Total\_Price$ immediately.
- UI Update: HTMX swaps the order summary panel (Left Panel) with the updated HTML.

## 5. Checkout & Print
- Action: Cashier clicks "Pay / Checkout".
- Logic:
  - Change Order `status` from `OPEN` to `PAID`.
  - Trigger receipt rendering (a clean, minimal HTML template).
  - Execute JS `window.print()` for the thermal printer.

## 6. Edge Cases & Error Handling
- Prevent adding items if no Order is currently active (return HTTP 400 or show HTMX error toast).
- Prevent modifying items on an order where $status \neq OPEN$.
