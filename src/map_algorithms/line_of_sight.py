"""
Line of sight calculations for visibility and targeting.
"""

from typing import TYPE_CHECKING, List, Set, Tuple

if TYPE_CHECKING:
    from src.world_map import WorldMap


def get_line_tiles(x1: int, y1: int, x2: int, y2: int) -> List[Tuple[int, int]]:
    """
    Get all tiles along a line from (x1, y1) to (x2, y2) using Bresenham's
    line algorithm. Returns list of (x, y) coordinates excluding the start point.
    """
    tiles = []
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    x, y = x1, y1
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1

    if dx > dy:
        err = dx // 2
        while x != x2:
            x += sx
            err -= dy
            if err < 0:
                y += sy
                err += dx
            tiles.append((x, y))
    else:
        err = dy // 2
        while y != y2:
            y += sy
            err -= dx
            if err < 0:
                x += sx
                err += dy
            tiles.append((x, y))

    return tiles


def has_clear_line_of_sight(
    world_map: "WorldMap", x1: int, y1: int, x2: int, y2: int
) -> bool:
    """
    Check if there is a clear line of sight between two points.
    Returns True if no walls block the view, False otherwise.
    """
    line_tiles = get_line_tiles(x1, y1, x2, y2)

    # Check all tiles except the final destination
    for x, y in line_tiles[:-1] if line_tiles else []:
        tile = world_map.get_tile(x, y)
        if tile is None or tile.type == "wall":
            return False

    return True


def calculate_visible_tiles(
    world_map: "WorldMap",
    origin_x: int,
    origin_y: int,
    view_radius: int,
) -> Set[Tuple[int, int]]:
    """
    Calculate all tiles visible from the origin point within view_radius.
    Uses raycasting to check line of sight to each potential tile.

    Args:
        world_map: The world map to check visibility on.
        origin_x: X coordinate of the viewer.
        origin_y: Y coordinate of the viewer.
        view_radius: Maximum viewing distance.

    Returns:
        Set of (x, y) tuples that are visible from the origin.
    """
    visible = set()
    visible.add((origin_x, origin_y))  # Origin is always visible

    # Cast rays to all tiles within the radius
    for dy in range(-view_radius, view_radius + 1):
        for dx in range(-view_radius, view_radius + 1):
            if dx == 0 and dy == 0:
                continue

            target_x = origin_x + dx
            target_y = origin_y + dy

            # Check if within map bounds
            if not world_map.is_in_bounds(target_x, target_y):
                continue

            # Check if within circular radius (not just square)
            distance_sq = dx * dx + dy * dy
            if distance_sq > view_radius * view_radius:
                continue

            # Check line of sight
            line_tiles = get_line_tiles(origin_x, origin_y, target_x, target_y)

            blocked = False
            for x, y in line_tiles:
                # Add the tile to visible (we can see up to and including walls)
                visible.add((x, y))

                tile = world_map.get_tile(x, y)
                if tile is None or tile.type == "wall":
                    blocked = True
                    break

            # If we reached the target without being blocked, add it
            if not blocked:
                visible.add((target_x, target_y))

    return visible
