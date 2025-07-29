"""Business logic for the Symbiosis API client."""

import logging

from symbiosis_api_client.check_latest_commit import check_latest_commit

from . import exceptions as excep
from .load_static_chain_data import load_static_config, models_static
from .model_adapter import ModelsAdapter
from .request_client import HttpxRequestClient, httpx, models

logger = logging.getLogger("SymbiosisAPIClient")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class SymbiosisApiClient:
    """Symbiosis API client for interacting with the Symbiosis API."""

    def __init__(
        self,
        base_url: str | None = None,
        httpx_client: httpx.Client | None = None,
    ) -> None:
        """Initialize the Symbiosis API client."""
        self._hrc = HttpxRequestClient(
            base_url=base_url,
            httpx_client=httpx_client,
        )
        self._hrc.health_check(raise_exception=True)
        self._verify_mainnet_commit()

        self._chains: list[models.ChainsResponseSchemaItem] = []
        self._tokens: list[models.TokensResponseSchemaItem] = []
        self._routes: list[models.DirectRoutesResponseItem] = []
        self._fees: list[models.FeesResponseItem] = []
        self._swap_limits: list[models.SwapLimitsResponseSchemaItem] = []
        self._swap_durations: list[models.SwapDurationsResponseSchemaItem] = []
        self._swap_configs: list[models.SwapConfigsResponseItem] = []
        self._swap_tiers: list[models.SwapDiscountTiersResponseSchemaItem] = []
        self._swap_chains: list[int] = []

        static_cfg = load_static_config()
        self._static_chains: list[models_static.StaticChain] = static_cfg.chains

    def _verify_mainnet_commit(self) -> None:
        if not check_latest_commit(client=self._hrc.client):
            raise excep.InvalidCommit("Addresses are updated, please update client!")

    @property
    def swap_chains(self) -> list[int]:
        """Return a list of chain IDs."""
        if not self._swap_chains:
            self._swap_chains = self._load_swap_chains()
        return self._swap_chains

    def _load_swap_chains(self) -> list[int]:
        response = self._hrc.get_swap_chains()
        self._swap_chains = response.root
        return self._swap_chains

    @property
    def swap_tiers(self) -> list[models.SwapDiscountTiersResponseSchemaItem]:
        if not self._swap_tiers:
            self._swap_tiers = self._load_swap_tiers()
        return self._swap_tiers

    def _load_swap_tiers(self) -> list[models.SwapDiscountTiersResponseSchemaItem]:
        response = self._hrc.get_swap_tiers()
        self._swap_tiers = response.root
        return self._swap_tiers

    @property
    def swap_configs(self) -> list[models.SwapConfigsResponseItem]:
        if not self._swap_configs:
            self._swap_configs = self._load_swap_configs()
        return self._swap_configs

    def _load_swap_configs(self) -> list[models.SwapConfigsResponseItem]:
        response = self._hrc.get_swap_configs()
        self._swap_configs = response.root
        return self._swap_configs

    @property
    def chains(self) -> list[models.ChainsResponseSchemaItem]:
        if not self._chains:
            self._chains = self._load_chains()
        return self._chains

    @property
    def chain_names(self) -> list[str]:
        """Return a list of chain names."""
        return [chain.name for chain in self.chains]

    def _load_chains(self) -> list[models.ChainsResponseSchemaItem]:
        response = self._hrc.get_chains()
        self._chains = response.root
        return self._chains

    @property
    def tokens(self) -> list[models.TokensResponseSchemaItem]:
        if not self._tokens:
            self._tokens = self._load_tokens()
        return self._tokens

    def _load_tokens(self) -> list[models.TokensResponseSchemaItem]:
        response = self._hrc.get_tokens()
        self._tokens = response.root
        return self.tokens

    @property
    def routes(self) -> list[models.DirectRoutesResponseItem]:
        if not self._routes:
            self._routes = self._load_routes()
        return self._routes

    def _load_routes(self) -> list[models.DirectRoutesResponseItem]:
        response = self._hrc.get_direct_routes()
        self._routes = response.root
        return self._routes

    @property
    def fees(self) -> list[models.FeesResponseItem]:
        if not self._fees:
            self._fees = self._load_fees()
        return self._fees

    def _load_fees(self) -> list[models.FeesResponseItem]:
        response = self._hrc.get_fees()
        self._fees = response.fees
        return self._fees

    @property
    def swap_limits(self) -> list[models.SwapLimitsResponseSchemaItem]:
        if not self._swap_limits:
            self._swap_limits = self._load_swap_limits()
        return self._swap_limits

    def _load_swap_limits(self) -> list[models.SwapLimitsResponseSchemaItem]:
        response = self._hrc.get_swap_limits()
        self._swap_limits = response.root
        return self._swap_limits

    @property
    def swap_durations(self) -> list[models.SwapDurationsResponseSchemaItem]:
        if not self._swap_durations:
            self._swap_durations = self._load_swap_durations()
        return self._swap_durations

    def _load_swap_durations(self) -> list[models.SwapDurationsResponseSchemaItem]:
        response = self._hrc.get_swap_durations()
        self._swap_durations = response.root
        return self._swap_durations

    def close(self) -> None:
        """Close the HTTP client."""
        self._hrc.close()

    def _lookup_chain(
        self,
        chain_name: str | None = None,
        chain_id: int | None = None,
        raise_exception: bool = False,
    ) -> models.ChainsResponseSchemaItem | None:
        if chain_name is None and chain_id is None:
            raise ValueError("Either chain_name or chain_id must be provided.")
        if chain_name is not None and chain_id is not None:
            raise ValueError("Only one of chain_name or chain_id must be provided.")
        if chain_name is not None:
            for item in self.chains:
                if item.name == chain_name:
                    return item
        if chain_id is not None:
            for item in self.chains:
                if item.id == chain_id:
                    return item
        logger.warning("Chain not found: %s", chain_name or chain_id)
        if raise_exception:
            raise excep.ChainNotFound(f"Chain not found: {chain_name or chain_id}")
        return None

    def _lookup_token(
        self, symbol: str, chainId: int, raise_exception: bool = False
    ) -> models.TokensResponseSchemaItem | None:
        chain = self._lookup_chain(chain_id=chainId)
        if chain is None:
            return None
        for item in self.tokens:
            if item.symbol == symbol and item.chainId == chain.id:
                return item
        logger.warning("Token not found: %s on chain %s", symbol, chain.name)
        if raise_exception:
            raise excep.TokenNotFound(
                f"Token not found: {symbol} on chain {chain.name}"
            )
        return None

    def _lookup_static_chain(
        self,
        chain_id: int,
        raise_exception: bool = False,
    ) -> models_static.StaticChain | None:
        for item in self._static_chains:
            if item.id == chain_id:
                return item
        msg = f"Static chain not found: {chain_id}"
        logger.warning(msg)
        if raise_exception:
            raise excep.ChainNotFound(msg)
        return None

    def _lookup_static_token(
        self, symbol, chainobj: models_static.StaticChain, raise_exception: bool = False
    ) -> models_static.Stable | None:
        for item in chainobj.stables:
            if item.symbol == symbol:
                return item
        msg = f"Static token not found: {symbol} on chain {chainobj.rpc}"
        logger.warning(msg)
        if raise_exception:
            raise excep.TokenNotFound(msg)
        return None

    def get_txn_status(
        self, chain_name: str, txn_hash: str
    ) -> models.TxResponseSchema | None:
        chain_obj = self._lookup_chain(chain_name=chain_name)
        if not chain_obj:
            return None
        tx = models.Tx12(
            transactionHash=txn_hash,
            chainId=chain_obj.id,
        )
        return self._hrc.get_transaction(tx)

    def create_swap(
        self,
        chain_from: str,
        token_from: str,
        chain_to: str,
        token_to: str,
        amount: float,
        sender: str,
        recipient: str,
        slippage: int = 200,
        raise_exception: bool = False,
    ) -> models.SwapResponseSchema | None:
        """Create a swap request."""

        chain_from_obj = self._lookup_chain(
            chain_name=chain_from, raise_exception=raise_exception
        )
        chain_to_obj = self._lookup_chain(
            chain_name=chain_to, raise_exception=raise_exception
        )
        if not chain_from_obj or not chain_to_obj:
            return None

        static_chain_from_obj = self._lookup_static_chain(
            chain_id=chain_from_obj.id, raise_exception=raise_exception
        )

        static_chain_to_obj = self._lookup_static_chain(
            chain_id=chain_to_obj.id, raise_exception=raise_exception
        )

        if not static_chain_from_obj or not static_chain_to_obj:
            return None

        static_token_from_obj = self._lookup_static_token(
            symbol=token_from,
            chainobj=static_chain_from_obj,
            raise_exception=raise_exception,
        )

        static_token_to_obj = self._lookup_static_token(
            symbol=token_to,
            chainobj=static_chain_to_obj,
            raise_exception=raise_exception,
        )

        if not static_token_from_obj or not static_token_to_obj:
            return None

        token_from_obj = self._lookup_token(
            symbol=token_from,
            chainId=chain_from_obj.id,
            raise_exception=raise_exception,
        )

        token_to_obj = self._lookup_token(
            symbol=token_to,
            chainId=chain_to_obj.id,
            raise_exception=raise_exception,
        )
        if not token_from_obj or not token_to_obj:
            pass

        payload = ModelsAdapter.create_swap_request_payload(
            chain_from_obj=static_chain_from_obj,
            chain_to_obj=static_chain_to_obj,
            token_from_obj=static_token_from_obj,
            token_to_obj=static_token_to_obj,
            amount=amount,
            sender=sender,
            recipient=recipient,
            slippage=slippage,
        )
        try:
            resp = self._hrc.post_swap(payload)
            logger.info("Swap created successfully: %s", resp)
            return resp
        except Exception as e:
            logger.error("Error creating swap: %s", e)
            if raise_exception:
                msg = f"Error creating swap: {e}"
                raise excep.SwapCreationError(msg)
            return None
