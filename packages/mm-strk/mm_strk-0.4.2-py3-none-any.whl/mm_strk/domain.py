from mm_http import http_request
from mm_result import Result
from mm_std import str_contains_any


async def address_to_domain(address: str, timeout: float = 5.0, proxy: str | None = None) -> Result[str | None]:
    url = "https://api.starknet.id/addr_to_domain"
    res = await http_request(url, params={"addr": address}, proxy=proxy, timeout=timeout)
    if (
        res.status_code == 400
        and res.body is not None
        and str_contains_any(res.body.lower(), ["no data found", "no domain found"])
    ):
        return res.to_result_ok(None)
    if res.is_err():
        return res.to_result_err()
    domain = res.parse_json_body("domain")
    if domain:
        return res.to_result_ok(domain)
    return res.to_result_err("unknown_response")
