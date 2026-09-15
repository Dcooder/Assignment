# Test cases

This document records the test scenarios that are implemented in the project and the outcomes confirmed by the current Django suite.

## Automated coverage in shipping/tests.py

### Model validation
- Valid product creation succeeds.
- Blank product name is rejected.
- Duplicate SKU values are rejected.
- Non-positive dimensions are rejected.
- Non-positive weights are rejected.
- Valid box creation succeeds, including free shipping cost.
- Invalid box capacity / negative shipping cost is rejected.
- Duplicate box codes are rejected.
- Invalid order quantity values are rejected.

### Packing engine
- Exact fit succeeds.
- Larger dimension fails correctly.
- Rotation allows a product to fit into a box when dimensions are reoriented.
- Rotation failure is correctly detected.
- Duplicate dimension orientations are deduplicated.
- Weight boundary conditions are handled correctly.
- Volume rejection occurs when items exceed capacity.
- Volume check does not prove a feasible packing arrangement.
- Identical items fit into a box when feasible.
- Mixed items fit into a box when feasible.
- Packing results are deterministic.
- Split-space logic creates disjoint free-space regions.
- Pruning removes contained spaces.

### Recommendation logic
- Empty order returns no suitable box.
- Cheapest suitable box is selected.
- Equal-cost tie-breaking uses unused volume, then box code.
- Ineligible boxes are rejected and inactive boxes are ignored.
- No suitable box path is handled correctly.

### Views and workflow
- Dashboard and empty orders render correctly.
- Product form validation errors are handled.
- Complete order workflow persists recommendations.
- Empty or inactive orders are rejected.
- No-solution flow is handled correctly.
- Unauthenticated users can access the app.
- Cart add/update/checkout actions behave as expected.
- Delete operations are safe for historical data and hard for active usage.
- Inch-entry conversion stores centimetres and displays inches correctly.
- Negative HTML constraints and server validation remain active.

## Verified project outcome

The current repository passes the project’s Django validation and test suite:

- python manage.py check
- python manage.py test -v 1

Verified result: 37 tests passed, and Django reported no system-check issues.
