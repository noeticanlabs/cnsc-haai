"""
TGS Exceptions

Custom exceptions for TGS operations.
"""


class TGSError(Exception):
    """Base exception for TGS errors."""

    pass


class ClockError(TGSError):
    """Exception raised for clock operations."""

    pass


class SnapshotError(TGSError):
    """Exception raised for snapshot operations."""

    pass


class GovernanceError(TGSError):
    """Exception raised for governance operations."""

    pass


class ReceiptError(TGSError):
    """Exception raised for receipt operations."""

    pass


class LedgerError(TGSError):
    """Exception raised for ledger operations."""

    pass


class RailError(TGSError):
    """Exception raised for rail evaluation."""

    pass


class CorrectionError(TGSError):
    """Exception raised for correction operations."""

    pass
