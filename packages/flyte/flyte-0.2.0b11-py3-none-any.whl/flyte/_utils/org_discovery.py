def hostname_from_url(url: str) -> str:
    """Parse a URL and return the hostname part."""

    # Handle dns:/// format specifically (gRPC convention)
    if url.startswith("dns:///"):
        return url[7:]  # Skip the "dns:///" prefix

    # Handle standard URL formats
    import urllib.parse

    parsed = urllib.parse.urlparse(url)
    return parsed.netloc or parsed.path.lstrip("/").rsplit("/")[0]


def org_from_endpoint(endpoint: str | None) -> str | None:
    """
    Extracts the organization from the endpoint URL. The organization is assumed to be the first part of the domain.
    This is temporary until we have a proper organization discovery mechanism through APIs.

    :param endpoint: The endpoint URL
    :return: The organization name or None if not found
    """
    if not endpoint:
        return None

    hostname = hostname_from_url(endpoint)
    domain_parts = hostname.split(".")
    if len(domain_parts) > 2:
        # Assuming the organization is the first part of the domain
        return domain_parts[0]
    return None
