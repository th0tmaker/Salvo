# tests/salvo_localnet_test.py
import json
import logging
from datetime import datetime
from typing import NamedTuple

import pytest
from algokit_utils import (
    AppClientCompilationParams,
    FundAppAccountParams,
    OnSchemaBreak,
    OnUpdate,
    PaymentParams,
    SendParams,
    TealTemplateParams,
    micro_algo,
)
from algokit_utils.algorand import AlgorandClient
from algokit_utils.models import SigningAccount
from algosdk.transaction import wait_for_confirmation

from smart_contracts.artifacts.plonk_verifier.lagrange_witness_calculator_client import (
    CalculateLagrangeWitnessArgs,
    LagrangeWitnessCalculatorFactory,
    LagrangeWitnessCalculatorMethodCallCreateParams,
)
from smart_contracts.artifacts.plonk_verifier.plonk_verifier_client import (
    PlonkVerifierBareCallCreateParams,
    PlonkVerifierClient,
    PlonkVerifierFactory,
)
from smart_contracts.artifacts.plonk_verifier.plonk_verifier_with_logs import (
    PlonkVerifierWithLogsBareCallCreateParams,
    PlonkVerifierWithLogsClient,
    PlonkVerifierWithLogsFactory,
)
from smart_contracts.artifacts.salvo.salvo_client import (
    SalvoClient,
    SalvoFactory,
    SalvoMethodCallCreateParams,
)
from tests.utils import send_app_call_txn
from utils.zk_getters import (
    get_zk_lagrange_witness,
    get_zk_proof,
    get_zk_proof_as_bytes,
    get_zk_public_signals,
    get_zk_root_of_unity_as_bytes,
    get_zk_vkey,
    get_zk_vkey_as_bytes,
)

# from .subscriber import (
#     AlgorandSubscriber,
#     create_subscriber,
# )

