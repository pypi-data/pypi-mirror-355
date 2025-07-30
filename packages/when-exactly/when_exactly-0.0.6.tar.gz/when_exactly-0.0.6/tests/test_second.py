import when_exactly as we


def test_assert_second_minute() -> None:
    second = we.Second(2020, 1, 1, 0, 0, 0)
    minute = second.minute()
    assert isinstance(minute, we.Minute)
    assert minute.start == we.Moment(2020, 1, 1, 0, 0, 0)
    assert minute.stop == we.Moment(2020, 1, 1, 0, 1, 0)


def test_second_end_of_minute() -> None:
    second = we.Second(2020, 1, 1, 0, 0, 59)
    assert second.stop == we.Moment(2020, 1, 1, 0, 1, 0)


def test_second_next() -> None:
    second = we.Second(2020, 1, 1, 0, 0, 0)
    assert next(second) == we.Second(2020, 1, 1, 0, 0, 1)


def test_from_moment() -> None:
    moment = we.Moment(2020, 1, 1, 0, 0, 0)
    second = we.Second.from_moment(moment)
    assert second == we.Second(2020, 1, 1, 0, 0, 0)
