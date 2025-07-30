from colorsys import hsv_to_rgb
from random import randint
from typing import Tuple, List


def generate_rgb(hsv: List[float]) -> Tuple[float, ...]:
    """Generate rgb color by random hsv."""
    return tuple(
        (round(value, 3) for value in hsv_to_rgb(hsv[0], hsv[1], hsv[2])),
    )


def generate_hsv() -> List[float]:
    """Generate a list with HSV values"""
    return [
        round(randint(0, 255) / 360, 3),  # hue
        round(randint(60, 90) / 100, 3),  # saturation
        round(randint(70, 90) / 100, 3)  # brightness
    ]


def generate_palette(length: int) -> List[Tuple[float, ...]]:
    """Generate a palette color by length provided."""
    excluded_hue = set()
    final_colors = []
    count: int = 0

    while count < length:
        hsv = generate_hsv()
        hue = hsv[0]
        if hue not in excluded_hue:
            excluded_hue.add(hue)
            rgb = generate_rgb(hsv)
            final_colors.append(rgb)
            count += 1

    return final_colors


if __name__ == "__main__":
    print(generate_palette(300))
