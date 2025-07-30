from threading import Thread
from time import sleep


class NoException(Exception):
    pass


class Caller:

    def __init__(self, func, args, kwargs):
        self.return_value = None
        self.done = False
        self.exception = None
        self.function = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.return_value = self.function(*self.args, **self.kwargs)

        except Exception as exc:
            self.exception = exc

        self.done = True

    def result(self):
        while not self.done:
            sleep(0.1)
        return self.return_value


class MultiThreader:
    def __init__(self, max_threads: int = 0, ignore_exceptions: bool = False):
        """
        :param max_threads: Max concurrent Threads; 0 is infinite
        :return:
        """
        self._threads: list[Thread] = []
        self.threads: list[Caller] = []
        self.max_threads = max_threads
        self.ignore_exceptions = ignore_exceptions

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and issubclass(exc_type, KeyboardInterrupt):
            while self.remove_finished_threads():
                print('\n\n')
                [print(thread.name) for thread in self._threads]
                sleep(2)

        try:
            while self.remove_finished_threads():
                sleep(0.1)

        except KeyboardInterrupt:
            while self.remove_finished_threads():
                print('\n\n')
                [print(thread.name) for thread in self._threads]
                sleep(2)

    def remove_finished_threads(self) -> int:
        for thread in self.threads:
            if thread.exception and not self.ignore_exceptions and not isinstance(thread.exception, NoException):
                raise thread.exception

        self._threads = [thread for thread in self._threads if thread.is_alive()]
        return len(self._threads)

    def add_thread(self, func: callable, *args, **kwargs) -> Caller:
        while self.remove_finished_threads() >= self.max_threads != 0:
            sleep(0.01)

        call_func = Caller(func=func, args=args, kwargs=kwargs)
        thread = Thread(target=call_func.run)
        thread.start()
        self._threads.append(thread)
        self.threads.append(call_func)
        return call_func
