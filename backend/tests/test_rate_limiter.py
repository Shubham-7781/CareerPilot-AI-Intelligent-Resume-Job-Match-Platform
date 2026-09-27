from app.services.rate_limiter import is_rate_limited, _memory_log


def test_rate_limiter_blocks_after_limit_exceeded():
    _memory_log.clear()
    key = "test-ip-rate-limit"
    limit = 5

    for _ in range(limit):
        assert is_rate_limited(key, limit, window_seconds=60) is False

    # One more request past the limit should be blocked
    assert is_rate_limited(key, limit, window_seconds=60) is True


def test_rate_limiter_tracks_keys_independently():
    _memory_log.clear()
    limit = 2

    assert is_rate_limited("ip-a", limit, window_seconds=60) is False
    assert is_rate_limited("ip-a", limit, window_seconds=60) is False
    assert is_rate_limited("ip-a", limit, window_seconds=60) is True

    # A different key must not be affected by ip-a's usage
    assert is_rate_limited("ip-b", limit, window_seconds=60) is False
