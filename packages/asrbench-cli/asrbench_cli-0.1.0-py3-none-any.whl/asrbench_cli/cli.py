from . import __version__
from .commands import run_benchmark, make_resume
from typer import Typer, Option, Exit, Context
from rich.console import Console

console = Console()
app = Typer(add_completion=False)

app.command(
    name='run',
    help='Run the benchmark with the configuration provided.',
)(run_benchmark)

app.command(
    name='resume',
    help='Displays a table with the averages of each transcribe system.',
)(make_resume)


def version(flag: bool) -> None:
    if flag:
        console.print(f'v{__version__}')
        raise Exit(0)


# noinspection PyUnusedLocal
@app.callback()
def typer_callback(
        ctx: Context,
        version: bool = Option(
            default=False,
            help='Show cli version and exit.',
            callback=version,
            is_flag=True,
            is_eager=True,
        ),
) -> None: ...


if __name__ == '__main__':
    app()
