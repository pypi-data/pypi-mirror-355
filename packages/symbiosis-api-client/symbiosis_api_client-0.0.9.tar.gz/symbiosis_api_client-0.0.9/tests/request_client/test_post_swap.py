import pytest

from symbiosis_api_client import HttpxRequestClient, models


@pytest.fixture
def client():
    clnt = HttpxRequestClient()
    assert clnt.health_check() is True
    yield clnt
    clnt.close()


@pytest.fixture
def token_amt_in():
    tokin = models.TokenAmountIn(
        address="",
        chainId=1,
        decimals=18,
        amount=50000000000000000,
    )
    return tokin


@pytest.fixture
def token_amt_out():
    tokout = models.TokenOut(
        address="",
        chainId=324,
        decimals=18,
        symbol="ETH",
    )
    return tokout


@pytest.fixture
def swap_request(token_amt_in, token_amt_out):
    swap_req = models.SwapRequestSchema(
        tokenAmountIn=token_amt_in,
        tokenOut=token_amt_out,
        from_="0xf93d011544e89a28b5bdbdd833016cc5f26e82cd",
        to="0xf93d011544e89a28b5bdbdd833016cc5f26e82cd",
        slippage=300,
        middlewareCall=None,
        revertableAddresses=None,
        selectMode=None,
        partnerAddress=None,
        refundAddress=None,
    )
    return swap_req


def test_post_swap(client, swap_request):
    swap_response = client.post_swap(swap_request)
    assert isinstance(swap_response, models.SwapResponseSchema)
