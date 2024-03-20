import argparse
from typing import Any, Sequence

import eth_abi
from eth_account import Account
from eth_utils import to_checksum_address
from web3 import HTTPProvider, Web3
from web3.exceptions import ContractLogicError

def encode_function(signature: str):
    return Web3.keccak(text=signature)[:4]


def encode_with_signature(function_signature: str, args: Sequence) -> str:
    assert type(args) in (tuple, list)

    function_selector = Web3.keccak(text=function_signature)[:4]
    selector_text = function_signature[
                    function_signature.find("(") + 1 : function_signature.rfind(")")
                    ]
    arg_types = selector_text.split(",")
    encoded_args = eth_abi.encode(arg_types, args)
    return "0x" + (function_selector + encoded_args).hex()


def build_domain(name: str, version: str, chain_id: int, address: str) -> dict[str, Any]:
#def build_domain(name: str, chain_id: int, address: str) -> dict[str, Any]:
    return {
        "name": name,
        "version": version,
        "chainId": chain_id,
        "verifyingContract": address
    }


def build_types() -> dict[str, Any]:
    return {
        "Permit": [
            {
                "name": "owner",
                "type": "address"
            },
            {
                "name": "spender",
                "type": "address"
            },
            {
                "name": "value",
                "type": "uint256"
            },
            {
                "name": "nonce",
                "type": "uint256"
            },
            {
                "name": "deadline",
                "type": "uint256"
            },
        ],
    }


def get_name(w3: Web3, contract: str) -> str:
    data = w3.eth.call({
        "to": contract,
        "data": encode_function("name()")
    })
    return eth_abi.decode(["string"], data)[0]


def get_nonce(w3: Web3, contract: str, address: str) -> int:
    data = w3.eth.call({
        "to": contract,
        "data": encode_with_signature("nonces(address)", (address,))
    })
    return eth_abi.decode(["uint256"], data)[0]


def get_version(w3: Web3, contract: str) -> str:
    if contract == "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84":
        data = w3.eth.call({
            "to": contract,
            "data": encode_function("getContractVersion()")
        })
        return str(eth_abi.decode(["uint256"], data)[0])
    data = w3.eth.call({
            "to": contract,
            "data": encode_function("version()")
        })
    return eth_abi.decode(["string"], data)[0]


def main(
    *,
    private_key: str,
    owner: str,
    spender: str,
    contract: str,
    value: int,
    deadline: int,
    provider_url: str,
    chain_id: int
) -> None:
    provider = HTTPProvider(provider_url)
    w3 = Web3(provider)
    name = get_name(w3, contract)
    nonce = get_nonce(w3, contract, owner)
    try:
        version = get_version(w3, contract)
    except ContractLogicError:
        version = "1"
    domain_data = build_domain(name, version, chain_id, contract)
#    domain_data = build_domain(name, chain_id, contract)
    types = build_types()
    data = {
        "owner": to_checksum_address(owner),
        "spender": to_checksum_address(spender),
        "value": value,
        "nonce": nonce,
        "deadline": deadline
    }
    signed_data = Account.sign_typed_data(private_key, domain_data, types, data)

    print(f"owner:    {owner}")
    print(f"spender:  {spender}")
    print(f"value:    {value}")
    print(f"deadline: {deadline}")
    print(f"v:        {signed_data.v}")
    print(f"r:        {hex(signed_data.r)}")
    print(f"s:        {hex(signed_data.s)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Description of your script")

    parser.add_argument("--private_key", type=str, help="Private key string")
    parser.add_argument("--owner", type=str, help="Owner address")
    parser.add_argument("--spender", type=str, help="Spender address")
    parser.add_argument("--contract", type=str, help="Contract address")
    parser.add_argument("--value", type=int, help="allowance")
    parser.add_argument("--deadline", type=int, help="deadline")
    parser.add_argument("--provider_url", type=str, help="Provider URL string")
    parser.add_argument("--chain_id", type=int, help="Integer chain ID")

    args = parser.parse_args()

    private_key = args.private_key
    owner = to_checksum_address(args.owner)
    spender = to_checksum_address(args.spender)
    contract = to_checksum_address(args.contract)
    value = args.value
    deadline = args.deadline
    provider_url = args.provider_url
    chain_id = args.chain_id

    main(
        private_key=private_key,
        owner=owner,
        spender=spender,
        contract=contract,
        value=value,
        deadline=deadline,
        provider_url=provider_url,
        chain_id=chain_id
    )
