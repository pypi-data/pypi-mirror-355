from . import models as models
from . import static_models as static_models


class ModelsAdapter:
    @staticmethod
    def create_token_out(token_to_obj: static_models.Stable) -> models.TokenOut:
        """Creates a TokenOut object from a static token object."""
        return models.TokenOut(
            # address="", it was like this in the original code. #
            # TODO: check for ethereum -> tron txn
            address=token_to_obj.address,
            chainId=token_to_obj.chainId,
            decimals=token_to_obj.decimals,
            symbol=token_to_obj.symbol,
        )

    @staticmethod
    def amount_to_decimals(amount: float, decimals: int) -> int:
        """Converts a float amount to a string with the specified number of decimals."""
        return int(amount * (10**decimals))

    @staticmethod
    def create_token_in(
        token_from_obj: static_models.Stable, amount: float
    ) -> models.TokenAmountIn:
        amt_dec = ModelsAdapter.amount_to_decimals(amount, token_from_obj.decimals)
        return models.TokenAmountIn(
            address=token_from_obj.address,
            amount=amt_dec,
            chainId=token_from_obj.chainId,
            decimals=token_from_obj.decimals,
            symbol=token_from_obj.symbol,
        )

    @staticmethod
    def create_swap_request_payload(
        chain_from_obj: static_models.StaticChain,
        chain_to_obj: static_models.StaticChain,
        token_from_obj: static_models.Stable,
        token_to_obj: static_models.Stable,
        amount: float,
        sender: str,
        recipient: str,
        slippage: int = 200,
        selectMode: models.SelectMode = models.SelectMode("best_return"),
    ) -> models.SwapRequestSchema:
        tokout = ModelsAdapter.create_token_out(token_to_obj)
        tokin = ModelsAdapter.create_token_in(token_from_obj, amount)

        mm = models.SwapRequestSchema(
            tokenAmountIn=tokin,
            tokenOut=tokout,
            from_=sender,  # type: ignore[call-arg]
            to=recipient,
            slippage=slippage,
            middlewareCall=None,
            revertableAddresses=None,
            selectMode=selectMode,
            partnerAddress=None,
            refundAddress=None,
        )

        return mm
