import logging
from datetime import timedelta
from typing import Optional

import httpx

from . import models as models
from .limiter import SyncRateLimitedTransport

logger = logging.getLogger("HttpxRequestClient")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

API_BASE_URL = "https://api.symbiosis.finance/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:137.0) Gecko/20100101 Firefox/137.0",
    "Accept": "*/*",
    "Accept-Language": "en,en-US;q=0.7,en-CA;q=0.3",
    "Content-Type": "application/json",
    "Origin": "https://app.symbiosis.finance",
    "DNT": "1",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Sec-GPC": "1",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}


class HttpxRequestClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(HttpxRequestClient, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        base_url: str | None = None,
        httpx_client: Optional[httpx.Client] = None,
    ) -> None:
        """Initialize the SymbiosisAPI client, singleton + rate limiting."""
        if base_url is None:
            base_url = API_BASE_URL

        if not httpx_client:
            transport = SyncRateLimitedTransport.create(
                rate=1, period=timedelta(seconds=1)
            )
            httpx_client = httpx.Client(
                headers=HEADERS,
                base_url=base_url,
                transport=transport,
                timeout=10.0,
            )
        self.client = httpx_client

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def health_check(self, raise_exception: bool = False) -> bool:
        # use self.client to check the health of the API
        response = self.client.get("/crosschain/health-check")
        if response.is_success:
            logger.info("Symbiosis API is healthy.")
            return True
        else:
            msg = (
                f"Symbiosis API is not healthy.{response.status_code} - {response.text}"
            )
            logger.error(msg)
            if raise_exception:
                response.raise_for_status()
            return False

    def get_chains(self) -> models.ChainsResponseSchema:
        """Returns the chains available for swapping."""
        response = self.client.get("/crosschain/v1/chains")
        response.raise_for_status()
        return models.ChainsResponseSchema.model_validate(response.json())

    def get_tokens(self) -> models.TokensResponseSchema:
        """Returns the tokens available for swapping."""
        response = self.client.get("/crosschain/v1/tokens")
        response.raise_for_status()
        return models.TokensResponseSchema.model_validate(response.json())

    def get_direct_routes(self) -> models.DirectRoutesResponse:
        """Returns the direct routes for all tokens."""
        response = self.client.get("/crosschain/v1/direct-routes")
        response.raise_for_status()
        return models.DirectRoutesResponse.model_validate(response.json())

    def get_fees(self) -> models.FeesResponseSchema:
        """Returns the current fees for all tokens."""
        response = self.client.get("/crosschain/v1/fees")
        response.raise_for_status()
        return models.FeesResponseSchema.model_validate(response.json())

    def get_swap_limits(self) -> models.SwapLimitsResponseSchema:
        """Returns the minimum and maximum allowed swap amounts for supported blockchain networks."""
        response = self.client.get("/crosschain/v1/swap-limits")
        response.raise_for_status()
        return models.SwapLimitsResponseSchema.model_validate(response.json())

    def get_swap_durations(self) -> models.SwapDurationsResponseSchema:
        """Returns estimated cross-chain swap execution times for supported blockchain networks.
        The duration is measured in seconds and is based on historical data."""
        response = self.client.get("/crosschain/v1/swap-durations")
        response.raise_for_status()
        return models.SwapDurationsResponseSchema.model_validate(response.json())

    def get_swap_configs(self):
        """Returns the swap configurations for supported blockchain networks."""
        response = self.client.get("/calculations/v1/swap/configs")
        response.raise_for_status()
        return models.SwapConfigsResponseSchema.model_validate(response.json())

    def get_swap_tiers(self):
        """Returns the swap tiers for supported blockchain networks."""
        response = self.client.get("/calculations/v1/swap/discount/tiers")
        response.raise_for_status()
        return models.SwapDiscountTiersResponseSchema.model_validate(response.json())

    def get_swap_chains(self):
        """Returns the swap chains for supported blockchain networks."""
        response = self.client.get("/calculations/v1/swap/discount/chains")
        response.raise_for_status()
        return models.SwapChainsResponseSchema.model_validate(response.json())

    def get_calc_token_price(
        self, payload: models.TokenPriceRequestSchema
    ) -> models.TokenPriceResponseSchema:
        """Returns the price of the token in USD.

        To get chain's carrier token price, leave address empty.
        """
        payload_dump = payload.model_dump(exclude_none=True, by_alias=True)
        response = self.client.post("/calculations/v1/token/price", json=payload_dump)
        response.raise_for_status()
        return models.TokenPriceResponseSchema.model_validate(response.json())

    def get_stucked(
        self, payload: models.StuckedRequestSchema
    ) -> models.StuckedResponseSchema:
        """Returns a list of stuck cross-chain operations associated with the specified address."""
        response = self.client.get(f"/crosschain/v1/stucked/{payload.address}")
        response.raise_for_status()
        return models.StuckedResponseSchema.model_validate(response.json())

    def get_transaction(self, payload: models.Tx12) -> models.TxResponseSchema:
        """Returns the operation by its transaction hash."""
        response = self.client.get(
            f"/crosschain/v1/tx/{payload.chainId}/{payload.transactionHash}"
        )
        response.raise_for_status()
        return models.TxResponseSchema.model_validate(response.json())

    def post_swap(
        self,
        payload: models.SwapRequestSchema,
    ) -> models.SwapResponseSchema:
        """Performs a cross-chain swap using the Symbiosis Finance API.

        :param payload: The payload containing the swap details.
        :return: The response from the Symbiosis Finance API.
        """

        payload_dump = payload.model_dump(exclude_none=True, by_alias=True)
        response = self.client.post("/crosschain/v1/swap", json=payload_dump)
        response.raise_for_status()
        return models.SwapResponseSchema.model_validate(response.json())

    def post_revert(
        self, payload: models.RevertRequestSchema
    ) -> models.RevertResponseSchema:
        """Returns calldata required to revert a stuck cross-chain operation.

        Data includes: swapping, bridging, zapping, interchain communicating.
        If a cross-operation gets stuck, Symbiosis automatically reverts such swaps.

        :param payload: The payload containing the revert details.
        :return: The response from the Symbiosis Finance API.
        """
        payload_dump = payload.model_dump(exclude_none=True, by_alias=True)
        response = self.client.post("/crosschain/v1/revert", json=payload_dump)
        response.raise_for_status()
        return models.RevertResponseSchema.model_validate(response.json())

    def post_batch_tx(
        self, payload: models.BatchTxRequestSchema
    ) -> models.BatchTxResponseSchema:
        """Returns the status of multiple cross-chain operations in a single request.

        Works the same way as /v1/tx, but accepts an array of { chainId, transactionHash }
        pairs to check the status of several operations at once.
        """
        payload_dump = payload.model_dump(exclude_none=True, by_alias=True)
        response = self.client.post("/crosschain/v1/batch-tx", json=payload_dump)
        response.raise_for_status()
        return models.BatchTxResponseSchema.model_validate(response.json())

    def post_zapping(
        self, payload: models.ZappingExactInRequestSchema
    ) -> models.ZappingExactInResponseSchema:
        """Returns calldata to execute a cross-chain zap operation.

        A cross-chain zap combines a cross-chain swap from the source token to
        the destination token with a subsequent deposit of the destination token
        into a liquidity pool managed by Symbiosis or a third-party DeFi protocol.

        :param payload: The payload containing the zap details.
        :return: The response from the Symbiosis Finance API.
        """

        payload_dump = payload.model_dump(exclude_none=True, by_alias=True)
        response = self.client.post(
            "/crosschain/v1/zapping/exact_in", json=payload_dump
        )
        response.raise_for_status()
        return models.ZappingExactInResponseSchema.model_validate(response.json())
