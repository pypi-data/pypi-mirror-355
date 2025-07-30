from mm_strk import balance


async def test_get_balance(mainnet_rpc_url):
    address = "0x076601136372fcdbbd914eea797082f7504f828e122288ad45748b0c8b0c9696"  # Bybit: Hot Wallet
    assert (await balance.get_balance(mainnet_rpc_url, address, balance.ETH_ADDRESS_MAINNET)).unwrap() > 1
    assert (await balance.get_balance(mainnet_rpc_url, address, balance.STRK_ADDRESS_MAINNET)).unwrap() > 1
