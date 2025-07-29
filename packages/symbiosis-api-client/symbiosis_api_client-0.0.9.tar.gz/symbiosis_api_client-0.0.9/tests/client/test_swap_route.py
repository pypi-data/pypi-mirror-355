import pytest

from symbiosis_api_client import SymbiosisApiClient, models


@pytest.fixture
def client():
    c = SymbiosisApiClient()
    yield c
    c.close()


@pytest.fixture
def routes_list():
    return [
        # Eth USDT -> BSC USDT
        (
            {
                "chain_from": "Ethereum",
                "token_from": "USDT",
                "chain_to": "Tron",
                "token_to": "USDT",
                "amount": 100,
                "slippage": 200,
                "sender": "0x40d3eE6c444E374c56f8f0d9480DF40f2B6E6aEd",
                "recipient": "0x40d3eE6c444E374c56f8f0d9480DF40f2B6E6aEd",
                "raise_exception": True,
            },
            {
                "some_field_to_check": "its_value",
            },
        ),
        # Eth USDT -> TON USDT
        (
            {
                "chain_from": "Ethereum",
                "token_from": "USDT",
                "chain_to": "TON",
                "token_to": "USDT",
                "amount": 100,
                "slippage": 200,
                "sender": "0x40d3eE6c444E374c56f8f0d9480DF40f2B6E6aEd",
                "recipient": "UQD9qA1MlNDFAM-oVAFPERJlmeOF6Dl6BLI3EtS4BopVC3Ci",
                "raise_exception": True,
            },
            {
                "some_field_to_check": "its_value",
            },
        ),
    ]


def test_check_lookup_route(routes_list, client):
    for rr in routes_list:
        route_dict, _ = rr
        swap = client.create_swap(**route_dict)
        assert isinstance(swap, models.SwapResponseSchema)
