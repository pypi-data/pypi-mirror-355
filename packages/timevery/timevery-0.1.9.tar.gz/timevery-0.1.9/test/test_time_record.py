from collections import deque

from timevery.timer import TimeRecord


class TestTimeRecord:

    def test_init(self):
        record = TimeRecord()
        assert record.total_time == 0.0
        assert isinstance(record.time, deque)
        assert record.count == 0
        assert record.average == 0.0
        assert record.frequency == 0.0
        assert record.min == float("inf")
        assert record.max == float("-inf")
