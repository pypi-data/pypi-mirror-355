from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Any, Tuple, Dict, Hashable

sns.set_theme(style="darkgrid")


def set_legend_position(
    ax: Any,
    loc: str = "upper left",
    anchor: Tuple[float] = (0.75, 1.0),
    frame_on: bool = True,
) -> None:
    sns.move_legend(
        obj=ax,
        loc=loc,
        bbox_to_anchor=anchor,
        frameon=frame_on,
    )


def set_facet_axis_labels(
    plot: sns.FacetGrid, x_label: str, y_label: str, font_size: float = 10.0
) -> None:
    plot.set_axis_labels(x_var=x_label, y_var=y_label, fontsize=font_size)


def set_joint_axis_labels(
    plot: sns.JointGrid, x_label: str, y_label: str, font_size: float = 10.0
) -> None:
    plot.set_axis_labels(xlabel=x_label, ylabel=y_label, fontsize=font_size)


def enumerate_points(df: pd.DataFrame, x_axis: str, y_axis: str) -> None:
    palette: Dict[Hashable, Any] = _get_plot_palette(df)
    numbers = list(range(1, len(df.index.tolist()) + 1))

    for i, point in df.iterrows():
        plt.text(
            point[x_axis] + 0.005,
            point[y_axis] + 0.005,
            str(numbers.pop(0)),
            ha="left",
            va="bottom",
            fontsize=8,
            color=palette[point.name],
        )


def _get_plot_palette(df: pd.DataFrame) -> Dict[Hashable, Any]:
    hue_values = df.index.tolist()
    return dict(
        zip(
            hue_values,
            sns.color_palette(
                n_colors=len(hue_values),
            ),
        )
    )
