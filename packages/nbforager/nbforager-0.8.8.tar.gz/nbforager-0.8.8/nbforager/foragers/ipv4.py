"""IPv4 address representation in CIDR notation."""

from __future__ import annotations

from functools import total_ordering
from ipaddress import IPv4Interface, IPv4Network


@total_ordering
class IPv4:
    """IPv4 address representation in CIDR notation."""

    def __init__(self, cidr: str, strict: bool = False):
        """Initialize IPv4 object with the given CIDR notation.

        :param cidr: A string like '192.168.1.1/24'
        :param strict: If True, IP must be valid network address (not host address).
        :raises ValueError: If strict is True and a network address is not supplied.
        """
        if strict:
            IPv4Network(cidr, strict=strict)
        self.interface = IPv4Interface(cidr)

    def __repr__(self):
        """Representation of the object."""
        return f"IPv4('{self.cidr}')"

    def __str__(self):
        """String representation

        :return: IPv4 address with prefixlen, A.B.C.D/LEN.
        """
        return self.cidr

    def __hash__(self) -> int:
        """Hash value of the object."""
        return hash(self.interface.network)

    def __eq__(self, other: IPv4, /) -> bool:
        """Check if two objects are equal.

        :param other: Another object to compare.
        :return: True if objects are equal, False otherwise.
        """
        if not isinstance(other, IPv4):
            return False
        return self.interface == other.interface

    def __lt__(self, other: IPv4, /) -> bool:
        """Compare two objects.

        :param other: Another object to compare with.
        """
        if not isinstance(other, IPv4):
            return False
        return self.interface < other.interface

    def __contains__(self, other: IPv4, /) -> bool:
        """Check if all IPs in the other subnet are part of this network."""
        return other.interface.network.subnet_of(self.interface.network)

    @property
    def ip(self) -> str:
        """IPv4 address without prefixlen, A.B.C.D."""
        return str(self.interface.ip)

    @property
    def cidr(self) -> str:
        """IPv4 address with prefixlen, A.B.C.D/LEN."""
        return str(self.interface.with_prefixlen)

    @property
    def is_private(self) -> bool:
        """IPv4 address is private."""
        return bool(self.interface.ip.is_private)

    @property
    def net(self) -> str:
        """IPv4 network with prefixlen, A.B.C.D/LEN."""
        return str(self.interface.network)

    @property
    def prefixlen(self) -> int:
        """IPv4 network with prefixlen, A.B.C.D/LEN."""
        return self.interface.network.prefixlen
