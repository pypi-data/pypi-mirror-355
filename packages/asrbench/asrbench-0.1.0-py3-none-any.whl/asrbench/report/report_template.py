import pandas as pd
from abc import ABC, abstractmethod
from datetime import datetime, UTC
from .input_ import Input
from jinja2 import Template
from .plots.appearance import (
    enumerate_points,
    set_legend_position,
    set_facet_axis_labels,
)
from .plots.strategy import DispersionPlot
from .report_data import ReportData
from .template_loader import TemplateLoader
from pathlib import Path
from typing import Dict, Any
from weasyprint import HTML


class ReportTemplate(ABC):
    def generate_report(self) -> None:
        df: pd.DataFrame = self.process_data()
        self.create_plot(df)
        self.mount_report()

    @abstractmethod
    def process_data(self) -> pd.DataFrame:
        raise NotImplementedError("Implement process_data method.")

    @abstractmethod
    def create_plot(self, df: pd.DataFrame) -> None:
        raise NotImplementedError("Implement create_plot method.")

    @abstractmethod
    def mount_report(self) -> None:
        raise NotImplementedError("Implement mount_report method.")


class DefaultReport(ReportTemplate):
    def __init__(self, input_: Input) -> None:
        self._data = ReportData(input_.read_data())
        self._output: Path = Path(input_.filepath).absolute()
        self._result: Dict[str, Any] = {"file": self._output.name}

    def process_data(self) -> pd.DataFrame:
        mean: pd.DataFrame = self._data.group_by_mean("transcriber_name")

        self._result["configs"] = self._data.get_configs_dict()
        self._result["mean_stats"] = mean.round(3).to_dict(orient="index")

        mean["transcriber_name"] = [
            f"{n + 1} {name}" for n, name in enumerate(mean.index.tolist())
        ]

        return mean

    def create_plot(self, df: pd.DataFrame) -> None:
        strategy = DispersionPlot(
            x="accuracy",
            y="rtf",
            hue="transcriber_name",
        )
        plot = strategy.plot(df)

        enumerate_points(df, "accuracy", "rtf")
        set_legend_position(plot)
        set_facet_axis_labels(
            plot=plot,
            x_label="Accuracy (% higher is better)",
            y_label="RTFx (higher is better)",
            font_size=11.0,
        )

        plot_output_path: str = self._output.with_suffix(".png").__str__()
        plot.savefig(plot_output_path, dpi=300)

        self._result["plot_title"] = "Dispersion Plot"
        self._result["plot"] = plot_output_path
        self._result["plot_description"] = """sla"""

    def mount_report(self) -> None:
        loader = TemplateLoader()
        template: Template = loader.load("default.html")

        self._result["created_at"] = datetime.now(UTC)
        self._result["templates_dir"] = Path(__file__).parent.joinpath(
            "templates",
        )

        HTML(
            string=template.render(**self._result),
            base_url=self._output.parent,
        ).write_pdf(self._output.with_suffix(".pdf"))
