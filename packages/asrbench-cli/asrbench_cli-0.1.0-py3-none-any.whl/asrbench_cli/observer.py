from asrbench.observer import Observer
from rich.progress import Progress
from rich.console import Console


class RichObserver(Observer):
    def __init__(self) -> None:
        self.__progress = Progress(transient=False)
        self._task = None
        self._console = Console()

    def start_progress(self) -> None:
        self.__progress.__enter__()

    def update_progress(self, progress: float, message: str) -> None:
        if self._task is None:
            self._task = self.__progress.add_task(message, total=1.0)

        self.__progress.update(self._task, completed=progress)

    def notify(self, message: str) -> None:
        self._console.print(message)

    def finish(self) -> None:
        if self._task is not None:
            self.__progress.stop()
            self.__progress.remove_task(self._task)
            self._task = None
