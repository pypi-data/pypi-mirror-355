from mm_result import Result
from mm_web3 import Nodes, Proxies, retry_with_node_and_proxy

from mm_apt import balance


async def get_balance(
    retries: int, nodes: Nodes, proxies: Proxies, *, account: str, coin_type: str, timeout: float = 5
) -> Result[int]:
    return await retry_with_node_and_proxy(
        retries, nodes, proxies, lambda node, proxy: balance.get_balance(node, account, coin_type, timeout, proxy)
    )