# VKEY_HEX = "0c00f31ab5823625090ce62aa6ca7518aed43c19597efcde4b89699f785b57f63cf6fb61991c01d00fd73135390e2df415d6e7125b0d2a2a9905bb4e05e025c8c31838b70057dc2e4134655ecb6e14df864a496c6447dbe4405619244e2d0108170275dadb4524ba602ce3e5e33bab66463a9f200a1774bf007f95be2f516326755085a5be0bfc98c4d6d4edbc273fc0018b41f2a760be868b9ed1e489a8a1949cff4cc7e72982c5174501c9d026934e5b13a0c8830c24500f777f5f217bd16715dd83342b5ed88dee6b736c833b84c432d97f6b337cc5854d82e4c3d9ab565e16a69c9b13bbc079a615df923fede40419001a1263eae13174c6dd85c7c0f7aa8cc4ab9deaf4bc51844a48b8f0f332a40166d83c47087d4ecaba8eabdc458e850d2159718c0f4efc8b9544065d2514f2bc8ba2377f2c6b4144f270fe38ad270b4d9ffc3cdc418437c2f281222852e43f0f9277fa9b627d5746672f1ae580ca4d64f7c241ed1df01f7878cb16cebfa0b5c3e616c9d0927fe7cec3dbc3681f853911b1cb79e7420a5f43cd91d41ce0d958153317f966a355f53dc8dabf763824f13addd707ea0d51471e303275de4536af069c04360e0a150cc9b76ba4c5c1ad816f1672baf222559a2a10ff4eccd1aaa195d33a15549a09caecc36d54a7eb161c0eb8c47da18ea60c787afa38053e499c109d33f1b5cdcb190184dc52545f47c52f83296ab31c925ff8f3180c9430575c00770edb41b5fa8fd318f878edab8c9d9308ceb03cddf176be687d0099c0b887100a9882606f827b0b68df14bf1a2cfa0e98d588db4b23de0280652d681eda9e65917606ef7aafc7274aa9e99b0fe9abc3d18bc2debf306f42bf928f6239b7c90b7602ca76ccc5339d7220c1f6e6736d4821dca005175d12500a07213adcc935432d4cf80472d586458cd0c6cd97f9e30e225dba250741b3eab9641c2aa11ee36ca07cbb8cb357843b88af1114f0c6b50f7a2da7852cc2fb7909656324ff695503adab95acb224c39123f182818286a6ad0bee365e954b0a81458c68c29590e0d622b33b8899703f16f2ffcbee2fc257000000000000000e000000000000000100000000000000020000000000000003168551071152798719667016500518019151568737276451525831503196981418651227967346087557263864360675191150a95a893af9fe055ae324275a5bd0eb3d8c159341ba0e2760f89aa18d2ef5cc1983640d57578e3864806446abb506812fb467b56359872f4932bcaf91d209ff70d768e238f42faea14d4326870a36307966f49d1957659b1750739a36140a3880ad5f146daee7e480adee15a7b0221dd48d35cf33a21fd33eb6818889fd32879937582f89469a7897096959cbba"
VKEY2HEX = "0c00f31ab5823625090ce62aa6ca7518aed43c19597efcde4b89699f785b57f63cf6fb61991c01d00fd73135390e2df415d6e7125b0d2a2a9905bb4e05e025c8c31838b70057dc2e4134655ecb6e14df864a496c6447dbe4405619244e2d0108170275dadb4524ba602ce3e5e33bab66463a9f200a1774bf007f95be2f516326755085a5be0bfc98c4d6d4edbc273fc0018b41f2a760be868b9ed1e489a8a1949cff4cc7e72982c5174501c9d026934e5b13a0c8830c24500f777f5f217bd16715dd83342b5ed88dee6b736c833b84c432d97f6b337cc5854d82e4c3d9ab565e16a69c9b13bbc079a615df923fede40419001a1263eae13174c6dd85c7c0f7aa8cc4ab9deaf4bc51844a48b8f0f332a40166d83c47087d4ecaba8eabdc458e850d2159718c0f4efc8b9544065d2514f2bc8ba2377f2c6b4144f270fe38ad270b4d9ffc3cdc418437c2f281222852e43f0f9277fa9b627d5746672f1ae580ca4d64f7c241ed1df01f7878cb16cebfa0b5c3e616c9d0927fe7cec3dbc3681f853911b1cb79e7420a5f43cd91d41ce0d958153317f966a355f53dc8dabf763824f13addd707ea0d51471e303275de4536af069c04360e0a150cc9b76ba4c5c1ad816f1672baf222559a2a10ff4eccd1aaa195d33a15549a09caecc36d54a7eb161c0eb8c47da18ea60c787afa38053e499c109d33f1b5cdcb190184dc52545f47c52f83296ab31c925ff8f3180c9430575c00770edb41b5fa8fd318f878edab8c9d9308ceb03cddf176be687d0099c0b887100a9882606f827b0b68df14bf1a2cfa0e98d588db4b23de0280652d681eda9e65917606ef7aafc7274aa9e99b0fe9abc3d18bc2debf306f42bf928f6239b7c90b7602ca76ccc5339d7220c1f6e6736d4821dca005175d12500a07213adcc935432d4cf80472d586458cd0c6cd97f9e30e225dba250741b3eab9641c2aa11ee36ca07cbb8cb357843b88af1114f0c6b50f7a2da7852cc2fb7909656324ff695503adab95acb224c39123f182818286a6ad0bee365e954b0a81458c68c29590e0d622b33b8899703f16f2ffcbee2fc257000000000000000e00000000000000010000000000000002000000000000000306ecb29d7853319169f87575d7d4e59516938ad445aed9dc7c7b706da5ce06a13cbd6eeda9c338beeb64874080abeee31333c853d054e888aa68bfcc4841dd1f18fbc89405d6760044c4937edd27dfdc2e600322c58f1644312403d4c83b4afc0727d07987d6580bfab9389fb2f7fada2d3f25437a97ac00c45bc1d17040f814588a89e0830b5d9f0a64d36a01a6838f00d8387b76c074e64972014465ae09e92c2840e8d0408f80281e600befe6ec4ee0c613caae9cf32b61de8a67ca9d96e1"
# Setup the logging.Logger
logger = logging.getLogger(__name__)


