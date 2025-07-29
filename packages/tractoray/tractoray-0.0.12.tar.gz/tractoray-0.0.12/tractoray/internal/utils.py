from urllib.parse import urlparse


def canonize_proxy(proxy: str) -> str:
    parsed = urlparse(proxy)
    if not parsed.scheme:
        return proxy
    host = parsed.hostname
    assert host is not None, proxy
    return host


def split_proxy(canonized_proxy: str) -> tuple[str, str]:
    if "." not in canonized_proxy:
        return canonized_proxy, ""
    name, rest = canonized_proxy.split(".", 1)
    return name, rest
