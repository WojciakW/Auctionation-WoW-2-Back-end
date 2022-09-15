"""
Auctionation2 exceptions.
"""


class TimeoutError(Exception):
    """Raised when connection with BlizzAPI hangs for too long."""
    pass