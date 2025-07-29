import pytest

from symbiosis_api_client import HttpxRequestClient, models


@pytest.fixture
def client():
    clnt = HttpxRequestClient()
    assert clnt.health_check() is True
    yield clnt
    clnt.close()


@pytest.fixture
def dummy_dict():
    d = {
        "tokenAmountIn": {
            "address": "",
            "chainId": 1,
            "decimals": 18,
            "amount": "50000000000000000",
        },
        "from": "0xf93d011544e89a28b5bdbdd833016cc5f26e82cd",
        "to": "0xf93d011544e89a28b5bdbdd833016cc5f26e82cd",
        "slippage": 300,
    }
    return d


@pytest.fixture
def payload(dummy_dict):
    return models.ZappingExactInRequestSchema.model_validate(dummy_dict)


def test_post_zapping(client, payload):
    # todo: check when the endpoint is available
    response = client.post_zapping(payload)
    assert isinstance(response, models.ZappingExactInResponseSchema)
