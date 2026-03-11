#!/usr/bin/env python3
"""


Install:
  pip install web3

Usage:
  python document_timestamp_client.py hash   <file>
  python document_timestamp_client.py anchor <file>
  python document_timestamp_client.py verify <file>
  python document_timestamp_client.py status
"""

from __future__ import annotations

import sys
import os
import hashlib
from dataclasses import dataclass
from typing import Any, Dict, Tuple

from web3 import Web3
from web3.exceptions import ContractLogicError

from config import RPC_URL, PRIVATE_KEY, CONTRACT_ADDRESS, CHAIN_ID


CONTRACT_ABI = [
    {
        "inputs": [],
        "stateMutability": "nonpayable",
        "type": "constructor",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "documentHash", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "sender", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"},
        ],
        "name": "DocumentStored",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [],
        "name": "Paused",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [],
        "name": "Unpaused",
        "type": "event",
    },
    {
        "inputs": [],
        "name": "pause",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "unpause",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "_hash", "type": "bytes32"}],
        "name": "storeDocument",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "_hash", "type": "bytes32"}],
        "name": "verifyDocument",
        "outputs": [
            {"internalType": "bool", "name": "exists", "type": "bool"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "address", "name": "sender", "type": "address"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "paused",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
]


@dataclass(frozen=True)
class AnchorResult:
    file_path: str
    sha256_hex: str
    tx_hash: str
    block_number: int
    block_timestamp: int
    event_sender: str
    event_timestamp: int


def die(msg: str, code: int = 1) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    raise SystemExit(code)


def info(msg: str) -> None:
    print(f"[INFO] {msg}")


def compute_sha256(file_path: str) -> str:
    if not os.path.isfile(file_path):
        die(f"File not found: {file_path}")

    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()  # 64 hex chars


def sha256hex_to_bytes32(hex_str: str) -> bytes:
    """
    Convert a 64-hex SHA-256 digest to bytes32 (32 bytes).
    """
    hex_str = hex_str.strip().lower()
    if hex_str.startswith("0x"):
        hex_str = hex_str[2:]
    if len(hex_str) != 64:
        die("SHA-256 must be 64 hex chars.")
    try:
        raw = bytes.fromhex(hex_str)
    except ValueError:
        die("Invalid hex SHA-256.")
    if len(raw) != 32:
        die("Decoded SHA-256 is not 32 bytes.")
    return raw

def normalize_private_key(pk: str) -> str:
    pk = pk.strip()
    if not pk.startswith("0x"):
        pk = "0x" + pk
    return pk


def connect() -> Web3:
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        die("Cannot connect to RPC. Check RPC_URL.")
    return w3


def contract_instance(w3: Web3):
    if not Web3.is_address(CONTRACT_ADDRESS):
        die("Invalid CONTRACT_ADDRESS.")
    return w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI)


def account(w3: Web3):
    pk = normalize_private_key(PRIVATE_KEY)
    if len(pk) != 66:
        die("Invalid PRIVATE_KEY length.")
    return w3.eth.account.from_key(pk)



def show_status() -> None:
    w3 = connect()
    c = contract_instance(w3)

    try:
        owner = c.functions.owner().call()
        paused = c.functions.paused().call()
    except Exception as e:
        die(f"Failed to read contract status: {e}")

    info(f"Contract: {c.address}")
    info(f"Owner:    {owner}")
    info(f"Paused:   {paused}")


