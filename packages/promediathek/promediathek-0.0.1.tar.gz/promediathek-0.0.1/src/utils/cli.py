from threading import Thread
from time import sleep

from lib.pakete.progresspaket import Progresspaket


class ProCLI:

    def __init__(self):
        self.progresspakete: list[Progresspaket] = []
        self.exit = False
        self.last_print_text = ""

    def add_progresspaket(self, progresspaket: Progresspaket) -> None:
        self.progresspakete.append(progresspaket)

    def stop(self) -> None:
        self.exit = True

    def print_text(self) -> str:
        return '\n'.join([str(progresspaket) for progresspaket in self.progresspakete if not progresspaket.done])

    def run(self) -> None:
        while not self.exit:
            sleep(0.1)
            print_text = self.print_text()
            if print_text != self.last_print_text:
                self.last_print_text = print_text
                print("\033[2J\033[H", end='')
                print(print_text)


class CLIThreader:

    def __init__(self, cli: ProCLI):
        self.cli = cli

    def __enter__(self) -> None:
        self.thread = Thread(target=self.cli.run)
        self.thread.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cli.stop()
