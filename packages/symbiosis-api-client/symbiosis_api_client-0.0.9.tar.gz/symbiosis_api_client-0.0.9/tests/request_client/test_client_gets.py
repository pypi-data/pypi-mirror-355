import time

import pytest

from symbiosis_api_client import HttpxRequestClient, models


@pytest.fixture
def client():
    clnt = HttpxRequestClient()
    assert clnt.health_check() is True
    yield clnt
    clnt.close()


@pytest.fixture
def stuck_address():
    stuck_req = models.StuckedRequestSchema(
        address="0x1234567890abcdef1234567890abcdef12345678"
    )
    return stuck_req


def test_client_get_chains(client):
    chains = client.get_chains()
    assert isinstance(chains, models.ChainsResponseSchema)
    assert len(chains.root) > 30
    assert all(isinstance(c, models.ChainsResponseSchemaItem) for c in chains.root)


def test_client_get_routes(client):
    routes = client.get_direct_routes()
    assert isinstance(routes, models.DirectRoutesResponse)
    assert len(routes.root) > 0
    assert all(isinstance(r, models.DirectRoutesResponseItem) for r in routes.root)


def test_client_get_fees(client):
    fees = client.get_fees()
    assert isinstance(fees, models.FeesResponseSchema)
    assert isinstance(fees.fees, list)
    assert len(fees.fees) > 80
    assert all(isinstance(fee, models.FeesResponseItem) for fee in fees.fees)
    updat = fees.updatedAt // 1000
    assert isinstance(updat, int)
    assert updat > 0
    assert updat < time.time()


def test_client_get_tokens(client):
    tokens = client.get_tokens()
    assert isinstance(tokens, models.TokensResponseSchema)
    assert len(tokens.root) > 30
    assert all(
        isinstance(token, models.TokensResponseSchemaItem) for token in tokens.root
    )


def test_client_get_limits(client):
    limits = client.get_swap_limits()
    assert isinstance(limits, models.SwapLimitsResponseSchema)
    assert len(limits.root) > 100
    assert all(isinstance(c, models.SwapLimitsResponseSchemaItem) for c in limits.root)


def test_client_get_durations(client):
    limits = client.get_swap_durations()
    assert isinstance(limits, models.SwapDurationsResponseSchema)
    assert len(limits.root) > 30
    assert all(
        isinstance(c, models.SwapDurationsResponseSchemaItem) for c in limits.root
    )


def test_get_stucked(client, stuck_address):
    struck = client.get_stucked(stuck_address)
    assert isinstance(struck, models.StuckedResponseSchema)
    assert isinstance(struck.root, list)
    # assert len(struck.root) > 0  # TODO: test when there is some stucked item
    assert all(isinstance(item, models.StuckedResponseItem) for item in struck.root)
