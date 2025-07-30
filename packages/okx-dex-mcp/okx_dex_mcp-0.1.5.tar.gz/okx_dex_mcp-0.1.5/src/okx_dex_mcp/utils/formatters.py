"""
Formatting utilities for DEX data display.
"""

from typing import Dict, List, Any
from decimal import Decimal
from .constants import STABLECOINS


def convert_decimal_to_minimal_units(decimal_amount: str, decimals: int) -> str:
    """
    Convert decimal amount to minimal units (wei-like format).
    
    Args:
        decimal_amount: Decimal amount as string (e.g., "1.0", "0.1")
        decimals: Number of decimals for the token (e.g., 18 for ETH, 6 for USDC)
    
    Returns:
        str: Amount in minimal units
    
    Examples:
        convert_decimal_to_minimal_units("1.0", 18) -> "1000000000000000000"  # 1 ETH
        convert_decimal_to_minimal_units("1.0", 6) -> "1000000"  # 1 USDC
        convert_decimal_to_minimal_units("0.1", 6) -> "100000"  # 0.1 USDC
    """
    try:
        # Use Decimal for precise arithmetic
        decimal_value = Decimal(decimal_amount)
        multiplier = Decimal(10) ** decimals
        minimal_units = decimal_value * multiplier
        
        # Convert to integer string (no decimal places)
        return str(int(minimal_units))
    except (ValueError, TypeError, OverflowError) as e:
        raise ValueError(f"Invalid decimal amount '{decimal_amount}' or decimals '{decimals}': {str(e)}")