def anchor(file_path: str) -> AnchorResult:
    w3 = connect()
    c = contract_instance(w3)
    acct = account(w3)

    sha_hex = compute_sha256(file_path)
    doc_hash = sha256hex_to_bytes32(sha_hex)

    info(f"Account:  {acct.address}")
    info(f"Contract: {c.address}")
    info(f"File:     {file_path}")
    info(f"SHA-256:  {sha_hex}")

    # Prepare tx
    try:
        nonce = w3.eth.get_transaction_count(acct.address)
        gas_price = w3.eth.gas_price

        tx = c.functions.storeDocument(doc_hash).build_transaction(
            {
                "from": acct.address,
                "nonce": nonce,
                "chainId": CHAIN_ID,
                "gasPrice": gas_price,
            }
        )
        tx["gas"] = w3.eth.estimate_gas(tx)
    except ContractLogicError as e:
        die(f"Contract reverted on build/estimate: {e}")
    except Exception as e:
        die(f"Failed to prepare tx: {e}")

    signed = acct.sign_transaction(tx)
    tx_hash_bytes = w3.eth.send_raw_transaction(signed.raw_transaction)
    tx_hash = tx_hash_bytes.hex()
    info(f"Tx sent:  {tx_hash}")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash_bytes)
    if receipt.status != 1:
        die("Transaction failed (receipt.status != 1).")

    block = w3.eth.get_block(receipt.blockNumber)
    block_ts = int(block.timestamp)

    # Parse DocumentStored event from receipt (if present)
    event_sender = "0x0000000000000000000000000000000000000000"
    event_ts = 0

    try:
        events = c.events.DocumentStored().process_receipt(receipt)
        if events:
            args = events[0]["args"]
            event_sender = str(args["sender"])
            event_ts = int(args["timestamp"])
    except Exception:
        # not fatal; tx is successful anyway
        pass

    info(f"Block:    {receipt.blockNumber}")
    info(f"Block ts: {block_ts}")

    if event_ts != 0:
        info(f"Event DocumentStored.sender:    {event_sender}")
        info(f"Event DocumentStored.timestamp: {event_ts}")

    return AnchorResult(
        file_path=file_path,
        sha256_hex=sha_hex,
        tx_hash=tx_hash,
        block_number=int(receipt.blockNumber),
        block_timestamp=block_ts,
        event_sender=event_sender,
        event_timestamp=event_ts,
    )


def verify(file_path: str) -> Tuple[bool, int, str, str]:
    """
    Returns: (exists, timestamp, sender, sha256_hex)
    """
    w3 = connect()
    c = contract_instance(w3)

    sha_hex = compute_sha256(file_path)
    doc_hash = sha256hex_to_bytes32(sha_hex)

    try:
        exists, ts, sender = c.functions.verifyDocument(doc_hash).call()
    except Exception as e:
        die(f"verifyDocument() call failed: {e}")

    return bool(exists), int(ts), str(sender), sha_hex


def print_usage() -> None:
    print(
        "Usage:\n"
        "  python document_timestamp_client.py status\n"
        "  python document_timestamp_client.py hash   <file>\n"
        "  python document_timestamp_client.py anchor <file>\n"
        "  python document_timestamp_client.py verify <file>\n"
    )


def main(argv: list[str]) -> None:
    if len(argv) < 2:
        print_usage()
        raise SystemExit(2)

    cmd = argv[1].lower()

    if cmd == "status":
        show_status()
        return

    if cmd == "hash":
        if len(argv) != 3:
            print_usage()
            raise SystemExit(2)
        print(compute_sha256(argv[2]))
        return

    if cmd == "anchor":
        if len(argv) != 3:
            print_usage()
            raise SystemExit(2)
        res = anchor(argv[2])
        print("\n--- RESULT ---")
        print(f"file:            {res.file_path}")
        print(f"sha256:          {res.sha256_hex}")
        print(f"tx_hash:         {res.tx_hash}")
        print(f"block_number:    {res.block_number}")
        print(f"block_timestamp: {res.block_timestamp}")
        if res.event_timestamp:
            print(f"event_sender:    {res.event_sender}")
            print(f"event_timestamp: {res.event_timestamp}")
        return

    if cmd == "verify":
        if len(argv) != 3:
            print_usage()
            raise SystemExit(2)
        exists, ts, sender, sha_hex = verify(argv[2])
        print("\n--- RESULT ---")
        print(f"sha256:   {sha_hex}")
        print(f"exists:   {exists}")
        print(f"ts:       {ts}")
        print(f"sender:   {sender}")
        return

    print_usage()
    raise SystemExit(2)


if __name__ == "__main__":
    main(sys.argv)
