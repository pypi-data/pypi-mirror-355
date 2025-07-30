from asrbench.benchmark import BenchmarkABC
from asrbench.config_loader import ConfigLoader
from asrbench.transcribers.registry import load_registers
from asrbench.report.report_template import DefaultReport
from asrbench.report.input_ import CsvInput, JsonInput, Input
from asrbench.report.report_data import ReportData
from .observer import RichObserver
from pathlib import Path
from rich.table import Table
from rich.console import Console
from typing_extensions import Annotated
from typer import Argument, Option

console = Console()


def run_benchmark(
        configfile: str = Argument(help='Path to config file.'),
        report: Annotated[
            bool, Option(help='Creates a report at the end of benchmark run.')
        ] = True
) -> None:
    load_registers(Path(__file__).parent.joinpath('transcribers'))

    loader: ConfigLoader = ConfigLoader(configfile, observer=RichObserver())
    benchmark: BenchmarkABC = loader.set_up_benchmark()
    output_filepath: str = benchmark.run()

    if report:
        report = DefaultReport(get_input(loader, output_filepath))
        report.generate_report()


def make_resume(filepath_: str = Argument(help='Path to result file.')) -> None:
    reader = get_input_by_ext(filepath_)
    data = ReportData(reader.read_data())
    df = data.group_by_mean("transcriber_name").round(3)
    df = df.reset_index().rename(columns={"index": "transcriber_name"})
    table = Table()

    for col in df.columns:
        table.add_column(str(col))

    for row in df.values:
        table.add_row(*[str(value) for value in row])

    console.print(table)


def get_input(loader: ConfigLoader, filepath_: str) -> Input:
    match loader.get_output_type():
        case "csv":
            return CsvInput(filepath_)
        case "json":
            return JsonInput(filepath_)


def get_input_by_ext(filepath_: str) -> Input:
    match Path(filepath_).suffix:
        case ".csv":
            return CsvInput(filepath_)
        case ".json":
            return JsonInput(filepath_)
