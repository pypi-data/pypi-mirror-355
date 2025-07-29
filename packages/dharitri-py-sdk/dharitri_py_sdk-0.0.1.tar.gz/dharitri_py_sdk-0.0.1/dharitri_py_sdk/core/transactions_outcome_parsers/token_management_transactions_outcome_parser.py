from typing import List

from dharitri_py_sdk.core.address import Address
from dharitri_py_sdk.core.codec import decode_unsigned_number
from dharitri_py_sdk.core.constants import DEFAULT_HRP
from dharitri_py_sdk.core.errors import ParseTransactionOutcomeError
from dharitri_py_sdk.core.transactions_outcome_parsers.resources import (
    TransactionEvent, TransactionOutcome, find_events_by_identifier)
from dharitri_py_sdk.core.transactions_outcome_parsers.token_management_transactions_outcome_parser_types import (
    AddQuantityOutcome, BurnOutcome, BurnQuantityOutcome, FreezeOutcome,
    IssueFungibleOutcome, IssueNonFungibleOutcome, IssueSemiFungibleOutcome,
    MintOutcome, NFTCreateOutcome, PauseOutcome, RegisterAndSetAllRolesOutcome,
    RegisterMetaDcdtOutcome, SetSpecialRoleOutcome, UnFreezeOutcome,
    UnPauseOutcome, UpdateAttributesOutcome, WipeOutcome)


