import time
from datetime import timedelta

import httpx
import pytest

from symbiosis_api_client.limiter import SyncRateLimitedTransport


@pytest.fixture
def client():
    transport = SyncRateLimitedTransport.create(rate=1, period=timedelta(seconds=1))
    c = httpx.Client(transport=transport)
    yield c
    c.close()


@pytest.fixture
def client_10rps():
    transport = SyncRateLimitedTransport.create(rate=10, period=timedelta(seconds=1))
    c = httpx.Client(transport=transport)
    yield c
    c.close()


@pytest.fixture
def url():
    return "https://ifconfig.me"


def test_request(url, client):
    response = client.get(url)
    assert response.status_code == 200


def test_rate_limit(url, client):
    prev_time = None
    for i in range(5):
        response = client.get(url)
        this_time = time.time()
        assert response.status_code == 200
        if prev_time:
            elapsed = this_time - prev_time
            assert elapsed >= 0.9, f"Rate limit exceeded: {elapsed} seconds"
        prev_time = this_time


def test_quick_request(url, client_10rps):
    prev_time = None
    for i in range(10):
        response = client_10rps.get(url)
        this_time = time.time()
        assert response.status_code == 200
        if prev_time:
            elapsed = this_time - prev_time
            assert 0.1 <= elapsed <= 0.3, f"Rate limit exceeded: {elapsed} seconds"
        prev_time = this_time
