"""A flexible, customizable timer for your Python code.

You can use `timevery.Timer` in several different ways:

1. As a **class**:

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

2. As a **context manager**:

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

3. As a **decorator**:

    @Timer("Locate")
    def locate():
        time.sleep(1)
        print("located")

    locate()
"""

__all__ = ["Timer", "TimerError"]

from .timer import Timer, TimerError