class TokenManagementTransactionsOutcomeParser:
    def __init__(self) -> None:
        pass

    def parse_issue_fungible(self, transaction_outcome: TransactionOutcome) -> List[IssueFungibleOutcome]:
        self._ensure_no_error(transaction_outcome.logs.events)

        events = find_events_by_identifier(transaction_outcome, "issue")
        return [IssueFungibleOutcome(self._extract_token_identifier(event)) for event in events]

    def parse_issue_non_fungible(self, transaction_outcome: TransactionOutcome) -> List[IssueNonFungibleOutcome]:
        self._ensure_no_error(transaction_outcome.logs.events)

        events = find_events_by_identifier(transaction_outcome, "issueNonFungible")
        return [IssueNonFungibleOutcome(self._extract_token_identifier(event)) for event in events]

    def parse_issue_semi_fungible(self, transaction_outcome: TransactionOutcome) -> List[IssueSemiFungibleOutcome]:
        self._ensure_no_error(transaction_outcome.logs.events)

        events = find_events_by_identifier(transaction_outcome, "issueSemiFungible")
        return [IssueSemiFungibleOutcome(self._extract_token_identifier(event)) for event in events]

    def parse_register_meta_dcdt(self, transaction_outcome: TransactionOutcome) -> List[RegisterMetaDcdtOutcome]:
        self._ensure_no_error(transaction_outcome.logs.events)

        events = find_events_by_identifier(transaction_outcome, "registerMetaDCDT")
        return [RegisterMetaDcdtOutcome(self._extract_token_identifier(event)) for event in events]

    def parse_register_and_set_all_roles(self, transaction_outcome: TransactionOutcome) -> List[RegisterAndSetAllRolesOutcome]:
        self._ensure_no_error(transaction_outcome.logs.events)

        register_events = find_events_by_identifier(transaction_outcome, "registerAndSetAllRoles")
        set_role_events = find_events_by_identifier(transaction_outcome, "DCDTSetRole")

        if len(register_events) != len(set_role_events):
            raise ParseTransactionOutcomeError("The number of `registerAndSetAllRoles` events and `DCDTSetRole` events do not match")

        result: List[RegisterAndSetAllRolesOutcome] = []
        for register_event, set_role_event in zip(register_events, set_role_events):
            identifier = self._extract_token_identifier(register_event)
            roles = self._decode_roles(set_role_event)
            result.append(RegisterAndSetAllRolesOutcome(identifier, roles))

        return result

    def parse_set_burn_role_globally(self, transaction_outcome: TransactionOutcome) -> None:
        self._ensure_no_error(transaction_outcome.logs.events)

    def parse_unset_burn_role_globally(self, transaction_outcome: TransactionOutcome) -> None:
        self._ensure_no_error(transaction_outcome.logs.events)

    def parse_set_special_role(self, transaction_outcome: TransactionOutcome) -> List[SetSpecialRoleOutcome]:
        self._ensure_no_error(transaction_outcome.logs.events)

        events = find_events_by_identifier(transaction_outcome, "DCDTSetRole")
        return [
            SetSpecialRoleOutcome(
                user_address=event.address,
                token_identifier=self._extract_token_identifier(event),
                roles=self._decode_roles(event)
            )
            for event in events
        ]

    def parse_nft_create(self, transaction_outcome: TransactionOutcome) -> List[NFTCreateOutcome]:
        self._ensure_no_error(transaction_outcome.logs.events)

        events = find_events_by_identifier(transaction_outcome, "DCDTNFTCreate")

        return [
            NFTCreateOutcome(
                token_identifier=self._extract_token_identifier(event),
                nonce=self._extract_nonce(event),
                initial_quantity=self._extract_amount(event)
            )
            for event in events
        ]

    def parse_local_mint(self, transaction_outcome: TransactionOutcome) -> List[MintOutcome]:
        self._ensure_no_error(transaction_outcome.logs.events)

        events = find_events_by_identifier(transaction_outcome, "DCDTLocalMint")
        return [
            MintOutcome(
                user_address=event.address,
                token_identifier=self._extract_token_identifier(event),
                nonce=self._extract_nonce(event),
                minted_supply=self._extract_amount(event)
            )
            for event in events
        ]

    def parse_local_burn(self, transaction_outcome: TransactionOutcome) -> List[BurnOutcome]:
        self._ensure_no_error(transaction_outcome.logs.events)

        events = find_events_by_identifier(transaction_outcome, "DCDTLocalBurn")
        return [
            BurnOutcome(
                user_address=event.address,
                token_identifier=self._extract_token_identifier(event),
                nonce=self._extract_nonce(event),
                burnt_supply=self._extract_amount(event)
            )
            for event in events
        ]

    def parse_pause(self, transaction_outcome: TransactionOutcome) -> List[PauseOutcome]:
        self._ensure_no_error(transaction_outcome.logs.events)

        events = find_events_by_identifier(transaction_outcome, "DCDTPause")
        return [PauseOutcome(self._extract_token_identifier(event)) for event in events]

    def parse_unpause(self, transaction_outcome: TransactionOutcome) -> List[UnPauseOutcome]:
        self._ensure_no_error(transaction_outcome.logs.events)

        events = find_events_by_identifier(transaction_outcome, "DCDTUnPause")
        return [UnPauseOutcome(self._extract_token_identifier(event)) for event in events]

    def parse_freeze(self, transaction_outcome: TransactionOutcome) -> List[FreezeOutcome]:
        self._ensure_no_error(transaction_outcome.logs.events)

        events = find_events_by_identifier(transaction_outcome, "DCDTFreeze")
        return [
            FreezeOutcome(
                user_address=self._extract_address(event),
                token_identifier=self._extract_token_identifier(event),
                nonce=self._extract_nonce(event),
                balance=self._extract_amount(event)
            )
            for event in events
        ]

    def parse_unfreeze(self, transaction_outcome: TransactionOutcome) -> List[UnFreezeOutcome]:
        self._ensure_no_error(transaction_outcome.logs.events)

        events = find_events_by_identifier(transaction_outcome, "DCDTUnFreeze")
        return [
            UnFreezeOutcome(
                user_address=self._extract_address(event),
                token_identifier=self._extract_token_identifier(event),
                nonce=self._extract_nonce(event),
                balance=self._extract_amount(event)
            )
            for event in events
        ]

    def parse_wipe(self, transaction_outcome: TransactionOutcome) -> List[WipeOutcome]:
        self._ensure_no_error(transaction_outcome.logs.events)

        events = find_events_by_identifier(transaction_outcome, "DCDTWipe")
        return [
            WipeOutcome(
                user_address=self._extract_address(event),
                token_identifier=self._extract_token_identifier(event),
                nonce=self._extract_nonce(event),
                balance=self._extract_amount(event)
            )
            for event in events
        ]

    def parse_update_attributes(self, transaction_outcome: TransactionOutcome) -> List[UpdateAttributesOutcome]:
        self._ensure_no_error(transaction_outcome.logs.events)

        events = find_events_by_identifier(transaction_outcome, "DCDTNFTUpdateAttributes")
        return [
            UpdateAttributesOutcome(
                token_identifier=self._extract_token_identifier(event),
                nonce=self._extract_nonce(event),
                attributes=event.topics[3] if event.topics[3] else b""
            )
            for event in events
        ]

    def parse_add_quantity(self, transaction_outcome: TransactionOutcome) -> List[AddQuantityOutcome]:
        self._ensure_no_error(transaction_outcome.logs.events)

        events = find_events_by_identifier(transaction_outcome, "DCDTNFTAddQuantity")
        return [
            AddQuantityOutcome(
                token_identifier=self._extract_token_identifier(event),
                nonce=self._extract_nonce(event),
                added_quantity=self._extract_amount(event)
            )
            for event in events
        ]

    def parse_burn_quantity(self, transaction_outcome: TransactionOutcome) -> List[BurnQuantityOutcome]:
        self._ensure_no_error(transaction_outcome.logs.events)

        events = find_events_by_identifier(transaction_outcome, "DCDTNFTBurn")
        return [
            BurnQuantityOutcome(
                token_identifier=self._extract_token_identifier(event),
                nonce=self._extract_nonce(event),
                burnt_quantity=self._extract_amount(event)
            )
            for event in events
        ]

    def _ensure_no_error(self, transaction_events: List[TransactionEvent]) -> None:
        for event in transaction_events:
            if event.identifier == "signalError":
                data = event.data_items[0].decode()[1:] if len(event.data_items[0]) else ""
                message = event.topics[1].decode()

                raise ParseTransactionOutcomeError(f"encountered signalError: {message} ({bytes.fromhex(data).decode()})")

    def _decode_roles(self, event: TransactionEvent) -> List[str]:
        encoded_roles = event.topics[3:]
        return [role.decode() for role in encoded_roles]

    def _extract_token_identifier(self, event: TransactionEvent) -> str:
        if not event.topics[0]:
            return ""

        return event.topics[0].decode()

    def _extract_nonce(self, event: TransactionEvent) -> int:
        if not event.topics[1]:
            return 0

        return decode_unsigned_number(event.topics[1])

    def _extract_amount(self, event: TransactionEvent) -> int:
        if not event.topics[2]:
            return 0

        return decode_unsigned_number(event.topics[2])

    def _extract_address(self, event: TransactionEvent) -> str:
        if not event.topics[3]:
            return ""

        return Address(event.topics[3], DEFAULT_HRP).to_bech32()