class AppFactories(NamedTuple):
    salvo_factories: dict[str, SalvoFactory]
    lwc_factories: dict[str, LagrangeWitnessCalculatorFactory]
    pvl_factories: dict[str, PlonkVerifierWithLogsFactory]
    pv_factories: dict[str, PlonkVerifierFactory]


class AppClients(NamedTuple):
    salvo_clients: dict[str, SalvoClient]
    pvl_clients: dict[str, PlonkVerifierWithLogsClient]
    pv_clients: dict[str, PlonkVerifierClient]

    # lwc_clients: dict[str, LagrangeWitnessCalculatorClient]


# Return an instance of the AlgorandSubscriber object to listen for network events
# @pytest.fixture(scope="session")
# def subscriber(algorand: AlgorandClient) -> AlgorandSubscriber:
#     return create_subscriber(
#         algod_client=algorand.client.algod,
#         indexer_client=algorand.client.indexer,
#         app_id=1001,
#         max_rounds_to_sync=100,
#     )


# Return an instance of the AlgorandClient object from the environment config
@pytest.fixture(scope="session")
def algorand() -> AlgorandClient:
    algorand = AlgorandClient.from_environment()
    algorand.set_default_validity_window(validity_window=1000)
    return algorand


# Return a dispenser account as SigningAccount object that will fund other accounts
@pytest.fixture(scope="session")
def dispenser(algorand: AlgorandClient) -> SigningAccount:
    return algorand.account.dispenser_from_environment()  # LocalNet dispenser account


# Generate a random account that will act as the default creator account for testing
@pytest.fixture(scope="session")
def creator(algorand: AlgorandClient, dispenser: SigningAccount) -> SigningAccount:
    # Create a random Algorand account to represent the creator account
    creator = algorand.account.random()

    # Send signed payment transaction using the Algorand client
    algorand.send.payment(
        PaymentParams(
            sender=dispenser.address,
            signer=dispenser.signer,
            receiver=creator.address,
            amount=micro_algo(50_000_000),
        )
    )
    # Return the creator account
    return creator


# Get the typed app factory of a given smart contract from the Algorand client
@pytest.fixture(scope="session")
def app_factories(
    algorand: AlgorandClient,
    creator: SigningAccount,
) -> AppFactories:
    proof = get_zk_proof()
    proof_bytes = get_zk_proof_as_bytes(proof)
    logger.info(proof_bytes.hex())
    logger.info(get_zk_lagrange_witness())
    logger.info(get_zk_vkey_as_bytes(get_zk_vkey(logger), logger))
    logger.info(get_zk_vkey(logger))

    # Define the on-deployment/compilation parameters
    salvo_template_params: TealTemplateParams = {
        "GEN_UNIX": int(datetime.now().timestamp()),
    }
    plonk_verifier_template_params: TealTemplateParams = {
        # "VERIFICATION_KEY": get_zk_vkey_as_bytes(get_zk_vkey(logger), logger),
        "VERIFICATION_KEY": bytes.fromhex(VKEY2HEX),
        "ROOT_OF_UNITY": get_zk_root_of_unity_as_bytes(),
    }

    salvo_factories = {
        "salvo_factory_1": algorand.client.get_typed_app_factory(
            SalvoFactory,
            default_sender=creator.address,
            default_signer=creator.signer,
            compilation_params=AppClientCompilationParams(
                deploy_time_params=salvo_template_params,
                updatable=True,
                deletable=None,
            ),
        )
    }
    lwc_factories = {
        "lwc_factory_1": algorand.client.get_typed_app_factory(
            LagrangeWitnessCalculatorFactory,
            default_sender=creator.address,
            default_signer=creator.signer,
            compilation_params=AppClientCompilationParams(
                deploy_time_params=plonk_verifier_template_params,
                updatable=None,
                deletable=None,
            ),
        )
    }
    pvl_factories = {
        "pvl_factory_1": algorand.client.get_typed_app_factory(
            PlonkVerifierWithLogsFactory,
            default_sender=creator.address,
            default_signer=creator.signer,
            compilation_params=AppClientCompilationParams(
                deploy_time_params=plonk_verifier_template_params,
                updatable=None,
                deletable=None,
            ),
        )
    }
    pv_factories = {
        "pv_factory_1": algorand.client.get_typed_app_factory(
            PlonkVerifierFactory,
            default_sender=creator.address,
            default_signer=creator.signer,
            compilation_params=AppClientCompilationParams(
                deploy_time_params=plonk_verifier_template_params,
                updatable=None,
                deletable=None,
            ),
        )
    }

    return AppFactories(
        salvo_factories=salvo_factories,
        lwc_factories=lwc_factories,
        pvl_factories=pvl_factories,
        pv_factories=pv_factories,
    )


