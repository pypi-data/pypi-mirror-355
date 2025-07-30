import aiohttp
from aiohttp_socks import ProxyConnector
from mm_result import Result
from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.models.chains import StarknetChainId
from starknet_py.net.signer.key_pair import KeyPair

ETH_ADDRESS_MAINNET = "0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"
ETH_DECIMALS = 18
DAI_ADDRESS_MAINNET = "0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3"
DAI_DECIMALS = 18
USDC_ADDRESS_MAINNET = "0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8"
USDC_DECIMALS = 6
USDT_ADDRESS_MAINNET = "0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8"
USDT_DECIMALS = 6
STRK_ADDRESS_MAINNET = "0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d"
STRK_DECIMALS = 18


async def get_balance(rpc_url: str, address: str, token: str, timeout: float = 5, proxy: str | None = None) -> Result[int]:
    try:
        timeout_config = aiohttp.ClientTimeout(total=timeout)
        connector = ProxyConnector.from_url(proxy) if proxy else None
        async with aiohttp.ClientSession(connector=connector, timeout=timeout_config) as session:
            client = FullNodeClient(node_url=rpc_url, session=session)
            account = Account(
                address=address,
                client=client,
                chain=StarknetChainId.MAINNET,
                key_pair=KeyPair(private_key=654, public_key=321),
            )
            balance = await account.get_balance(token_address=token)
            return Result.ok(balance)
    except Exception as e:
        return Result.err(e)
