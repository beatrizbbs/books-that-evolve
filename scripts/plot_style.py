from __future__ import annotations

from collections.abc import Iterable

import matplotlib.pyplot as plt


PALETTE = [
    "#beae8c",
    "#cc8654",
    "#aab1aa",
    "#a07055",
    "#908f7d",
    "#cb8f8f",
    "#d6766f",
    "#d6a994",
    "#c27e7e",
    "#c7c0b6",
]
TEXT_COLOR = "#59514a"
BACKGROUND_COLOR = "#fbf8f1"
GRID_COLOR = "#d8d0c4"
LINE_WIDTH = 4.0
SECONDARY_LINE_WIDTH = 3.6
MARKER_SIZE = 5


def apply_light_academia_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": BACKGROUND_COLOR,
            "axes.facecolor": BACKGROUND_COLOR,
            "axes.edgecolor": TEXT_COLOR,
            "axes.labelcolor": TEXT_COLOR,
            "axes.titlecolor": TEXT_COLOR,
            "xtick.color": TEXT_COLOR,
            "ytick.color": TEXT_COLOR,
            "text.color": TEXT_COLOR,
            "grid.color": GRID_COLOR,
            "grid.alpha": 0.35,
            "font.family": "serif",
            "font.serif": ["DejaVu Serif", "Georgia", "Times New Roman", "serif"],
            "axes.prop_cycle": plt.cycler(color=PALETTE),
        }
    )


def color_map(labels: Iterable[str]) -> dict[str, str]:
    return {label: PALETTE[index % len(PALETTE)] for index, label in enumerate(labels)}
