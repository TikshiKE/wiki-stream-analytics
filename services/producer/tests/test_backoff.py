from producer.backoff import ExponentialBackoff


def test_delays_grow_exponentially_without_jitter() -> None:
    backoff = ExponentialBackoff(base=1.0, cap=60.0, jitter=0.0)
    assert [backoff.next_delay() for _ in range(5)] == [1.0, 2.0, 4.0, 8.0, 16.0]


def test_delay_is_capped() -> None:
    backoff = ExponentialBackoff(base=1.0, cap=60.0, jitter=0.0)
    for _ in range(20):
        delay = backoff.next_delay()
    assert delay == 60.0


def test_reset_starts_over() -> None:
    backoff = ExponentialBackoff(base=1.0, cap=60.0, jitter=0.0)
    backoff.next_delay()
    backoff.next_delay()
    backoff.reset()
    assert backoff.next_delay() == 1.0


def test_jitter_stays_within_bounds() -> None:
    backoff = ExponentialBackoff(base=4.0, cap=60.0, jitter=0.25)
    delay = backoff.next_delay()
    assert 3.0 <= delay <= 5.0
