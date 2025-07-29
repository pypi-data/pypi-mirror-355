import pytest

from symbiosis_api_client import HttpxRequestClient, models


@pytest.fixture
def client():
    clnt = HttpxRequestClient()
    assert clnt.health_check() is True
    yield clnt
    clnt.close()


def test_client_get_swap_configs(client):
    swap_config = client.get_swap_configs()
    assert isinstance(swap_config, models.SwapConfigsResponseSchema)
    assert len(swap_config.root) > 20


def test_get_swap_tiers(client):
    swap_tiers = client.get_swap_tiers()
    assert isinstance(swap_tiers, models.SwapDiscountTiersResponseSchema)
    assert len(swap_tiers.root) > 0


def test_get_swap_chains(client):
    chains = client.get_swap_chains()
    assert isinstance(chains, models.SwapChainsResponseSchema)
    assert len(chains.root) > 0


@pytest.fixture
def token_price_request():
    d = [
        {"address": "0x9328Eb759596C38a25f59028B146Fecdc3621Dfe", "chain_id": 85918},
        {"address": "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d", "chain_id": 56},
        {"address": "", "chain_id": 85918},
    ]
    return models.TokenPriceRequestSchema.model_validate(d)


def test_get_calc_token_price(client, token_price_request):
    token_prices = client.get_calc_token_price(token_price_request)
    assert isinstance(token_prices, models.TokenPriceResponseSchema)
    assert len(token_prices.root) == len(token_price_request.root)
    req_resp_pairs = zip(token_price_request.root, token_prices.root)
    for request, response in req_resp_pairs:
        assert isinstance(request, models.TokenPriceRequestSchemaItem)
        assert isinstance(response, models.TokenPriceResponseSchemaItem)
        assert request.address == response.address
        assert isinstance(response.price, float)
        assert response.price > 0
