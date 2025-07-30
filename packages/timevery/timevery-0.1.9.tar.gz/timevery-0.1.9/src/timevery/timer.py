from __future__ import annotations

import time
from collections import deque
from contextlib import ContextDecorator
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Union


class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class."""


@dataclass
class TimeRecord:
    total_time: float = 0.0
    time: deque[float] = field(default_factory=lambda: deque(maxlen=120))
    count: int = 0
    average: float = 0.0
    frequency: float = 0.0
    min: float = float("inf")
    max: float = float("-inf")

    def update(self, time: float):
        self.time.append(time)
        self.total_time += time
        self.count += 1
        self.average = self.total_time / self.count
        self.frequency = 1 / self.average
        self.min = min(self.min, time)
        self.max = max(self.max, time)


@dataclass
class Timer(ContextDecorator):
    name: str = "Timer"
    text: str = "Elapsed time of {name}: {seconds:0.4f} seconds. "
    initial_text: Union[bool, str] = False
    show_freq: bool = False
    show_report: bool = False
    report_throttle_times: int = 1
    auto_restart: bool = False
    logger: Callable = print

    def __init__(
        self,
        name: Optional[str] = "Timer",
        text: Optional[str] = "Elapsed time of {name}: {seconds:0.4f} seconds. ",
        initial_text: Union[bool, str] = False,
        period: Optional[float] = None,
        show_freq: Optional[bool] = False,
        show_report: Optional[bool] = False,
        report_throttle_times: Optional[int] = 1,
        auto_restart: Optional[bool] = False,
        logger: Optional[Callable] = print,
        time_function: Optional[Callable] = time.perf_counter,
    ):
        """Create a Timer.

        Args:
            name (Optional[str], optional): Timer's name. Defaults to "Timer".
            text (Optional[str]): Then text shown when `stop()` or `lap()` is called.
                Defaults to "Elapsed time of {name}: {seconds:0.4f} seconds. ".
                Available substitutions: {name}, {milliseconds}, {seconds}, {minutes}.
            initial_text (Union[bool, str], optional): The text shown when `start()` is called. Defaults to False.
            period (Optional[float]): Period of the timer. Defaults to None. Use with `sleep_until_next_period()`, `stop_and_sleep_until_next_period()`, `sleep_until_next_period_and_stop()`.
            show_freq (Optional[str]): Show frequency when `stop()` is called if is True. Defaults to False.
            show_report (Optional[str]): Show report when `stop()` is called if is True. Defaults to False.
            report_throttle_times (Optional[int]): Show report every `report_throttle_times` times. Defaults to 1.
            auto_restart: Optional[bool]: Restart the timer when `start()` is called if is True. Defaults to False.
            logger (Optional[Callable], optional): Callable to show logs. Defaults to `print`.
            time_function (Optional[Callable], optional): The function can return a number to indicate the time it be called.
                Defaults to `time.perf_counter()` in seconds. `time.time()`, `time.monotonic()`, `time.process_time()` are also available.
        """

        self.name = name
        self.text = text
        if isinstance(initial_text, bool):
            if initial_text:
                initial_text = "{name} started."
        elif not isinstance(initial_text, str):
            raise TimerError("initial_text must be a string or a boolean.")
        self.initial_text = initial_text
        self.period = period
        self.show_freq = show_freq
        self.show_report = show_report
        self.report_throttle_times = report_throttle_times
        self.auto_restart = auto_restart
        self.logger = logger
        self.time_function = time_function  # get a time in seconds
        self._records = {name: TimeRecord()}
        self._start_time = None
        self._lap_start_time = None

    def start(self):
        """Start a new timer."""
        if self._start_time is not None:
            if self.auto_restart:
                self.lap("auto-restart")
                self.stop()
            else:
                raise TimerError("Timer is running. Use .stop() to stop it")

        # Log initial text when timer starts
        if self.logger and self.initial_text:
            initial_text = self.initial_text.format(name=self.name)
            self.logger(initial_text)

        self._start_time = self.time_function()
        self._lap_start_time = self._start_time

    def lap(self, name: Optional[str] = None) -> float:
        """Record a lap time."""
        if name is None:
            name = str(len(self._records))
        else:
            try:
                name = str(name)
            except Exception as e:
                raise TimerError(
                    "name must be a string or can be convert to a string with `str()`."
                ) from e
        if self._start_time is None:
            raise TimerError("Timer is not running. Use .start() to start it")

        # Calculate elapsed time
        elapsed_time = self.time_function() - self._lap_start_time
        self._update_record(name, elapsed_time)
        self._lap_start_time = self.time_function()

        if self.logger:
            attributes = {
                "name": name,
                "milliseconds": elapsed_time * 1000,
                "seconds": elapsed_time,
                "minutes": elapsed_time / 60,
            }
            text = self.text.format(**attributes)
            self.logger(str(text))

        return elapsed_time

    def stop(
        self,
    ) -> float:
        """Stop the timer, and report the elapsed time."""
        if self._start_time is None:
            raise TimerError("Timer is not running. Use .start() to start it")

        # Calculate elapsed time
        elapsed_time = self.time_function() - self._start_time
        self._update_record(self.name, elapsed_time)
        self._start_time = None
        self._lap_start_time = None

        # Report elapsed time
        if self.logger:
            attributes = {
                "name": self.name,
                "milliseconds": elapsed_time * 1000,
                "seconds": elapsed_time,
                "minutes": elapsed_time / 60,
            }
            text = self.text.format(**attributes)

            if self.show_freq:
                freq = 1 / elapsed_time
                freq_text = f" Frequency: {freq:.2f} Hz"
                text += freq_text

            self.logger(str(text))
        if self.show_report:
            self.report()
        return elapsed_time

    def sleep_until_next_period(self, name: Optional[str] = "sleep"):
        """Sleep until the next period."""
        if self._start_time is None:
            raise TimerError("Timer is not running. Use .start() to start it.")
        if self.period is None:
            raise TimerError("Period is not set.")
        elapsed_time = self.time_function() - self._start_time
        if elapsed_time < self.period:
            time.sleep(self.period - elapsed_time)
        self.lap(name)

    def stop_and_sleep_until_next_period(self):
        """Stop the timer, and sleep until the next period."""
        elapsed_time = self.stop()
        if self.period is None:
            raise TimerError("Period is not set.")
        if elapsed_time < self.period:
            time.sleep(self.period - elapsed_time)

    def sleep_until_next_period_and_stop(self, name: Optional[str] = "sleep"):
        """Sleep until the next period, and stop the timer."""
        self.sleep_until_next_period(name)
        return self.stop()

    def report(self):
        times = self._records[self.name].count
        if not times % self.report_throttle_times == 0:
            return
        from rich import box
        from rich.console import Console
        from rich.table import Table

        c = Console()

        headers = [
            "Name",
            "Total(s)",
            "Average(s)",
            "Freq(Hz)",
            "Percent(%)",
            "Count",
            "Min",
            "Max",
        ]
        t = Table(show_header=True, header_style="bold magenta", box=box.MARKDOWN)
        for header in headers:
            t.add_column(header, justify="center")

        total_time = self._records[self.name].total_time
        for name, record in self._records.items():
            total = record.total_time
            count = record.count
            average = record.average
            freq = record.frequency
            min_time = record.min
            max_time = record.max
            percent = total / total_time * 100

            t.add_row(
                name,
                f"{total:.4f}",
                f"{average:.4f}",
                f"{freq:.4f}",
                f"{percent:.4f}",
                f"{count}",
                f"{min_time:.4f}",
                f"{max_time:.4f}",
            )
        c.print(t)

    def _update_record(self, name: str, time: float):
        if name not in self._records:
            self._records[name] = TimeRecord()
        self._records[name].update(time)

    def __enter__(self) -> "Timer":
        self.start()
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.stop()
