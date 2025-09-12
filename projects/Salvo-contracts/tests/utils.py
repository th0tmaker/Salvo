# tests/utils.py
import inspect
from logging import Logger
from typing import Callable, Optional

from algokit_utils import CommonAppCallParams, PaymentParams, SendParams, micro_algo
from algokit_utils.models import SigningAccount
from algokit_utils.transactions.transaction_sender import SendAppTransactionResult
from algosdk.transaction import Transaction, wait_for_confirmation

from smart_contracts.artifacts.salvo.salvo_client import SalvoClient


# Define a helper method that creates of a payment transaction
def create_payment_txn(
    app: SalvoClient,
    sender: SigningAccount,
    amount: int,
    note: bytes | str | None = None,
) -> Transaction:
    return app.algorand.create_transaction.payment(
        PaymentParams(
            sender=sender.address,
            signer=sender.signer,
            receiver=app.app_address,
            amount=micro_algo(amount),
            note=note,
        )
    )


# Define a helper method that send an app call transaction to an abimethod inside the contract
def send_app_call_txn(
    logger: Logger,
    app: SalvoClient,
    sender: SigningAccount,
    method: Callable[..., SendAppTransactionResult],
    args: Optional[tuple] = None,
    max_fee: int = 1000,
    note: bytes | str | None = None,
    send_params: Optional[SendParams] = None,
    description: str = "App call",
) -> None:
    # Define the commonly used app call params
    params = CommonAppCallParams(
        max_fee=micro_algo(max_fee),
        sender=sender.address,
        signer=sender.signer,
        note=note,
    )

    # Perform try and except
    try:
        # Inspect the method signature and check it contains the 'args' field
        if "args" in inspect.signature(method).parameters:
            # Call with args (can be empty tuple)
            result = method(
                args=args or (),
                params=params,
                send_params=send_params,
            )
        else:
            # Call without args
            result = method(
                params=params,
                send_params=send_params,
            )

        # Wait 3 rounds for confirmation
        wait_for_confirmation(app.algorand.client.algod, result.tx_id, 3)

        # Assert transaction was successfully confirmed
        assert result.confirmation, f"{description} transaction failed confirmation."

        # If the send app transcation result has a return value that is not None
        if result.abi_return is not None:
            # Log the call abimethod return value
            logger.info(f"{description} ABI return value: {result.abi_return}")
    # Log error if failure
    except Exception as e:
        logger.warning(f"{description} transaction failed: {e}")
