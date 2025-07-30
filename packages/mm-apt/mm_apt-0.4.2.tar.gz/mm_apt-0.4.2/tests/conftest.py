import os

import pytest
from dotenv import load_dotenv

load_dotenv()

MAINNET_RPC_URL = os.getenv("MAINNET_RPC_URL")


@pytest.fixture
def mainnet_rpc_url() -> str:
    if not MAINNET_RPC_URL:
        raise ValueError("MAINNET_RPC_URL environment variable is not set.")
    return MAINNET_RPC_URL


@pytest.fixture
def okx_address() -> str:
    return "0x834d639b10d20dcb894728aa4b9b572b2ea2d97073b10eacb111f338b20ea5d7"
