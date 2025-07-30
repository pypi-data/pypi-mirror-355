"""
ishne_to_csv module

Provides functionality to convert ISHNE ECG Holter binary files (.ISHNE) 
to timestamped CSV format using time and lead data.

Usage:
    from ishne_to_csv.core import read_ishne, ishne_to_csv
"""

from .core import read_ishne, ishne_to_csv

__all__ = ["read_ishne", "ishne_to_csv"]
__version__ = "0.1.0"
