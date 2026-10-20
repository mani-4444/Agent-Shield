import socket

import pytest
from pytest_socket import SocketConnectBlockedError


@pytest.mark.filterwarnings("ignore::UserWarning:pytest_socket")
def test_outbound_network_is_blocked() -> None:
    # 192.0.2.1 is TEST-NET-1 (RFC 5737): never routable, so this can't leak even if unblocked.
    with pytest.raises(SocketConnectBlockedError):
        socket.create_connection(("192.0.2.1", 443), timeout=1)