# Create a factory that can generate an arbitrary amount of random localnet test accounts called Randy
@pytest.fixture(scope="session")
def randy_factory(algorand: AlgorandClient, dispenser: SigningAccount) -> dict:
    # Define the number of randy accounts that will be created and used for testing
    randy_accounts = 9

    # Create a list to store all the randy accounts that were randomly generated by the Algorand client
    randies = [algorand.account.random() for _ in range(randy_accounts)]

    # Create a list to store all the funding amounts (first randy gets 30_000_000, subsequent ones get 1_000_000 less)
    funding_amounts = [30_000_000 - i * 1_000_000 for i in range(randy_accounts)]

    # Take the matching indices of both lists and zip them into a tuple then iterate through a new list of these tuples
    for randy, amount in zip(randies, funding_amounts):
        algorand.send.payment(
            PaymentParams(
                sender=dispenser.address,
                signer=dispenser.signer,
                receiver=randy.address,
                amount=micro_algo(amount),
            )
        )

    # Return a dict with all randy accounts (output: dict[str, AddressAndSigner])
    return {f"randy_{i+1}": randy for i, randy in enumerate(randies)}


# Create smart contract client using factory deploy method
@pytest.fixture(scope="session")
def app_clients(algorand: AlgorandClient, app_factories: AppFactories) -> AppClients:
    salvo_clients = {}
    for name, factory in app_factories.salvo_factories.items():
        try:
            sc_client, deploy_result = factory.deploy(
                on_update=OnUpdate.ReplaceApp,
                on_schema_break=OnSchemaBreak.ReplaceApp,
                create_params=SalvoMethodCallCreateParams(
                    method="generate",
                    note=b'salvo:j{"concern":"txn.app_call;generate"}',
                ),
                # "delete_params": SalvoMethodCallDeleteParams(
                #     method="terminate",
                #     max_fee=micro_algo(5_000),
                #     note=b'salvo:j{"concern":"txn.app_call;terminate"}',
                # ),
            )
            client_name = name.replace("_factory", "_client")
            salvo_clients[client_name] = sc_client

            # Verify transaction was confirmed by the network
            wait_for_confirmation(
                algorand.client.algod, deploy_result.create_result.tx_id, 3
            )
            assert (
                deploy_result.create_result.confirmation
            ), "deploy_result.create_result.confirmation transaction failed confirmation."

        except Exception as e:
            logger.info(f"Failed to deploy {name}: {e}")

    for name, factory in app_factories.lwc_factories.items():
        try:
            deploy_result = factory.deploy(
                on_update=OnUpdate.UpdateApp,
                on_schema_break=OnSchemaBreak.ReplaceApp,
                create_params=LagrangeWitnessCalculatorMethodCallCreateParams(
                    on_complete=5,  # 5=DeleteApplication
                    method="calculateLagrangeWitness",
                    args=CalculateLagrangeWitnessArgs(
                        signals=get_zk_public_signals(), proof=get_zk_proof()
                    ),
                    max_fee=micro_algo(500_000),
                ),
                send_params=SendParams(cover_app_call_inner_transaction_fees=True),
            )[1]

            # Verify transaction was confirmed by the network
            wait_for_confirmation(
                algorand.client.algod, deploy_result.create_result.tx_id, 3
            )
            assert (
                deploy_result.create_result.confirmation
            ), "deploy_result.create_result.confirmation transaction failed confirmation."

            # Retrieve the ABI return value from the LWC deployment result create method call
            lwc_abi_return = deploy_result.create_result.abi_return

            # Map the LWC ABI return value to separate keys in a flat object
            lw_data = {
                "l": lwc_abi_return[0],
                "xin": lwc_abi_return[1],
                "zh": lwc_abi_return[2],
            }

            # Write LW into a JSON file
            with open("./circuits/main/artifacts/lagrange_witness.json", "w") as f:
                json.dump(lw_data, f, indent=4)

        except Exception as e:
            logger.info(f"Failed to deploy {name}: {e}")

    pvl_clients = {}
    for name, factory in app_factories.pvl_factories.items():
        try:
            sc_client, deploy_result = factory.deploy(
                on_update=OnUpdate.UpdateApp,
                on_schema_break=OnSchemaBreak.ReplaceApp,
                create_params=PlonkVerifierWithLogsBareCallCreateParams(
                    on_complete=0,  # 0=NoOp
                ),
                # params=CommonAppCallCreateParams(on_complete=CreateOnComplete(0))
            )
            # sc_client, deploy_result = factory.deploy(
            #     on_update=OnUpdate.ReplaceApp,
            #     on_schema_break=OnSchemaBreak.ReplaceApp,
            #     create_params=SalvoMethodCallCreateParams(
            #         method="generate",
            #         note=b'salvo:j{"concern":"txn.app_call;generate"}',
            #     ),
            # "delete_params": SalvoMethodCallDeleteParams(
            #     method="terminate",
            #     max_fee=micro_algo(5_000),
            #     note=b'salvo:j{"concern":"txn.app_call;terminate"}',
            # ),
            # )
            client_name = name.replace("_factory", "_client")
            pvl_clients[client_name] = sc_client

            # logger.info(deploy_result.abi_return)

            # Verify transaction was confirmed by the network
            wait_for_confirmation(
                algorand.client.algod, deploy_result.create_result.tx_id, 3
            )
            assert (
                deploy_result.create_result.confirmation
            ), "deploy_result.create_result.confirmation transaction failed confirmation."

        except Exception as e:
            logger.info(f"Failed to deploy {name}: {e}")

    pv_clients = {}
    for name, factory in app_factories.pv_factories.items():
        try:
            sc_client, deploy_result = factory.deploy(
                on_update=OnUpdate.UpdateApp,
                on_schema_break=OnSchemaBreak.ReplaceApp,
                create_params=PlonkVerifierBareCallCreateParams(
                    on_complete=0,  # 0=NoOp
                ),
                # params=CommonAppCallCreateParams(on_complete=CreateOnComplete(0))
            )
            # sc_client, deploy_result = factory.deploy(
            #     on_update=OnUpdate.ReplaceApp,
            #     on_schema_break=OnSchemaBreak.ReplaceApp,
            #     create_params=SalvoMethodCallCreateParams(
            #         method="generate",
            #         note=b'salvo:j{"concern":"txn.app_call;generate"}',
            #     ),
            # "delete_params": SalvoMethodCallDeleteParams(
            #     method="terminate",
            #     max_fee=micro_algo(5_000),
            #     note=b'salvo:j{"concern":"txn.app_call;terminate"}',
            # ),
            # )
            client_name = name.replace("_factory", "_client")
            pv_clients[client_name] = sc_client

            # logger.info(deploy_result.abi_return)

            # Verify transaction was confirmed by the network
            wait_for_confirmation(
                algorand.client.algod, deploy_result.create_result.tx_id, 3
            )
            assert (
                deploy_result.create_result.confirmation
            ), "deploy_result.create_result.confirmation transaction failed confirmation."

        except Exception as e:
            logger.info(f"Failed to deploy {name}: {e}")

    return AppClients(
        salvo_clients=salvo_clients,
        pvl_clients=pvl_clients,
        pv_clients=pv_clients,
    )


