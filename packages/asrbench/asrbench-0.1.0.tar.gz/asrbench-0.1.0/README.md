[:brazil: Versão Português Brasileiro](./README-pt.md)

# ASRBench 
### Evaluate, compare and find the best model for audio transcription.

## Index
- [ASRBench](#asrbench)
    - [Evaluate, compare and find the best model for audio transcription.](#evaluate-compare-and-find-the-best-model-for-audio-transcription)
  - [Index](#index)
  - [Introduction](#introduction)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Contribution](#contribution)
  - [About](#about)
  - [License](#license)

## Introduction
ASRBench is a framework developed in Python to create and run benchmarks of audio transcription systems.
It allows researchers and developers to compare different transcription systems in terms of accuracy,
performance and resource utilization.

## Installation
To install ASRBench, all you need is [Python 3.12+](https://www.python.org/downloads/) and pip. Use the
command below to install the latest version:

```sh
pip install asrbench
```

## Usage
ASRBench allows you to configure and run the benchmark using a YAML configuration file. This approach facilitates the
benchmark environment by allowing the user to define datasets, transcribers and output parameters in a simple and declarative way.
parameters in a simple and declarative way. For more details on the structure of the configuration file, go to
[documentation](https://asrbench.github.io/asrbench/configuration).

Below is an example of the configuration file structure:

```yaml
# data output configuration
output:
  type: "csv"
  dir: "./results"
  filename: "example_filename"

# configuration of datasets
datasets:
  dataset1:
    audio_dir: "resources/common_voice_05/wav"
    reference_dir: "resources/common_voice_05/txt"

# transcription system configuration
transcribers:
  faster_whisper_medium_int8:
    asr: "faster_whisper"
    model: "medium"
    compute_type: "int8"
    device: "cpu"
    beam_size: 5
    language: "en"  
```

With the configuration file ready, just create a Python script to read the file and set up the benchmark environment.
See an example below:

```python
from asrbench.config_loader import ConfigLoader

loader = ConfigLoader("path/to/configfile.yml")
benchmark = loader.set_up_benchmark()
benchmark.run()
```

If you also want to generate a PDF report from the data generated in the benchmark, just add the following
code snippet:

```python
from asrbench.report.report_template import DefaultReport
from asrbench.report.input_ import CsvInput
...

output_path = benchmark.run()
report = DefaultReport(CsvInput(output_filepath))
report.generate_report()

```

If you prefer a more direct and simplified solution, you can check out [asrbench-cli](https://github.com/ASRBench/asrbench-cli).

## Contribution
If you want to contribute to ASRBench, see [CONTRIBUTING.md](./CONTRIBUTING.md) for information on how to set up the
development environment and the necessary dependencies. The main development tools are defined
in the file [pyproject.toml](./pyproject.toml) and are managed with [Poetry](https://python-poetry.org/docs/#installation).

## About
ASRBench was developed as part of a course completion project to explore and evaluate the efficiency of audio transcription models.
of audio transcription models. The academic project provides a detailed analysis of the framework's development,
as well as the challenges and results obtained during the research. For more information, see [TCC](https://repositorio.animaeducacao.com.br/handle/ANIMA/48443).

## License
Distributed under the MIT license. See the [LICENSE](./LICENSE) file for more details.

[Go to top](#index)
