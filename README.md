# Parcel Fit

A small internal Django tool for selecting a shipping box for a multi-product ecommerce order. It evaluates physical fit, axis-aligned product rotation, and weight capacity, then chooses a box deterministically.

## Features

- Public landing page with authenticated operational workspace; product and box management with server-side validation, activation, and safe deletion controls.
- Cart-based order building with persistent quantity indicators.
- Centimetre/inch entry and display support. Dimensions are always converted to canonical centimetres before reaching the packing engine; weight is consistently kilograms.
- Order building with quantities, live total weight, persisted line-item snapshots, and persisted recommendation results.
- Per-box explanations for suitability or rejection.
- Dashboard, order history, responsive server-rendered interface, and Django admin.
- Actual placement data rendered in an interactive canvas-based 3D packing view; the browser never decides packing.
- 37 automated tests plus a GitHub Actions workflow.

## Units and selection rule

- Dimensions: centimetres internally (internal dimensions for boxes); entry/display supports centimetres and inches.
- Weight: kilograms.
- Cost: INR.

Among boxes which physically pack every item and satisfy capacity, Parcel Fit selects: (1) lowest shipping cost, (2) lowest unused volume, then (3) box code. This is deterministic.

## Packing architecture

`shipping/services/packing.py` is a pure domain layer, separate from requests, views, and templates. It expands quantities into individual item instances, checks weight and volume as early rejections, generates each unique axis-aligned orientation, then orders items by decreasing volume with stable tie-breaks.

It uses a rotation-aware best-fit decreasing heuristic. Free space is represented by disjoint rectangular cuboids using x=length, y=width, z=height. An item is placed at a cuboid origin and the remaining space is split into non-overlapping right, front, and above guillotine regions. Empty, duplicate, and contained spaces are removed. For robustness it searches the best three candidate placements at each decision point, in deterministic order, with a hard 600-node search limit. It is deliberately a bounded heuristic, not an exact global 3D bin-packing solver; a feasible arrangement can occasionally be missed.

## Historical integrity

Order items store the product name, SKU, dimensions, and weight used at checkout. Successful recommendations store a box snapshot as well. Editing or deactivating current catalogue data therefore does not alter how a past order is understood.

## Setup

Requires Python 3.13 (or a supported Django Python version).

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Use `/admin/` after creating an administrator with `python manage.py createsuperuser`.

## Testing

```powershell
python manage.py check
python manage.py test -v 2
```

The CI workflow runs migrations, Django checks, and the complete test suite on pushes and pull requests.

## Typical workflow

1. Add active products with real physical dimensions and weight.
2. Add active shipping boxes, using their internal dimensions and capacity.
3. Create an order and adjust quantities.
4. Choose **Find best box**.
5. Review the selected box or the per-box rejection explanation in the saved order.

## Project structure

- `shipping/models.py` — validated domain persistence and order snapshots.
- `shipping/services/packing.py` — independent packing geometry and bounded search.
- `shipping/services/recommendation.py` — candidate evaluation and business tie-breaks.
- `shipping/views.py`, `templates/`, `static/` — authenticated server-rendered operator UI, cart, and canvas visualizer.
- `shipping/tests.py` — models, geometry, recommendation, units, lifecycle, authentication, cart, and end-to-end tests.

## Limitations and next steps

The heuristic intentionally trades exhaustive packing completeness for predictable runtime and explainability. A future version could make the branch limit configurable or record placement diagrams, while retaining the same physical constraints and deterministic business rule.

## What did you learn?

I have been able to learn how to design models for products, boxes and order items and link them to a realistc business need. The most difficult thins was how to put the logic of recommending boxes into place, particularly with regard to the size of the products, rotation of products, number of products, weight capacity and products in the same order.
