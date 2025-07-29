from dataclasses import dataclass

from dharitri_py_sdk.core.address import Address
from dharitri_py_sdk.core.interfaces import (IAddress, IChainID, IGasPrice,
                                            ITransactionValue)


@dataclass
class DefaultTransactionBuildersConfiguration:
    chain_id: IChainID
    min_gas_price: IGasPrice = 1000000000
    min_gas_limit = 50000
    gas_limit_per_byte = 1500

    issue_cost: ITransactionValue = 50000000000000000
    gas_limit_dcdt_issue = 60000000
    gas_limit_dcdt_transfer = 200000
    gas_limit_dcdt_nft_transfer = 200000
    additional_gas_for_dcdt_transfer = 100000
    additional_gas_for_dcdt_nft_transfer = 800000

    dcdt_contract_address: IAddress = Address.new_from_bech32("drt1yvesqqqqqqqqqqqqqqqqqqqqqqqqyvesqqqqqqqqqqqqqqqzlllsd5j0s2")
    deployment_address: IAddress = Address.new_from_bech32("drt1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq85hk5z")
