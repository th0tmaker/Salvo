# smart_contracts/salvo/contract.py
# NOTE: Consider pinching a percentage of the prize pot

from algopy import (
    Account,
    ARC4Contract,
    BoxMap,
    BoxRef,
    Bytes,
    Global,
    OpUpFeeSource,
    TemplateVar,
    Txn,
    UInt64,
    arc4,
    ensure_budget,
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
class Salvo(ARC4Contract, avm_version=11):
    game_id: UInt64

    # Application init method
    def __init__(self) -> None:
        # Box Storage type declarations
        self.box_user_registry = BoxMap(Account, stc.UserRegistry, key_prefix="r_")

        self.box_game_grid = BoxMap(UInt64, ta.GameGrid, key_prefix="g_")
        self.box_game_state = BoxMap(UInt64, stc.GameState, key_prefix="s_")
        self.box_game_lobby = BoxMap(UInt64, Bytes, key_prefix="l_")
        self.box_game_character = BoxMap(Account, stc.GameCharacter, key_prefix="c_")

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

    # READ-ONLY: Return True if user registry box value exists, else False
    @arc4.abimethod(readonly=True)
    def does_box_user_registry_exist(self, account: Account) -> bool:
        return self.box_user_registry.maybe(account)[1]

    # READ-ONLY: Return True if game grid box value exists, else False
    @arc4.abimethod(readonly=True)
    def does_box_game_grid_exist(self, game_id: UInt64) -> bool:
        return self.box_game_grid.maybe(game_id)[1]

    # READ-ONLY: Return True if game state box value exists, else False
    @arc4.abimethod(readonly=True)
    def does_box_game_state_exist(self, game_id: UInt64) -> bool:
        return self.box_game_state.maybe(game_id)[1]

    # READ-ONLY: Return True if game character box value exists, else False
    @arc4.abimethod(readonly=True)
    def does_box_game_character_exist(self, account: Account) -> bool:
        return self.box_game_character.maybe(account)[1]

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
    def get_box_user_registry(
        self,
        box_r_pay: gtxn.PaymentTransaction,
    ) -> None:
        # Fail transaction unless the assertion below evaluates True
        assert Global.group_size == 2, err.INVALID_GROUP_SIZE
        assert Txn.sender not in self.box_user_registry, err.BOX_FOUND
        # assert self.box_game_trophy, err.BOX_NOT_FOUND

        # assert box_r_pay.amount == cst.BOX_R_COST, err.INSUFFICIENT_PAY_AMOUNT
        assert box_r_pay.sender == Txn.sender, err.INVALID_BOX_PAY_SENDER
        assert (
            box_r_pay.receiver == Global.current_application_address
        ), err.INVALID_BOX_PAY_RECEIVER

        # Create a new box storage unit for the user registry w/ the sender address value as key
        self.box_user_registry[Txn.sender] = stc.UserRegistry(
            hosting_game=arc4.Bool(False),  # noqa: FBT003
            game_id=arc4.UInt64(0),
            commit_rand_round=arc4.UInt64(0),
            expiry_round=arc4.UInt64(Global.round + cst.BOX_R_EXP_ROUND_DELTA),
        )

    @arc4.abimethod
    def new_game(
        self,
        box_g_pay: gtxn.PaymentTransaction,
        box_s_pay: gtxn.PaymentTransaction,
        box_c_pay: gtxn.PaymentTransaction,
        box_l_pay: gtxn.PaymentTransaction,
        stake_pay: gtxn.PaymentTransaction,
        lobby_size: arc4.UInt8,
    ) -> None:
        # Fail transaction unless the assertion below evaluates True
        assert Global.group_size == 6, err.INVALID_GROUP_SIZE

        assert box_g_pay.amount >= cst.BOX_G_COST, err.INSUFFICIENT_PAY_AMOUNT
        assert box_s_pay.amount >= cst.BOX_S_COST, err.INSUFFICIENT_PAY_AMOUNT
        assert box_c_pay.amount >= cst.BOX_C_COST, err.INSUFFICIENT_PAY_AMOUNT
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
        assert box_c_pay.sender == Txn.sender, err.INVALID_BOX_PAY_SENDER
        assert box_l_pay.sender == Txn.sender, err.INVALID_BOX_PAY_SENDER
        assert stake_pay.sender == Txn.sender, err.INVALID_STAKE_PAY_SENDER

        assert (
            box_g_pay.receiver == Global.current_application_address
        ), err.INVALID_BOX_PAY_RECEIVER
        assert (
            box_s_pay.receiver == Global.current_application_address
        ), err.INVALID_BOX_PAY_RECEIVER
        assert (
            box_c_pay.receiver == Global.current_application_address
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

        # Create a new box storage unit for the game grid w/ the current global game_id value as key
        self.box_game_grid[self.game_id] = ta.GameGrid.from_bytes(cst.ZEROED_GRID_BYTES)

        # Create a new box storage unit for the game state w/ the current global game_id value as key
        self.box_game_state[self.game_id] = stc.GameState(
            staking_closed=arc4.Bool(False),  # noqa: FBT003
            # quick_play_enabled=arc4.Bool(False),  # quick_play_enabled,
            lobby_size=lobby_size,
            active_players=arc4.UInt8(1),
            box_l_start_pos=arc4.UInt16(cst.ADDRESS_SIZE),
            expiry_ts=arc4.UInt64(Global.latest_timestamp + cst.PHASE_EXPIRY_INTERVAL),
            prize_pot=arc4.UInt64(stake_pay.amount),
            admin_address=arc4.Address(Txn.sender),
        )

        # NOTE: STAKE_PAY.AMOUNT in new game needs to be put in game state so others can match

        # Create a new box storage unit for the game lobby w/ the current global game_id value as key
        self.box_game_lobby[self.game_id] = op.bzero(
            cst.ADDRESS_SIZE * lobby_size.native
        )  # Assign zeroed bytes to store all player addresses in lobby (32 bytes per player)

        # Create a new box storage unit for the game character w/ the sender address value as key
        self.box_game_character[Txn.sender] = stc.GameCharacter(
            arc4.UInt8(1),
            arc4.UInt8(6),
            arc4.UInt8(5),
            arc4.UInt8(0),
            arc4.UInt8(1),
        )

        # For game lobby box, replace the bytes starting at index 0 w/ the sender address bytes
        game_lobby_bref = BoxRef(
            key=self.box_game_lobby.key_prefix + op.itob(self.game_id)
        )
        game_lobby_bref.replace(0, Txn.sender.bytes)

        # Increment game id by 1 for next new game instance
        self.game_id += 1

    @arc4.abimethod
    def mimc_tester(
        self,
        # game_id: arc4.UInt64, <- Consider as mimc input
        position: ta.CoordsPair,
        movement: ta.CoordsArray,
        action: arc4.UInt8,
        direction: arc4.UInt8,
        salt: arc4.UInt64,
    ) -> Bytes:
        # Ensure transaction has sufficient opcode budget
        ensure_budget(required_budget=10500, fee_source=OpUpFeeSource.GroupCredit)

        # Extract row and column values from the given position argument
        row, col = position.native

        # NOTE: Consider as mimc input
        # assert game_id.native in self.box_game_grid, err.BOX_NOT_FOUND

        # Fail transaction unless the assertion below evaluates True
        srt.assert_coords_in_range(row, col)
        assert (
            srt.convert_grid_coords_to_index(row, col)
            == self.box_game_character[Txn.sender].position
        ), err.POSITION_MISMATCH

        assert (
            movement.length <= self.box_game_character[Txn.sender].move_points
        ), err.MOVEMENT_OVERFLOW

        assert action <= 1, err.ACTION_OVERFLOW
        assert direction <= 3, err.DIRECTION_OVERFLOW

        assert srt.is_move_sequence_valid(
            UInt64(1), self.box_game_grid, position, movement.copy()
        ), err.INVALID_MOVE_SEQUENCE

        # Initialize a preimage byte array that will store scalar input ints for MiMC hashing
        preimage = Bytes()
        preimage += srt.u64_to_fr32(arc4.UInt64(cst.DOMAIN_PREFIX))
        # preimage += srt.u64_to_fr32(game_id) <- Consider as mimc input

        # Iterate through all the entries in the movement coords array
        for new_coords in movement:
            # Extract new row and new column values from the given movement argument
            new_row, new_col = new_coords.native
            # Append the validated move to preimage
            preimage += srt.u8_to_fr32(new_row)
            preimage += srt.u8_to_fr32(new_col)

        # Add rest of the scalar inputs
        preimage += srt.u8_to_fr32(action)
        preimage += srt.u8_to_fr32(direction)
        preimage += srt.u64_to_fr32(salt)

        # # After processing the full sequence, find valid path cells of the last updated position
        # neighbors_with_count = srt.get_neighbors_with_count(
        #     UInt64(1),
        #     self.box_game_grid,
        #     position,
        # )

        # valid_path_cells = srt.get_valid_path_cells(neighbors_with_count)

        output = op.mimc(op.MiMCConfigurations.BLS12_381Mp111, preimage)

        # # return srt.check_valid_move(
        # #     UInt64(1), self.box_game_grid[self.game_id], current_pos
        # # )

        return output

    @arc4.abimethod(allow_actions=["UpdateApplication"])
    def update(self) -> None:
        assert TemplateVar[bool]("UPDATABLE"), err.UPDATABLE_NOT_TRUE
        assert Txn.sender == Global.creator_address, err.SENDER_NOT_CREATOR

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