# # Create a dict called apps that stores as many smart contract clients as needed
# @pytest.fixture(scope="session")
# def apps(
#     app_clients: AppClients,
# ) -> dict:
#     # Initialize dict to store app clients
#     apps = {}

#     # Extract Salvo clients
#     for name, client in app_clients.salvo_clients.items():
#         apps[name] = client
#         logger.info(f"APP CLIENT: {name}, APP ID: {client.app_id}")

#     # Extract LWC clients
#     for name, client in app_clients.lwc_clients.items():
#         apps[name] = client
#         logger.info(f"APP CLIENT: {name}, APP ID: {client.app_id}")

#     app_clients.salvo_clients["salvo_client_1"].app_client.
#     logger.info(apps)
#     return apps


# Fund smart contract app account (app creator is account doing the funding, implied by use of their client instance)
def test_fund_app_mbr(app_clients: AppClients) -> None:
    # Get smart contract application client from from app clients dict
    salvo = app_clients.salvo_clients["salvo_client_1"]
    pvl = app_clients.pvl_clients["pvl_client_1"]
    pv = app_clients.pv_clients["pv_client_1"]

    fund_salvo_txn = salvo.app_client.fund_app_account(
        FundAppAccountParams(
            note=b'salvo:j{"method":"fund_app_account","concern":"txn.pay;fund_base_mbr"}',
            amount=micro_algo(100_000),
        )
    )
    fund_pvl_txn = pvl.app_client.fund_app_account(
        FundAppAccountParams(
            note=b'pvl:j{"method":"fund_app_account","concern":"txn.pay;fund_base_mbr"}',
            amount=micro_algo(150_000),
        )
    )

    fund_pv_txn = pv.app_client.fund_app_account(
        FundAppAccountParams(
            note=b'pv:j{"method":"fund_app_account","concern":"txn.pay;fund_base_mbr"}',
            amount=micro_algo(150_000),
        )
    )

    # Verify transaction was confirmed by the network
    wait_for_confirmation(salvo.algorand.client.algod, fund_salvo_txn.tx_id, 3)
    assert (
        fund_salvo_txn.confirmation
    ), "fund_salvo_txn.confirmation transaction failed confirmation."

    wait_for_confirmation(salvo.algorand.client.algod, fund_pvl_txn.tx_id, 3)
    assert (
        fund_pvl_txn.confirmation
    ), "fund_pvl_txn.confirmation transaction failed confirmation."

    wait_for_confirmation(salvo.algorand.client.algod, fund_pv_txn.tx_id, 3)
    assert (
        fund_pv_txn.confirmation
    ), "fund_pv_txn.confirmation transaction failed confirmation."


