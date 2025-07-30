# timevery

Python timer for measuring execution time.

[![PyPI License](https://img.shields.io/pypi/l/timevery.svg)](https://pypi.org/project/timevery)
[![PyPI Version](https://img.shields.io/pypi/v/timevery.svg)](https://pypi.org/project/timevery)

## Quick Start

- Install `timevery`:

    ```bash
    pip install timevery
    ```

You can use `timevery.Timer` in several different ways:

1. As a **class**:

    ```python
    a = Timer("Detect", show_freq=True, logger=print)

    for i in range(5):
        a.start()

        time.sleep(0.1)
        a.lap("detect")

        if i % 2 == 0:
            time.sleep(0.1)
            a.lap("segment")

        time.sleep(0.2)
        a.lap("plot")
        a.stop()
    a.report()
    ```

    <details>
    <summary>Click to see the output</summary>

    ```bash
    >>>
        Detect started.
        Elapsed time of detect: 0.1002 seconds.
        Elapsed time of segment: 0.1003 seconds.
        Elapsed time of plot: 0.2003 seconds.
        Elapsed time of Detect: 0.4009 seconds.  Frequency: 2.49 Hz
        Detect started.
        Elapsed time of detect: 0.1001 seconds.
        Elapsed time of plot: 0.2004 seconds.
        Elapsed time of Detect: 0.3006 seconds.  Frequency: 3.33 Hz
        Detect started.
        Elapsed time of detect: 0.1001 seconds.
        Elapsed time of segment: 0.1002 seconds.
        Elapsed time of plot: 0.2004 seconds.
        Elapsed time of Detect: 0.4008 seconds.  Frequency: 2.49 Hz
        Detect started.
        Elapsed time of detect: 0.1001 seconds.
        Elapsed time of plot: 0.2004 seconds.
        Elapsed time of Detect: 0.3006 seconds.  Frequency: 3.33 Hz
        Detect started.
        Elapsed time of detect: 0.1002 seconds.
        Elapsed time of segment: 0.1003 seconds.
        Elapsed time of plot: 0.2004 seconds.
        Elapsed time of Detect: 0.4010 seconds.  Frequency: 2.49 Hz

        |  Name   | Total(s) | Average(s) | Freq(Hz) | Percent(%) | Count |  Min   |  Max   |
        |---------|----------|------------|----------|------------|-------|--------|--------|
        | Detect  |  1.8040  |   0.3608   |  2.7716  |  100.0000  |   5   | 0.3006 | 0.4010 |
        | detect  |  0.5008  |   0.1002   |  9.9831  |  27.7627   |   5   | 0.1001 | 0.1002 |
        | segment |  0.3008  |   0.1003   |  9.9739  |  16.6730   |   3   | 0.1002 | 0.1003 |
        |  plot   |  1.0018  |   0.2004   |  4.9909  |  55.5327   |   5   | 0.2003 | 0.2004 |
    ```

    </details>

2. As a **context manager**:

    ```python
    with Timer("MakeRobot", show_report=True) as t:
        time.sleep(1)
        t.lap("foot")
        time.sleep(1)
        t.lap("hand")
        time.sleep(1)
        t.lap("head")
        time.sleep(2)
        t.lap("body")
        time.sleep(1)
        t.lap("combine")
    ```

    <details>
    <summary>Click to see the output</summary>

    ```bash
    >>>
        MakeRobot started.
        Elapsed time of foot: 1.0011 seconds.
        Elapsed time of hand: 1.0012 seconds.
        Elapsed time of head: 1.0010 seconds.
        Elapsed time of body: 2.0021 seconds.
        Elapsed time of combine: 1.0012 seconds.
        Elapsed time of MakeRobot: 6.0068 seconds.
        |   Name    | Total(s) | Average(s) | Freq(Hz) | Percent(%) | Count |  Min   |  Max   |
        |-----------|----------|------------|----------|------------|-------|--------|--------|
        | MakeRobot |  6.0068  |   6.0068   |  0.1665  |  100.0000  |   1   | 6.0068 | 6.0068 |
        |   foot    |  1.0011  |   1.0011   |  0.9989  |  16.6663   |   1   | 1.0011 | 1.0011 |
        |   hand    |  1.0012  |   1.0012   |  0.9988  |  16.6679   |   1   | 1.0012 | 1.0012 |
        |   head    |  1.0010  |   1.0010   |  0.9990  |  16.6640   |   1   | 1.0010 | 1.0010 |
        |   body    |  2.0021  |   2.0021   |  0.4995  |  33.3309   |   1   | 2.0021 | 2.0021 |
        |  combine  |  1.0012  |   1.0012   |  0.9988  |  16.6674   |   1   | 1.0012 | 1.0012 |
    ```

    </details>

3. As a **decorator**:

    ```python
    @Timer("Locate")
    def locate():
        time.sleep(1)
        print("located")

    locate()
    ```

    <details>
    <summary>Click to see the output</summary>

    ```bash
    >>>
        Locate started.
        located
        Elapsed time of Locate: 1.0011 seconds.
    ```

    </details>

Some showcases are available in the [showcase.py](showcase.py).

## API

### `timevery.Timer()`

- `Timer()`

    ```python
    class Timer(ContextDecorator):
        def __init__(
            self,
            name: Optional[str] = "Timer",
            text: Optional[str] = "Elapsed time of {name}: {seconds:0.4f} seconds. ",
            initial_text: Union[bool, str] = False,
            period: Optional[float] = None,
            show_freq: Optional[bool] = False,
            show_report: Optional[bool] = False,
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
                auto_restart: Optional[bool]: Restart the timer when `start()` is called if is True. Defaults to False.
                logger (Optional[Callable], optional): Callable to show logs. Defaults to `print`.
                time_function (Optional[Callable], optional): The function can return a number to indicate the time it be called.
                    Defaults to `time.perf_counter()` in seconds. `time.time()`, `time.monotonic()`, `time.process_time()` are also available.
            """
    ```

- `Timer.start()`
- `Timer.stop()`
- `Timer.lap(name: Optional[str] = None)`
- `Timer.report()`

## Acknowledgement

Thanks to [this tutorial](https://realpython.com/python-timer/) and the [`codetiming`](https://github.com/realpython/codetiming) for the inspiration.
