from requests.models import PreparedRequest, Response

from requests_pprint.formatting import (format_headers, format_http_message,
                                        parse_request_body,
                                        parse_response_body)

try:
    from rich import print  # pylint: disable=redefined-builtin
except ImportError:
    pass


def pprint_http_request(req: PreparedRequest | None) -> None:
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".

    However pay attention at the formatting used in
    this function because it is programmed to be pretty
    printed and may differ from the actual request.

    Reference: https://stackoverflow.com/a/23816211/19705722

    Args:
        req (requests.models.PreparedRequest): The request to print.
    """
    if req is None:
        return
    
    if "Host" not in req.headers and req.url:
        req.headers["Host"] = req.url.split("/")[2]

    path: str = (
        req.url.split(req.headers["Host"])[-1] if req.url else req.path_url or "/"
    )
    request_body: str = parse_request_body(req)

    msg: str = format_http_message(
        "--------------START--------------",
        f"{req.method} {path} HTTP/1.1",
        format_headers(req.headers),
        request_body,
        "---------------END---------------",
    )

    print(msg)


def pprint_http_response(resp: Response) -> None:
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".

    However pay attention at the formatting used in
    this function because it is programmed to be pretty
    printed and may differ from the actual request.

    Args:
        resp (requests.models.Response): The response to print.
    """
    http_version: str = (
        f"HTTP/{resp.raw.version // 10}.{resp.raw.version % 10}"
        if resp.raw
        else "HTTP/1.1"
    )
    response_body: str | bytes = parse_response_body(resp)

    msg: str = format_http_message(
        "--------------START--------------",
        f"{http_version} {resp.status_code} {resp.reason}",
        format_headers(resp.headers),
        response_body,  # type: ignore
        "---------------END---------------",
    )

    print(msg)


def print_response_summary(response: Response) -> None:
    """
    Print a summary of the response.

    Args:
        response (requests.models.Response): The response to print.
    """
    if response.history:
        print("[bold yellow]Request was redirected![/]")
        print("------ ORIGINAL REQUEST ------")
        pprint_http_request(response.history[0].request)
        print("------ ORIGINAL RESPONSE ------")
        pprint_http_response(response.history[0])
        print("------ REDIRECTED REQUEST ------")
        pprint_http_request(response.request)
        print("------ REDIRECTED RESPONSE ------")
        pprint_http_response(response)
    else:
        print("[bold green]Request was not redirected[/]")
        pprint_http_request(response.request)
        pprint_http_response(response)