def test_plonk_verify(creator: SigningAccount, app_clients: AppClients) -> None:
    # Get smart contract application client from from app clients dict
    pvl = app_clients.pvl_clients["pvl_client_1"]
    pv = app_clients.pv_clients["pv_client_1"]

    # Define nested function that attemps to call the `plonk_verify` method
    def try_plonk_verify_txn(
        sender: SigningAccount,
        note: bytes | str | None = None,
    ) -> None:
        # Send app call transaction to execute smart contract method `plonk_verify`
        send_app_call_txn(
            logger=logger,
            app=pvl,
            sender=sender,
            method=pvl.send.verify,
            args=(get_zk_public_signals(), get_zk_proof(), get_zk_lagrange_witness()),
            max_fee=500_000,
            note=note,
            description="App Call Method Call Transaction: verify()",
        )

    # Call `try_plonk_verify_txn`
    try_plonk_verify_txn(
        sender=creator,
        note=b'pv:j{"method":"verify","concern":"txn.app_call;verify_plonk_bls12-381_artifacts"}',
    )

    # composer = pv.new_group()

    # logger.info(get_zk_public_signals())
    # logger.info(get_zk_proof())
    # logger.info(get_zk_lagrange_witness())
    # logger.info(get_zk_vkey(logger))

    # composer.verify(
    #     args=(get_zk_public_signals(), get_zk_proof(), get_zk_lagrange_witness()),
    #     params=CommonAppCallParams(
    #         sender=creator.address,
    #         signer=creator.signer,
    #         max_fee=micro_algo(200_000),
    #     ),
    # )

    # result = composer.simulate(
    #     # allow_more_logs=True,
    #     extra_opcode_budget=102_900,
    # )

    # logger.info(result)


# # Test case for sending an app call transaction to the `get_box_user_registry` method of the smart contract
# def test_get_box_user_registry(
#     creator: SigningAccount,
#     apps: dict[str, SalvoClient],
# ) -> None:
#     # Get smart contract application from from apps dict
#     app = apps["salvo_client_1"]

