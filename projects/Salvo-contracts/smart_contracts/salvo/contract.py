# smart_contracts/salvo/contract.py
# NOTE: Consider pinching a percentage of the prize pot
from algopy import (
    Account,
    ARC4Contract,
    BoxMap,
    BoxRef,
    Bytes,
    Global,
    TemplateVar,
    Txn,
    UInt64,
    arc4,
    gtxn,
    op,
    urange,
)

from . import constants as cst
from . import errors as err
from . import structs as stc
from . import subroutines as srt
from . import type_aliases as ta


# Smart contract class
class Salvo(ARC4Contract):
    game_id: UInt64

    # Application init method
    def __init__(self) -> None:
        # Box Storage type declarations
        self.box_game_grid = BoxMap(UInt64, ta.GameGrid, key_prefix="g_")
        self.box_game_state = BoxMap(UInt64, stc.GameState, key_prefix="s_")
        self.box_game_lobby = BoxMap(UInt64, Bytes, key_prefix="l_")
        self.box_game_player = BoxMap(Account, stc.GamePlayer, key_prefix="p_")

        self.box_user_profile = BoxMap(Account, stc.UserProfile, key_prefix="u_")

    # READ-ONLY: Calculate the minimum balance requirement (MBR) cost for storing a single box unit
    @arc4.abimethod(readonly=True)
    def calc_single_box_cost(
        self, key_size: arc4.UInt8, value_size: arc4.UInt16
    ) -> UInt64:
        # Formula for calculating single box total cost
        base_cost = arc4.UInt16(2_500)  # Base fee (2_500)
        size_cost = arc4.UInt16(400).native * (
            key_size.native + value_size.native
        )  # Size fee (400 per byte * (len(key)+len(value)))

        # Return single box total cost amount
        return base_cost.native + size_cost

    # READ-ONLY: Return the app genesis timestamp in Unix format
    @arc4.abimethod(readonly=True)
    def read_gen_unix(self) -> UInt64:
        return TemplateVar[UInt64]("GEN_UNIX")

    # READ-ONLY: Read game grid cell value at array index under the given game id key
    @arc4.abimethod(readonly=True)
    def read_grid_cell_value_by_index(
        self, game_id: UInt64, i: arc4.UInt8
    ) -> arc4.UInt8:
        # Return byte value at grid cell index
        return srt.get_grid_cell_value(game_id, self.box_game_grid, i)

    # READ-ONLY: Read game grid cell value at x and y coordinates under the given game id key
    @arc4.abimethod(readonly=True)
    def read_grid_cell_value_at_coords(
        self, game_id: UInt64, x: arc4.UInt8, y: arc4.UInt8
    ) -> arc4.UInt8:
        # Convert x & y coords to grid cell index, then return byte value at that index
        return srt.get_grid_cell_value(
            game_id, self.box_game_grid, srt.convert_grid_coords_to_index(x, y)
        )

    # READ-ONLY: Return True if game grid box value exists, else False
    @arc4.abimethod(readonly=True)
    def does_box_game_grid_exist(self, game_id: UInt64) -> bool:
        return self.box_game_grid.maybe(game_id)[1]

    # READ-ONLY: Return an array of all active users in the game lobby at time of call
    @arc4.abimethod(readonly=True)
    def read_box_game_lobby(self, game_id: UInt64) -> ta.GameLobby:
        # Fail transaction unless the assertion below evaluates True
        assert game_id in self.box_game_lobby, err.GAME_ID_NOT_FOUND

        # Retrieve byte array of current user addresses from the box using the game id parameter
        game_lobby_b_arr = self.box_game_lobby[game_id]

        # Define a dynamic array to append all remaining active users
        users_in_lobby = ta.GameLobby()

        # Iterate through the users byte array
        for i in urange(0, game_lobby_b_arr.length, cst.ADDRESS_SIZE):
            # Extract the bytes representing the user address
            user_addr_bytes = op.extract(game_lobby_b_arr, i, cst.ADDRESS_SIZE)
            # Only append address if its bytes do NOT equal to a zeroed byte array of size 32
            if user_addr_bytes != Bytes(cst.ZEROED_ADDR_BYTES):
                user_account = Account.from_bytes(user_addr_bytes)
                users_in_lobby.append(arc4.Address(user_account))

        # Return the array containing the remaining active users in the game lobby
        return users_in_lobby

    # Generate the smart contract application client
    @arc4.abimethod(create="require")
    def generate(
        self,
    ) -> None:
        # Fail transaction unless the assertion below evaluates True
        # assert Txn.sender == Global.creator_address, err.UNAUTH_CREATOR
        # assert Txn.sender == Account(CREATOR_ADDRESS), "temp error in generate method"

        # Set Global State variables to their default starting values
        self.game_id = UInt64(1)

    @arc4.abimethod
    def new_game(
        self,
        box_g_pay: gtxn.PaymentTransaction,
        box_s_pay: gtxn.PaymentTransaction,
        box_p_pay: gtxn.PaymentTransaction,
        box_l_pay: gtxn.PaymentTransaction,
        stake_pay: gtxn.PaymentTransaction,
        lobby_size: arc4.UInt8,
    ) -> None:
        # Fail transaction unless the assertion below evaluates True
        assert Global.group_size == 6, err.INVALID_GROUP_SIZE

        assert box_g_pay.amount >= cst.BOX_G_COST, err.INSUFFICIENT_PAY_AMOUNT
        assert box_s_pay.amount >= cst.BOX_S_COST, err.INSUFFICIENT_PAY_AMOUNT
        assert box_p_pay.amount >= cst.BOX_P_COST, err.INSUFFICIENT_PAY_AMOUNT
        assert box_l_pay.amount >= self.calc_single_box_cost(
            key_size=arc4.UInt8(10),
            value_size=arc4.UInt16(cst.ADDRESS_SIZE * lobby_size.native),
        ), err.INSUFFICIENT_PAY_AMOUNT
        assert (
            stake_pay.amount >= cst.MIN_STAKE_AMOUNT
            and stake_pay.amount <= cst.MAX_STAKE_AMOUNT
            and stake_pay.amount % cst.MIN_STAKE_AMOUNT == 0
        ), err.INVALID_STAKE_AMOUNT

        assert box_g_pay.sender == Txn.sender, err.INVALID_BOX_PAY_SENDER
        assert box_s_pay.sender == Txn.sender, err.INVALID_BOX_PAY_SENDER
        assert box_p_pay.sender == Txn.sender, err.INVALID_BOX_PAY_SENDER
        assert box_l_pay.sender == Txn.sender, err.INVALID_BOX_PAY_SENDER
        assert stake_pay.sender == Txn.sender, err.INVALID_STAKE_PAY_SENDER

        assert (
            box_g_pay.receiver == Global.current_application_address
        ), err.INVALID_BOX_PAY_RECEIVER
        assert (
            box_s_pay.receiver == Global.current_application_address
        ), err.INVALID_BOX_PAY_RECEIVER
        assert (
            box_p_pay.receiver == Global.current_application_address
        ), err.INVALID_BOX_PAY_RECEIVER
        assert (
            box_l_pay.receiver == Global.current_application_address
        ), err.INVALID_BOX_PAY_RECEIVER
        assert (
            stake_pay.receiver == Global.current_application_address
        ), err.INVALID_BOX_PAY_RECEIVER

        assert (
            lobby_size >= cst.MIN_LOBBY_SIZE
            and lobby_size <= cst.MAX_LOBBY_SIZE
            and lobby_size.native % 2 == 0
        ), err.INVALID_LOBBY_SIZE

        # Create a game grid box with unique game ID as key
        self.box_game_grid[self.game_id] = ta.GameGrid.from_bytes(cst.ZEROED_GRID_BYTES)

        # Create a game state box with unique game ID as key
        self.box_game_state[self.game_id] = stc.GameState(
            staking_closed=arc4.Bool(False),  # noqa: FBT003
            # quick_play_enabled=arc4.Bool(False),  # quick_play_enabled),
            lobby_size=lobby_size,
            active_players=arc4.UInt8(1),
            box_l_start_pos=arc4.UInt16(cst.ADDRESS_SIZE),
            expiry_ts=arc4.UInt64(Global.latest_timestamp + cst.PHASE_EXPIRY_INTERVAL),
            prize_pot=arc4.UInt64(stake_pay.amount),
            admin_address=arc4.Address(Txn.sender),
        )

        # Create a game lobby box with unique game ID as key
        # Assign zeroed bytes to store all player addresses in lobby (32 bytes per player)
        self.box_game_lobby[self.game_id] = op.bzero(
            cst.ADDRESS_SIZE * lobby_size.native
        )

        self.box_game_player[Txn.sender] = stc.GamePlayer(
            arc4.UInt8(1),
            arc4.UInt8(6),
            arc4.UInt8(22),
            arc4.UInt8(10),
            arc4.UInt8(0),
        )

        # For game lobby box, replace the bytes starting at index 0 w/ the sender address bytes
        game_lobby_bref = BoxRef(
            key=self.box_game_lobby.key_prefix + op.itob(self.game_id)
        )
        game_lobby_bref.replace(0, Txn.sender.bytes)

        # Increment game id by 1 for next new game instance
        self.game_id += 1

        # Set player 1 and player 2 position on the grid
        # srt.set_grid_cell_value_at_index(
        #     game_id, self.box_game_grid, arc4.UInt8(6), arc4.UInt8(1)
        # )
        # srt.set_grid_cell_value_at_index(
        #     game_id, self.box_game_grid, arc4.UInt8(116), arc4.UInt8(2)
        # )

    @arc4.abimethod(allow_actions=["UpdateApplication"])
    def update(self) -> None:
        assert TemplateVar[bool]("UPDATABLE"), err.UPDATABLE_NOT_TRUE
        assert Txn.sender == Global.creator_address, err.UNAUTH_CREATOR

        # return self._convert_grid_index_to_coords(i=arc4.UInt8(6))

    # Allow application creator to delete the smart contract application
    # @arc4.abimethod(allow_actions=["DeleteApplication"])
    # def terminate(self) -> None:
    #     # Fail transaction unless the assertions below evaluate True
    #     assert TemplateVar[bool]("DELETABLE"), err.DELETEABLE_NOT_TRUE
    #     assert Txn.sender == Global.creator_address, err.INVALID_CREATOR

    #     # Check if game trophy box exists
    #     if self.box_game_trophy:
    #         # Use game trophy box data asset id property to check app account asset balance for trophy
    #         asset_balance, asset_exists = op.AssetHoldingGet.asset_balance(
    #             Global.current_application_address,
    #             self.box_game_trophy.value.asset_id.native,
    #         )
    #         # If asset exists and its balance is 1, perform burn via asset config inner transaction
    #         if asset_exists and asset_balance == 1:
    #             srt.burn_itxn(
    #                 asset_id=self.box_game_trophy.value.asset_id.native,
    #                 note=String(
    #                     'pieout:j{"method":"terminate","concern":"itxn.asset_config;burn_trophy_asset"}'
    #                 ),
    #             )
    #         # Delete box game trophy from contract storage if it exsists
    #         del self.box_game_trophy.value

    #     # Issue payment inner transaction closing all remaining funds in application account balance
    #     itxn.Payment(
    #         receiver=Txn.sender,
    #         amount=0,
    #         close_remainder_to=Txn.sender,
    #         note=b'pieout:j{"method":"terminate","concern":"itxn.pay;close_remainder_to"}',
    #     ).submit()
