from aiohttp import ClientRequest, ClientResponse, RequestInfo

from requests_pprint.formatting import (async_parse_request_body,
                                        async_parse_response_body,
                                        format_headers, format_http_message)

try:
    from rich import print  # pylint: disable=redefined-builtin
except ImportError:
    pass


async def pprint_async_http_request(req: ClientRequest | RequestInfo) -> None:
    """
    Pretty print an aiohttp ClientRequest.

    Args:
        req (aiohttp.ClientRequest): The request to print.
    """
    if "Host" not in req.headers and req.url:
        req.headers["Host"] = req.url.host  # type: ignore

    path: str = req.url.path_qs or "/"
    body: str = (
        "" if isinstance(req, RequestInfo) else await async_parse_request_body(req)
    )

    msg: str = format_http_message(
        "--------------START--------------",
        f"{req.method} {path} HTTP/1.1",
        format_headers(req.headers),
        body,
        "---------------END---------------",
    )

    print(msg)


async def pprint_async_http_response(resp: ClientResponse) -> None:
    """
    Pretty print an aiohttp ClientResponse.

    Args:
        resp (aiohttp.ClientResponse): The response to print.
    """
    response_body: str | bytes = await async_parse_response_body(resp)

    msg: str = format_http_message(
        "--------------START--------------",
        f"HTTP/1.1 {resp.status} {resp.reason}",
        format_headers(resp.headers),
        response_body,  # type: ignore
        "---------------END---------------",
    )

    print(msg)


async def print_async_response_summary(response: ClientResponse) -> None:
    """
    Print a summary of the response.

    Args:
        response (aiohttp.ClientResponse): The response to print.
    """
    if response.history:
        print("[bold yellow]Request was redirected![/]")
        print("------ ORIGINAL REQUEST ------")
        await pprint_async_http_request(response.history[0].request_info)
        print("------ ORIGINAL RESPONSE ------")
        await pprint_async_http_response(response.history[0])
        print("------ REDIRECTED REQUEST ------")
        await pprint_async_http_request(response.request_info)
        print("------ REDIRECTED RESPONSE ------")
        await pprint_async_http_response(response)
    else:
        print("[bold green]Request was not redirected[/]")
        await pprint_async_http_request(response.request_info)
        await pprint_async_http_response(response)