#     # Define nested function that attemps to call the `get_box_user_registry` method
#     def try_get_box_user_registry_txn(
#         sender: SigningAccount,
#         note: bytes | str | None = None,
#     ) -> None:
#         # Create the required payment transactions
#         box_r_pay = create_payment_txn(
#             app=app,
#             sender=sender,
#             amount=cst.BOX_R_COST,
#             note=b'salvo:j{"concern":"txn.pay;box_r_mbr_pay"}',
#         )  # Box user registry MBR cost payment

#         # Send app call transaction to execute smart contract method `new_game`
#         send_app_call_txn(
#             logger=logger,
#             app=app,
#             sender=sender,
#             method=app.send.get_box_user_registry,
#             args=(box_r_pay,),
#             note=note,
#             description="App Call Method Call Transaction: get_box_user_registry()",
#         )

#     # Call `try_get_box_user_registry_txn`
#     try_get_box_user_registry_txn(
#         sender=creator,
#         note=b'salvo:j{"method":"new_game","concern":"txn.app_call;user_registered_their_acc"}',
#     )

#     box_r_value = app.state.box.box_user_registry.get_value(
#         decode_address(creator.address)
#     )

#     # Log
#     logger.info(box_r_value)


# # Test case for sending an app call transaction to the `new_game` method of the smart contract
# def test_new_game(
#     creator: SigningAccount,
#     apps: dict[str, SalvoClient],
# ) -> None:
#     # Get smart contract application from from apps dict
#     app = apps["salvo_client_1"]

#     # Define nested function that attemps to call the `new_game` method
#     def try_new_game_txn(
#         sender: SigningAccount,
#         stake_amount: int,
#         lobby_size: int,
#         note: bytes | str | None = None,
#     ) -> None:
#         # Define payment amounts
#         box_l_cost = app.send.calc_single_box_cost(
#             (10, lobby_size * cst.ADDRESS_SIZE)
#         ).abi_return

#         # Create the required payment transactions
#         stake_pay = create_payment_txn(
#             app=app,
#             sender=sender,
#             amount=stake_amount,
#             note=b'salvo:j{"concern":"txn.pay;stake_pay"}',
#         )  # Stake payment
#         box_g_pay = create_payment_txn(
#             app=app,
#             sender=sender,
#             amount=cst.BOX_G_COST,
#             note=b'salvo:j{"concern":"txn.pay;box_g_mbr_pay"}',
#         )  # Box game grid MBR cost payment
#         box_s_pay = create_payment_txn(
#             app=app,
#             sender=sender,
#             amount=cst.BOX_S_COST,
#             note=b'salvo:j{"concern":"txn.pay;box_s_mbr_pay"}',
#         )  # Box game state MBR cost payment
#         box_c_pay = create_payment_txn(
#             app=app,
#             sender=sender,
#             amount=cst.BOX_C_COST,
#             note=b'salvo:j{"concern":"txn.pay;box_c_mbr_pay"}',
#         )  # Box game character MBR cost payment
#         box_l_pay = create_payment_txn(
#             app=app,
#             sender=sender,
#             amount=box_l_cost,  # current cost: 32_100 mAlgo
#             note=b'salvo:j{"concern":"txn.pay;box_l_mbr_pay"}',
#         )  # Box game lobby MBR cost payment

#         # Send app call transaction to execute smart contract method `new_game`
#         send_app_call_txn(
#             logger=logger,
#             app=app,
#             sender=sender,
#             method=app.send.new_game,
#             args=(
#                 box_g_pay,
#                 box_s_pay,
#                 box_c_pay,
#                 box_l_pay,
#                 stake_pay,
#                 lobby_size,
#             ),
#             note=note,
#             description="App Call Method Call Transaction: new_game()",
#         )

#     # Call `try_new_game_txn`
#     try_new_game_txn(
#         sender=creator,
#         stake_amount=0,
#         # stake_amount=2_000_000,
#         lobby_size=2,
#         note=b'salvo:j{"method":"new_game","concern":"txn.app_call;create_new_game"}',
#     )

