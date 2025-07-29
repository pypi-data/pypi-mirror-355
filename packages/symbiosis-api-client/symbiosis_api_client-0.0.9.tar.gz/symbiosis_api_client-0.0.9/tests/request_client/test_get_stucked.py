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


def test_get_stucked(client, stuck_address):
    struck = client.get_stucked(stuck_address)
    assert isinstance(struck, models.StuckedResponseSchema)
    assert isinstance(struck.root, list)
    # assert len(struck.root) > 0  # TODO: test when there is some stucked item
    assert all(isinstance(item, models.StuckedResponseItem) for item in struck.root)
