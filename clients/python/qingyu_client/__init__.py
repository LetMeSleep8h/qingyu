"""Read-only Python client for the Qingyu Evidence Query API.

GET-only by construction: the client exposes no method that could write,
and every request it can make is a GET. Pagination cursors are signed by
the server and are passed back opaquely, so the caller never inspects
them; `iter_*` walks pages for you.
"""

from .client import QingyuClient

__all__ = ["QingyuClient"]
