import pytest

# from dotenv import load_dotenv
# load_dotenv()
from symbiosis_api_client import HttpxRequestClient, models


@pytest.fixture
def client():
    clnt = HttpxRequestClient()
    yield clnt
    clnt.close()


@pytest.fixture
def txnlist():
    txndata = [
        {
            "chainId": 56,  # BNB
            "transactionHash": "0x6bb1d7b4709c395da1579f7ce5a95fb01026044c72a46be538921e443a615bfd",
        },
        {
            "chainId": 43114,  # avalanche
            "transactionHash": "0x8028a927848e99de1c39a256ac0a562da5e17a57683fd0b11a9788787c441169",
        },
        {
            "chainId": 137,  # polygon
            "transactionHash": "0xb038fedfa8234409bdcc74d32a5ff35cd44628ab5afc82a64aadd97478e090f5",
        },
        {
            "chainId": 42161,  # arbitrum
            "transactionHash": "0x1e4037e0bcc6224b2a1c1af4f35e7d01a9909f04f39d49ce0ae06b8c1be87c6e",
        },
    ]
    return txndata


@pytest.fixture
def txndata(txnlist):
    txn_models = []
    for tx in txnlist:
        txn_models.append(models.Tx12.model_validate(tx))
    return txn_models


def test_get_transaction(client, txndata):
    for txn in txndata:
        tnx_info = client.get_transaction(payload=txn)
        assert isinstance(tnx_info, models.TxResponseSchema)
        assert tnx_info.status.text.lower() == "success"


@pytest.fixture
def tnxbatch(txnlist):
    batch = models.BatchTxRequestSchema.model_validate({"txs": txnlist})
    return batch


def test_batch_txn_info(client, tnxbatch):
    txn_info = client.post_batch_tx(tnxbatch)
    assert isinstance(txn_info, models.BatchTxResponseSchema)
