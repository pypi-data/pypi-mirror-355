import pytest

from symbiosis_api_client import SymbiosisApiClient, models


@pytest.fixture
def client():
    c = SymbiosisApiClient()
    yield c
    c.close()


@pytest.fixture
def symbols():
    # return tupples of symbol + chain_id
    retlist = [("WETH", 1), ("USDC", 56), ("USDT", 85918), ("USDT", 728126428)]
    return retlist


@pytest.fixture
def chain_dict():
    return {
        "BNB": 56,
        "TON": 85918,
        "Ethereum": 1,
        "Tron": 728126428,
    }


def test_find_chain_errors(client):
    with pytest.raises(Exception):
        client._lookup_chain()

    with pytest.raises(Exception):
        client._lookup_chain(chain_name="Ethereum", chain_id=0)


def test_find_chain(client, chain_dict):
    for chain_name, chain_id in chain_dict.items():
        chainobj = client._lookup_chain(chain_name=chain_name)
        assert isinstance(chainobj, models.ChainsResponseSchemaItem)
        assert chainobj.name == chain_name
        assert chainobj.id == chain_id

        chainobj = client._lookup_chain(chain_id=chain_id)
        assert isinstance(chainobj, models.ChainsResponseSchemaItem)
        assert chainobj.name == chain_name
        assert chainobj.id == chain_id


def test_find_token(client, symbols):
    for symbol, chain_id in symbols:
        token = client._lookup_token(symbol, chain_id)
        assert isinstance(token, models.TokensResponseSchemaItem)
        assert token.symbol == symbol
        assert token.chainId == chain_id
        # [i for i in client.tokens if 'eth' == i.symbol.lower()]
