import asyncio

import mm_print
import typer
from pydantic import BaseModel
from starknet_py.net.client_models import SyncStatus
from starknet_py.net.full_node_client import FullNodeClient


class NodeStatus(BaseModel):
    block_number: int | str
    chain_id: int | str
    syncing_status: bool | SyncStatus | str


def run(urls: list[str], proxy: str | None) -> None:
    if proxy:
        typer.echo("proxy is not supported yet")
        raise typer.Exit(code=1)
    asyncio.run(_run(urls))


async def _run(urls: list[str]) -> None:
    result = {}
    for url in urls:
        result[url] = (await _node_status(url)).model_dump()

    mm_print.json(result)


async def _node_status(url: str) -> NodeStatus:
    client = FullNodeClient(node_url=url)

    try:
        block_number: int | str = await client.get_block_number()
    except Exception as e:
        block_number = str(e)

    try:
        chain_id: int | str = int(await client.get_chain_id(), 16)
    except Exception as e:
        chain_id = str(e)

    try:
        syncing_status: bool | SyncStatus | str = await client.get_syncing_status()
    except Exception as e:
        syncing_status = str(e)

    return NodeStatus(block_number=block_number, chain_id=chain_id, syncing_status=syncing_status)
