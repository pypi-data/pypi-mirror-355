import pytest

from symbiosis_api_client import HttpxRequestClient, models


@pytest.fixture
def client():
    clnt = HttpxRequestClient()
    assert clnt.health_check() is True
    yield clnt
    clnt.close()


@pytest.fixture
def payload():
    d = {
        "transactionHash": "0x6bb1d7b4709c395da1579f7ce5a95fb01026044c72a46be538921e443a615bfd",
        "chainId": 56,
    }
    return models.RevertRequestSchema.model_validate(d)


def no_test_post_revert(client, payload):
    # todo: check when the endpoint is available
    response = client.post_revert(payload)
    assert isinstance(response, models.RevertResponseSchema)
