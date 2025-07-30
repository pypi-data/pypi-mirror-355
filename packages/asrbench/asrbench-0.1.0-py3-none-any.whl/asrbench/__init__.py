__version__ = "0.1.0"

from asrbench.transcribers import (
    registry,
    abc_transcriber,
    factory,
    abc_factory,
)

from asrbench.report import (
    input_,
    report_template,
    report_data,
    template_loader,
    components,
)

from asrbench.report.plots import (
    appearance,
    strategy,
    colors_,
)
