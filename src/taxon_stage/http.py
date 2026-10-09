"""Shared HTTP setup for the two modules that reach the network.

Stdlib only: the package declares no required dependencies, and one SPARQL
query plus one label lookup do not justify adding any.

The CA-bundle search exists because a Homebrew Python does not necessarily
trust anything out of the box -- `ssl.create_default_context()` alone fails with
CERTIFICATE_VERIFY_FAILED on this machine. Kept in one place so the two callers
cannot drift apart.
"""

from __future__ import annotations

import os
import ssl

UA = "taxon-stage-axioms/0.1 (https://github.com/dosumis/taxon-stage-axioms)"

CA_BUNDLE_CANDIDATES = (
    "/etc/ssl/cert.pem",
    "/opt/homebrew/etc/ca-certificates/cert.pem",
    "~/.homebrew/etc/ca-certificates/cert.pem",
    "/usr/local/etc/ca-certificates/cert.pem",
)


def ssl_context() -> ssl.SSLContext:
    try:
        import certifi  # type: ignore

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    paths = (os.environ.get("SSL_CERT_FILE"),) + CA_BUNDLE_CANDIDATES
    for path in paths:
        if path and os.path.exists(os.path.expanduser(path)):
            return ssl.create_default_context(cafile=os.path.expanduser(path))
    return ssl.create_default_context()
