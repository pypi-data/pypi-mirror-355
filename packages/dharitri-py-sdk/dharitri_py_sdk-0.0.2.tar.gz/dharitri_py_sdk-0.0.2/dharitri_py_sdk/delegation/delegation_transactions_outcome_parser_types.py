from dataclasses import dataclass

from dharitri_py_sdk.core.address import Address


@dataclass
class CreateNewDelegationContractOutcome:
    contract_address: Address