#     game_id_1_bytes = (1).to_bytes(8, "big")
#     box_g_value = app.state.box.box_game_grid.get_value(game_id_1_bytes)
#     box_s_value = app.state.box.box_game_state.get_value(game_id_1_bytes)
#     box_p_value = app.state.box.box_game_character.get_value(
#         decode_address(creator.address)
#     )

#     read_game_1_lobby_txn = app.send.read_box_game_lobby(
#         args=(1,),
#         params=CommonAppCallParams(sender=creator.address, signer=creator.address),
#     )

#     # Log
#     logger.info(box_g_value)
#     logger.info(box_s_value)
#     logger.info(box_p_value)

#     logger.info(f"Creator address: {creator.address}")
#     logger.info(f"Game lobby: {read_game_1_lobby_txn.abi_return}")


# # Test case for sending an app call transaction to the `commit_turn` method of the smart contract
# def test_commit_turn(
#     creator: SigningAccount,
#     apps: dict[str, SalvoClient],
# ) -> None:
#     # Get smart contract application from from apps dict
#     app = apps["salvo_client_1"]

#     # Define nested function that attemps to call the `commit_turn` method
#     def try_commit_turn_txn(
#         sender: SigningAccount,
#         game_id: int,
#         turn_hash: int,
#         note: bytes | str | None = None,
#     ) -> None:

#         # Send app call transaction to execute smart contract method `commit_turn`
#         send_app_call_txn(
#             logger=logger,
#             app=app,
#             sender=sender,
#             method=app.send.commit_turn,
#             args=(game_id, turn_hash),
#             note=note,
#             description="App Call Method Call Transaction: commit_turn()",
#         )

#     # Call `try_commit_turn_txn`
#     try_commit_turn_txn(
#         sender=creator,
#         game_id=1,
#         turn_hash=3367837694425617368410147401029684414564229674589041874024747373990573450785,
#         note=b'salvo:j{"method":"commit_turn","concern":"txn.app_call;user_turn_commitment"}',
#     )

#     box_c_value = app.state.box.box_game_character.get_value(
#         decode_address(creator.address)
#     )

#     # Log
#     logger.info(box_c_value)


# Test case for sending an app call transaction to the `get_box_user_registry` method of the smart contract
def test_mimc_tester(
    creator: SigningAccount,
    app_clients: AppClients,
) -> None:
    # Get smart contract application from from apps dict
    salvo = app_clients.salvo_clients["salvo_client_1"]

    # Define nested function that attemps to call the `mimc_tester` method
    def try_mimc_tester_txn(
        sender: SigningAccount,
        # position: tuple[int, int],
        # movement: list[tuple[int, int]],
        # action: int,
        # direction: int,
        # salt: int,
        note: bytes | str | None = None,
    ) -> None:
        # Send app call transaction to execute smart contract method `mimc_tester`
        send_app_call_txn(
            logger=logger,
            app=salvo,
            sender=sender,
            method=salvo.send.mimc_tester,
            # args=(position, movement, action, direction, salt),
            max_fee=105_000,
            note=note,
            description="App Call Method Call Transaction: mimc_tester()",
        )

    # Call `try_mimc_tester_txn`
    try_mimc_tester_txn(
        sender=creator,
        # position=(0, 6),
        # movement=[(0, 7), (0, 8), (0, 9), (1, 9), (1, 10)],
        # action=0,
        # direction=2,
        # salt=1234567888999,
        note=b'salvo:j{"method":"mimc_tester","concern":"txn.app_call;test_mimc_hashing"}',
    )

    # composer = salvo.new_group()

    # composer.mimc_tester(
    #     # args=((0, 6), [(0, 7), (0, 8), (0, 9), (1, 9), (1, 10)], 0, 2, 1234567888999),
    #     params=CommonAppCallParams(
    #         sender=creator.address,
    #         signer=creator.signer,
    #         max_fee=micro_algo(200_000),
    #     ),
    # )

    # result = composer.simulate(
    #     # allow_more_logs=True,
    #     extra_opcode_budget=100_000,
    # )

    # logger.info(result)
