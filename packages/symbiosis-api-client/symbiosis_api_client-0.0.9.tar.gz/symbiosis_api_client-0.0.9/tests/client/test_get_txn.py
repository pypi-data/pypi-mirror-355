import pytest

from symbiosis_api_client import SymbiosisApiClient, models


@pytest.fixture
def client():
    c = SymbiosisApiClient()
    yield c
    c.close()


def test_get_txn(client):
    txn_hash = "0xe514ea90e4bdb3947a41497aef4e03eec2210a964518ef1657a5ec09676c7435"
    txn = client.get_txn_status(chain_name="Ethereum", txn_hash=txn_hash)
    assert isinstance(txn, models.TxResponseSchema)
    assert txn.status.text == "Success"
