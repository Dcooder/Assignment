"""Deterministic axis-aligned packing with guillotine free-space subdivision.

Coordinates use x=length, y=width, z=height.  Every placement occupies the
origin of one disjoint free cuboid; splitting its remainder into right, front,
and above cuboids therefore never creates overlapping usable space.  Search is
bounded: at most the three best placements at each level are explored.
"""

from dataclasses import dataclass
from decimal import Decimal
from itertools import permutations

ZERO = Decimal("0")
MAX_BRANCHES = 3
MAX_SEARCH_NODES = 600


@dataclass(frozen=True)
class Item:
    key: str
    dimensions: tuple[Decimal, Decimal, Decimal]
    weight: Decimal = ZERO

    @property
    def volume(self):
        return self.dimensions[0] * self.dimensions[1] * self.dimensions[2]


@dataclass(frozen=True)
class Space:
    x: Decimal
    y: Decimal
    z: Decimal
    length: Decimal
    width: Decimal
    height: Decimal

    @property
    def volume(self):
        return self.length * self.width * self.height

    @property
    def dimensions(self):
        return (self.length, self.width, self.height)


def orientations(dimensions):
    """Return sorted, deduplicated axis-aligned orientations."""
    return tuple(sorted(set(permutations(dimensions))))


def fits(dimensions, space):
    return all(
        value <= capacity for value, capacity in zip(dimensions, space.dimensions)
    )


def split_space(space, dimensions):
    """Guillotine partition around an item placed at a free-space origin."""
    l, w, h = dimensions
    spaces = (
        Space(
            space.x + l, space.y, space.z, space.length - l, space.width, space.height
        ),
        Space(space.x, space.y + w, space.z, l, space.width - w, space.height),
        Space(space.x, space.y, space.z + h, l, w, space.height - h),
    )
    return prune_spaces(spaces)


def contains(outer, inner):
    return (
        outer.x <= inner.x
        and outer.y <= inner.y
        and outer.z <= inner.z
        and outer.x + outer.length >= inner.x + inner.length
        and outer.y + outer.width >= inner.y + inner.width
        and outer.z + outer.height >= inner.z + inner.height
    )


def prune_spaces(spaces):
    unique = sorted(
        {s for s in spaces if s.length > ZERO and s.width > ZERO and s.height > ZERO},
        key=lambda s: (s.x, s.y, s.z, s.length, s.width, s.height),
    )
    return tuple(
        s
        for s in unique
        if not any(other != s and contains(other, s) for other in unique)
    )


def _candidates(item, spaces):
    result = []
    for space_index, space in enumerate(spaces):
        for orientation in orientations(item.dimensions):
            if fits(orientation, space):
                residual = (
                    space.volume - orientation[0] * orientation[1] * orientation[2]
                )
                dimensional_waste = sum(
                    capacity - value
                    for value, capacity in zip(orientation, space.dimensions)
                )
                score = (
                    residual,
                    dimensional_waste,
                    space.x,
                    space.y,
                    space.z,
                    orientation,
                    space_index,
                )
                result.append((score, space_index, orientation))
    return sorted(result, key=lambda candidate: candidate[0])


def pack(
    items, box_dimensions, max_branches=MAX_BRANCHES, max_search_nodes=MAX_SEARCH_NODES
):
    """Pack items; returns a structured deterministic result, never a boolean."""
    box_dimensions = tuple(Decimal(d) for d in box_dimensions)
    ordered = tuple(
        sorted(
            items,
            key=lambda i: (
                -i.volume,
                -max(i.dimensions),
                -sorted(i.dimensions)[-2],
                i.key,
            ),
        )
    )
    initial = (Space(ZERO, ZERO, ZERO, *box_dimensions),)

    for item in ordered:
        if not any(
            fits(orientation, initial[0])
            for orientation in orientations(item.dimensions)
        ):
            return {
                "success": False,
                "reason": "item_does_not_fit",
                "placements": [],
                "item": item.key,
            }

    nodes_visited = 0

    def search(index, spaces, placed):
        nonlocal nodes_visited
        nodes_visited += 1
        if nodes_visited > max_search_nodes:
            return None
        if index == len(ordered):
            return placed
        item = ordered[index]
        candidates = _candidates(item, spaces)
        for _, space_index, orientation in candidates[:max_branches]:
            space = spaces[space_index]
            replacement = split_space(space, orientation)
            next_spaces = prune_spaces(
                tuple(s for pos, s in enumerate(spaces) if pos != space_index)
                + replacement
            )
            result = search(
                index + 1,
                next_spaces,
                placed
                + (
                    {
                        "item": item.key,
                        "x": space.x,
                        "y": space.y,
                        "z": space.z,
                        "dimensions": orientation,
                    },
                ),
            )
            if result is not None:
                return result
        return None

    placements = search(0, initial, ())
    if placements is None:
        return {
            "success": False,
            "reason": "packing_failed",
            "placements": [],
            "nodes_visited": nodes_visited,
        }
    return {
        "success": True,
        "reason": None,
        "placements": list(placements),
        "nodes_visited": nodes_visited,
    }


def evaluate(items, box_dimensions, max_weight):
    total_weight = sum((item.weight for item in items), ZERO)
    if total_weight > Decimal(max_weight):
        return {"success": False, "reason": "weight_exceeded", "placements": []}
    total_volume = sum((item.volume for item in items), ZERO)
    box_volume = (
        Decimal(box_dimensions[0])
        * Decimal(box_dimensions[1])
        * Decimal(box_dimensions[2])
    )
    if total_volume > box_volume:
        return {"success": False, "reason": "volume_exceeded", "placements": []}
    return pack(items, box_dimensions)
