import os

import pytest
from dotenv import load_dotenv

load_dotenv()

MAINNET_URL = os.getenv("MAINNET_URL")


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def zklend_market_address() -> str:
    return "0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05"


@pytest.fixture
def mainnet_rpc_url() -> str:
    if not MAINNET_URL:
        raise ValueError("MAINNET_URL environment variable is not set.")
    return MAINNET_URL
