from mm_http import http_request
from mm_result import Result


async def get_balance(node: str, account: str, coin_type: str, timeout: float = 5, proxy: str | None = None) -> Result[int]:
    url = f"{node}/accounts/{account}/resource/0x1::coin::CoinStore%3C{coin_type}%3E"
    res = await http_request(url, proxy=proxy, timeout=timeout)
    try:
        json_res = res.parse_json_body()
        if json_res.get("error_code") == "resource_not_found":
            return res.to_result_ok(0)
        return res.to_result_ok(int(json_res["data"]["coin"]["value"]))
    except Exception as e:
        return res.to_result_err(e)
